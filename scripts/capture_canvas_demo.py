"""
Record tutor canvas demo — screenshots + animated video.
Uses Playwright to render the canvas-demo page, then captures
an animated version where drawing commands appear one-by-one.
"""
import json
import os
import subprocess

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5001"
OUT = "/home/muatasr/.nanobot/workspace/teas-study-app/static/screenshots"
os.makedirs(OUT, exist_ok=True)

# Parabola drawing steps (Python booleans)
PARABOLA_STEPS = [
    {"type":"grid","x":30,"y":20,"w":700,"h":280,"step":50,"gridColor":"rgba(0,0,0,0.05)"},
    {"type":"arrow","x1":30,"y1":160,"x2":740,"y2":160,"color":"#2D3436","strokeWidth":2},
    {"type":"arrow","x1":380,"y1":290,"x2":380,"y2":10,"color":"#2D3436","strokeWidth":2},
    {"type":"label","x":742,"y":150,"content":"x","color":"#636e72","fontSize":14,"box":False},
    {"type":"label","x":386,"y":2,"content":"y","color":"#636e72","fontSize":14,"box":False},
    {"type":"plot","color":"#e74c3c","points":[[80,270],[130,240],[180,205],[230,175],[280,150],[330,130],[380,120],[430,125],[480,145],[530,180],[580,225],[630,280]],"dots":True,"roughness":0.8},
    {"type":"label","x":410,"y":100,"content":"y = x²","color":"#e74c3c","fontSize":18,"box":True,"boxColor":"rgba(231,76,60,0.08)"},
    {"type":"label","x":366,"y":164,"content":"0","color":"#636e72","fontSize":12,"box":False}
]

STEP_LABELS = [
    "Drawing coordinate grid...",
    "X-axis with arrow",
    "Y-axis with arrow",
    "Label: x",
    "Label: y",
    "Plotting the parabola curve...",
    "Label: y = x²",
    "Origin point"
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        # ── 1. Full-page screenshot of canvas-demo ──
        print("📸 Taking full-page screenshot...")
        page.goto(f"{BASE}/canvas-demo", wait_until="networkidle")
        page.wait_for_timeout(3000)
        page.screenshot(path=f"{OUT}/canvas-demo-full.png", full_page=True)
        print(f"   → {OUT}/canvas-demo-full.png")

        # ── 2. Individual canvas screenshots ──
        page.wait_for_timeout(2000)
        canvases = page.query_selector_all(".tutor-canvas")
        print(f"   Found {len(canvases)} tutor-canvas elements")
        for i, canvas in enumerate(canvases):
            canvas.screenshot(path=f"{OUT}/canvas-{i+1}.png")
            print(f"   → {OUT}/canvas-{i+1}.png")

        # ── 3. Animated video: tutor draws parabola step by step ──
        print("🎬 Recording animated drawing...")

        # Build animation HTML with JSON injected server-side
        cmds_json = json.dumps(PARABOLA_STEPS)
        labels_json = json.dumps(STEP_LABELS)

        anim_html = f"""<!DOCTYPE html>
<html><head><style>
body {{ margin:0; background:#FAFAF7; display:flex; flex-direction:column;
       align-items:center; justify-content:center; min-height:100vh;
       font-family:'Source Sans 3',system-ui,sans-serif; }}
.title {{ font-size:22px; color:#2D3436; margin-bottom:8px; font-weight:600; }}
.subtitle {{ font-size:14px; color:#636e72; margin-bottom:20px; }}
.canvas-wrap {{ border-radius:12px; box-shadow:0 2px 12px rgba(0,0,0,0.08); overflow:hidden; }}
.step-label {{ font-size:14px; color:#b2bec3; margin-top:16px; min-height:22px; text-align:center; }}
</style></head><body>
<div class="title">y = x²</div>
<div class="subtitle">AI Tutor draws the coordinate plane and parabola</div>
<div class="canvas-wrap">
  <div class="tutor-canvas" id="mainCanvas" data-width="760" data-height="320"></div>
</div>
<div class="step-label" id="stepLabel">Preparing canvas...</div>
<script src="file:///home/muatasr/.nanobot/workspace/teas-study-app/static/vendor/fabric.min.js"></script>
<script src="file:///home/muatasr/.nanobot/workspace/teas-study-app/static/vendor/rough.js"></script>
<script src="file:///home/muatasr/.nanobot/workspace/teas-study-app/static/js/tutor-canvas.js"></script>
<script>
const STEPS = {cmds_json};
const LABELS = {labels_json};
window.renderStep = function(i) {{
    const el = document.getElementById("mainCanvas");
    const label = document.getElementById("stepLabel");
    if (i >= STEPS.length) {{
        label.textContent = "Done ✓";
        return;
    }}
    const subset = STEPS.slice(0, i + 1);
    el.dataset.commands = JSON.stringify(subset);
    el.removeAttribute("data-rendered");
    MU2.tutorCanvas.renderAll();
    label.textContent = LABELS[i] || "";
}};
</script></body></html>"""

        anim_path = "/tmp/tutor-canvas-anim.html"
        with open(anim_path, "w") as f:
            f.write(anim_html)

        page.goto(f"file://{anim_path}", wait_until="networkidle")
        page.wait_for_timeout(500)

        # Capture frames
        frames_dir = "/tmp/tutor-frames"
        os.makedirs(frames_dir, exist_ok=True)
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir, f))

        frame_idx = 0
        fps = 4
        hold_final = fps * 3

        for step in range(len(PARABOLA_STEPS) + 1):
            page.evaluate(f"window.renderStep({step})")
            page.wait_for_timeout(400)

            count = hold_final if step == len(PARABOLA_STEPS) else fps
            for _ in range(count):
                page.screenshot(path=f"{frames_dir}/frame_{frame_idx:05d}.png")
                frame_idx += 1

        print(f"   → {frame_idx} frames captured")
        browser.close()

    # ── 4. Encode video ──
    print("🎥 Encoding video...")
    import imageio_ffmpeg
    ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
    video_path = f"{OUT}/tutor-canvas-drawing.mp4"
    frames_pattern = os.path.join(frames_dir, "frame_%05d.png")

    cmd = [
        ffmpeg_bin, "-y",
        "-framerate", "4",
        "-i", frames_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        "-preset", "fast",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=#FAFAF7",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        size = os.path.getsize(video_path)
        print(f"   → {video_path} ({size//1024}KB)")
    else:
        print(f"   ✗ ffmpeg failed: {result.stderr[-300:]}")

    # Cleanup
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    os.rmdir(frames_dir)
    print("✅ Done!")


if __name__ == "__main__":
    main()
