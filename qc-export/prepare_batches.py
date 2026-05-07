import json
import os

BASE_DIR = "/home/muatasr/.nanobot/workspace/teas-study-app/qc-export"

with open(os.path.join(BASE_DIR, "phase1_results.json")) as f:
    p1 = json.load(f)

FILES = {
    "math": "math_questions.json",
    "science": "science_questions.json",
    "reading": "reading_questions.json",
    "english": "english_questions.json",
}

BATCH_SIZE = 50

os.makedirs(os.path.join(BASE_DIR, "batches"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "phase2_results"), exist_ok=True)

manifest = []

for subject, fname in FILES.items():
    filepath = os.path.join(BASE_DIR, fname)
    with open(filepath) as f:
        questions = json.load(f)

    passed = [q for q in questions if not p1[str(q["id"])]["mechanical_fail_reasons"]]

    batch_num = 0
    for i in range(0, len(passed), BATCH_SIZE):
        batch = passed[i : i + BATCH_SIZE]
        batch_num += 1
        batch_fname = f"batch_{subject}_{batch_num}.json"
        batch_path = os.path.join(BASE_DIR, "batches", batch_fname)
        with open(batch_path, "w") as f:
            json.dump(batch, f, indent=2)
        manifest.append({
            "batch_file": batch_fname,
            "subject": subject,
            "batch_num": batch_num,
            "count": len(batch),
            "output_file": f"phase2_{subject}_{batch_num}.json",
        })

    print(f"{subject}: {len(passed)} passed Phase 1 -> {batch_num} batches")

with open(os.path.join(BASE_DIR, "batch_manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"\nTotal batches: {len(manifest)}")
