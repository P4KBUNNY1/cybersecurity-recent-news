# pipeline.py - fetch -> analyze -> index (-> digest).  Run:  python run.py pipeline [--loop 30] [--digest]
import argparse, os, subprocess, sys, time, datetime as dt
from ..config import ROOT, LOCK_FILE, LOG_FILE
STEPS = [("Fetch", "intel.jobs.scraper"), ("Analyze", "intel.jobs.analyze"), ("Index", "intel.rag")]

def log(msg):
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(line + "\n")

def run_once(digest):
    if LOCK_FILE.exists() and time.time() - LOCK_FILE.stat().st_mtime < 3600:
        log("Another run is in progress - skipping"); return
    LOCK_FILE.touch()
    try:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        for name, module in STEPS + ([("Digest", "intel.jobs.digest")] if digest else []):
            r = subprocess.run([sys.executable, "-m", module], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", cwd=ROOT, env=env)
            out = r.stdout.strip().splitlines()
            log(f"{name}: {'ok' if r.returncode == 0 else 'FAILED'}")
            for line in (out if name == "Fetch" else out[-1:]):
                log(f"   {line}")
            if r.returncode: log(r.stderr.strip()[-400:])
    finally:
        LOCK_FILE.unlink(missing_ok=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--loop", type=int, metavar="MINUTES", help="repeat every N minutes")
    p.add_argument("--digest", action="store_true", help="also email new critical/high posts")
    a = p.parse_args()
    while True:
        run_once(a.digest)
        if not a.loop: break
        time.sleep(a.loop * 60)

if __name__ == "__main__":
    main()
