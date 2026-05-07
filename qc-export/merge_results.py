import json
import os
import glob

BASE = "/home/muatasr/.nanobot/workspace/teas-study-app/qc-export"

with open(os.path.join(BASE, "phase1_results.json")) as f:
    p1 = json.load(f)

p2_results = {}
results_dir = os.path.join(BASE, "phase2_results")
for fpath in sorted(glob.glob(os.path.join(results_dir, "phase2_*.json"))):
    with open(fpath) as f:
        batch = json.load(f)
    for r in batch:
        p2_results[r["id"]] = r

FILES = [
    "math_questions.json",
    "science_questions.json",
    "reading_questions.json",
    "english_questions.json",
]

all_results = []
subject_counts = {}
total = 0
pass_count = 0
fail_count = 0

for fname in FILES:
    with open(os.path.join(BASE, fname)) as f:
        questions = json.load(f)

    for q in questions:
        total += 1
        qid = q["id"]
        subject = q["subject"]

        if subject not in subject_counts:
            subject_counts[subject] = {"total": 0, "pass": 0, "fail": 0}
        subject_counts[subject]["total"] += 1

        all_fail_reasons = []

        p1_reasons = p1[str(qid)]["mechanical_fail_reasons"]
        if p1_reasons:
            all_fail_reasons.extend(p1_reasons)

        p2 = p2_results.get(qid)
        if p2 and p2.get("verdict") == "FAIL":
            all_fail_reasons.extend(p2.get("fail_reasons", []))

        if all_fail_reasons:
            entry = {
                "id": qid,
                "subject": subject,
                "verdict": "FAIL",
                "fail_reasons": all_fail_reasons,
            }
            fail_count += 1
            subject_counts[subject]["fail"] += 1
        else:
            entry = {
                "id": qid,
                "subject": subject,
                "verdict": "PASS",
            }
            pass_count += 1
            subject_counts[subject]["pass"] += 1

        all_results.append(entry)

output = {
    "summary": {
        "total": total,
        "pass": pass_count,
        "fail": fail_count,
        "by_subject": subject_counts,
    },
    "results": all_results,
}

out_path = os.path.join(BASE, "qc_results.json")
with open(out_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"Written to {out_path}")
print(f"Total: {total}")
print(f"PASS: {pass_count}")
print(f"FAIL: {fail_count}")
print(f"By subject:")
for subj, counts in sorted(subject_counts.items()):
    pct = counts["fail"] / counts["total"] * 100
    print(f"  {subj}: {counts['total']} total, {counts['pass']} pass, {counts['fail']} fail ({pct:.1f}% fail)")
