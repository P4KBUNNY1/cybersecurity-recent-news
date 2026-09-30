# digest.py - email critical/high posts that were not emailed yet
import smtplib, sys
from email.mime.text import MIMEText
from ..config import GMAIL_USER, GMAIL_APP_PASSWORD, DIGEST_TO
from ..db import get_db

def main():
    if not (GMAIL_USER and GMAIL_APP_PASSWORD):
        print("Digest skipped: Gmail not configured"); return
    db = get_db()
    rows = db.execute("SELECT id,channel,severity,category,summary FROM posts WHERE digested=0 "
                      "AND severity IN ('critical','high') AND summary IS NOT NULL").fetchall()
    if not rows:
        print("No new critical/high posts."); return
    body = "Cyber Intel Digest\n\n" + "\n\n".join(
        f"[{s.upper()}] [{c}] {ch}\n{t}" for _, ch, s, c, t in rows)
    msg = MIMEText(body); msg["Subject"] = f"Cyber Digest: {len(rows)} new alerts"
    msg["From"], msg["To"] = GMAIL_USER, DIGEST_TO
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls(); s.login(GMAIL_USER, GMAIL_APP_PASSWORD); s.send_message(msg)
    db.executemany("UPDATE posts SET digested=1 WHERE id=?", [(r[0],) for r in rows]); db.commit()
    print(f"Digest sent ({len(rows)} alerts)")

if __name__ == "__main__":
    main()
