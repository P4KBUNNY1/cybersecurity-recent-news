# export_training_data.py - dump your analyzed posts as JSONL for later fine-tuning.
# Review train.jsonl by hand first: labels made by a 2B model contain mistakes.
import json
from ..db import get_db
from ..config import TRAIN_FILE
def main():
    rows = get_db().execute("SELECT text,summary,category,severity FROM posts WHERE summary IS NOT NULL AND text!=''").fetchall()
    with open(TRAIN_FILE, "w", encoding="utf-8") as f:
        for t, s, c, v in rows:
            f.write(json.dumps({"instruction": "Classify this cybersecurity post as JSON with summary, category, severity.",
                                "input": t[:2000],
                                "output": json.dumps({"summary": s, "category": c, "severity": v})}, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} examples to {TRAIN_FILE} (aim for 500+ reviewed ones before fine-tuning)")

if __name__ == "__main__":
    main()
