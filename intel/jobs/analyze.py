# analyze.py - label posts with the local LLM, then force labels into the fixed taxonomy
import json
from .. import llm
from ..config import MODEL
from ..db import get_db
from ..extract import dumps, extract, adjust_severity
from ..taxonomy import CATEGORIES, SEVERITIES, norm_category, norm_severity

PROMPT = """You are a cybersecurity analyst. Classify the post below.
Reply with ONLY JSON: {{"summary": "<2 short sentences>", "category": "<ONE of: {cats}>", "severity": "<ONE of: {sevs}>"}}
Choose exactly one category. Severity guide: critical = actively exploited / major breach,
high = serious vuln or attack, medium = notable news, low = promo, tutorials, general chatter.

Post:
{text}"""

def main():
    db = get_db()
    for pid, text in db.execute("SELECT id,text FROM posts WHERE entities IS NULL AND text!=''").fetchall():
        db.execute("UPDATE posts SET entities=? WHERE id=?", (dumps(text), pid))
    db.commit()
    ph = ",".join("?" * len(CATEGORIES))
    rows = db.execute(f"SELECT id,text FROM posts WHERE text!='' AND "
                      f"(summary IS NULL OR category IS NULL OR category NOT IN ({ph}))",
                      CATEGORIES).fetchall()
    print(f"Analyzing {len(rows)} posts with {MODEL}...")
    for pid, text in rows:
        try:
            r = llm.generate(format="json", prompt=PROMPT.format(
                cats=" | ".join(CATEGORIES), sevs=" | ".join(SEVERITIES), text=text[:3000]))
            d = json.loads(r["response"])
            cat, sev = norm_category(d.get("category"), text), adjust_severity(norm_severity(d.get("severity")), text)
            db.execute("UPDATE posts SET summary=?,category=?,severity=? WHERE id=?",
                       (d.get("summary") or text[:200], cat, sev, pid))
            db.commit()
            print(f"  [OK] {pid[:35]} {cat} / {sev}")
        except Exception as e:
            print(f"  [SKIP] {pid[:35]} {e}")

if __name__ == "__main__":
    main()
