#!/usr/bin/env python3
"""
Credential scanner — blocks secrets from ever entering this repo again.

Modes:
  secret_scan.py                scan all git-tracked files
  secret_scan.py --staged       scan content staged in the index (pre-commit hook)
  secret_scan.py --all-history  scan every blob in every commit (slow; pre-release gate)

Exit 0 = clean, 1 = findings (so it works as a blocking hook).

Stdlib only. No install, no network.
"""
import os, re, subprocess, sys

# --- patterns -------------------------------------------------------------
# Ordered roughly most-specific first. Each is (name, regex).
PATTERNS = [
    ("Private key block",      re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |PGP )?PRIVATE KEY-----")),
    ("AWS access key id",      re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16,20}\b")),
    ("GitHub token",           re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
    ("Anthropic key",          re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b")),
    ("OpenAI key",             re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{24,}\b")),
    ("Google API key",         re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b")),
    ("Slack token",            re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b")),
    ("Z.AI / BigModel key",    re.compile(r"\b[0-9a-f]{32}\.[A-Za-z0-9_\-]{12,}\b")),
    ("Stripe key",             re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    ("SendGrid key",           re.compile(r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\b")),
    ("Generic secret assign",  re.compile(
        r"""(?ix)\b(?:api[_-]?key|secret|token|password|passwd|pwd|access[_-]?key|
                        private[_-]?key|client[_-]?secret|auth[_-]?token)\b
                     \s*[:=]\s*
                     ["'](?P<val>[^"'\s]{12,})["']""")),
]

# --- allowlist: things that look like secrets but are not ------------------
PLACEHOLDER = re.compile(
    r"""(?ix)^(?:
        |your[-_].*|.*[-_]here|changeme|placeholder|example|dummy|sample|redacted
        |x{6,}|\*{6,}|REMOVED[-_]ROTATED[-_]KEY
        |os\.environ.*|getenv.*|\$\{.*\}.*|<.*>.*|%.*%|process\.env.*
        |null|none|true|false|test|todo
    )$""")

BINARY_EXT = {".png",".jpg",".jpeg",".gif",".webp",".ico",".svg",".woff",".woff2",
              ".ttf",".otf",".pdf",".zip",".gz",".tgz",".mp3",".mp4",".ogg",".wav"}
SKIP_DIRS = {".git",".venv","venv","node_modules","__pycache__","dist","build",".mypy_cache"}


def allowed(value: str) -> bool:
    """True = ignore this candidate.

    Deliberately conservative. An earlier version also required the value to
    contain BOTH a letter and a digit "to be a plausible key" -- that silently
    skipped real-format keys with no digits (several vendor tokens, and PEM
    headers). A scanner with a silent blind spot is worse than no scanner,
    because it creates false confidence. Only explicit placeholders are ignored.
    """
    v = value.strip().strip("\"'")
    if len(v) < 8:
        return True
    if PLACEHOLDER.match(v):
        return True
    return False


def scan_text(name, text, findings):
    for i, line in enumerate(text.splitlines(), 1):
        if len(line) > 4000:
            continue
        for label, rx in PATTERNS:
            for m in rx.finditer(line):
                val = m.groupdict().get("val") or m.group(0)
                if allowed(val):
                    continue
                findings.append((name, i, label, val))


def tracked_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f.strip()]


def staged_files():
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                         capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f.strip()]


def show(path, staged):
    try:
        if staged:
            r = subprocess.run(["git", "show", f":{path}"], capture_output=True, text=True)
            return r.stdout
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def history_blobs():
    """Every blob in every commit (pre-release gate)."""
    revs = subprocess.run(["git", "rev-list", "--all"], capture_output=True, text=True).stdout.split()
    seen = set()
    for rev in revs:
        for line in subprocess.run(["git", "ls-tree", "-r", rev], capture_output=True,
                                   text=True).stdout.splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            sha, path = parts[2], parts[3]
            if sha in seen:
                continue
            seen.add(sha)
            if os.path.splitext(path)[1].lower() in BINARY_EXT:
                continue
            body = subprocess.run(["git", "cat-file", "-p", sha], capture_output=True,
                                  text=True, errors="replace").stdout
            yield f"{rev[:10]}:{path}", body


def main():
    args = set(sys.argv[1:])
    findings = []

    if "--all-history" in args:
        count = 0
        for name, body in history_blobs():
            count += 1
            scan_text(name, body, findings)
        print(f"scanned {count} blobs across all commits")
    elif "--staged" in args:
        files = staged_files()
        for f in files:
            if os.path.splitext(f)[1].lower() in BINARY_EXT:
                continue
            scan_text(f, show(f, True), findings)
        print(f"scanned {len(files)} staged file(s)")
    else:
        files = tracked_files()
        for f in files:
            if os.path.splitext(f)[1].lower() in BINARY_EXT:
                continue
            if any(part in SKIP_DIRS for part in f.split(os.sep)):
                continue
            scan_text(f, show(f, False), findings)
        print(f"scanned {len(files)} tracked file(s)")

    if findings:
        print(f"\n{len(findings)} POTENTIAL CREDENTIAL(S) FOUND\n")
        for name, line, label, val in findings[:60]:
            masked = val[:6] + "..." + val[-4:] if len(val) > 12 else "***"
            print(f"  {label:22s} {name}:{line}  {masked}")
        if len(findings) > 60:
            print(f"  ... and {len(findings)-60} more")
        print("\nRemediation: remove the literal, read it from the environment "
              "(see .env.example). If it was ever committed, ROTATE the credential — "
              "deleting the file does not remove it from history.")
        return 1
    print("no credentials detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
