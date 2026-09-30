#!/usr/bin/env python
"""One entry point for everything:  python run.py <command>

  dashboard   open the web dashboard
  pipeline    fetch + analyze + index   (options: --loop 30   --digest)
  fetch       only fetch new Telegram posts
  analyze     only run the AI labeling + keyword extraction
  index       only build the chat search index
  digest      email new critical/high posts
  login       log in to Telegram once (creates data/session.session)
  channels    list your Telegram channels with their exact usernames
  export      write data/train.jsonl for fine-tuning
  model       build the custom Ollama model from models/Modelfile
"""
import runpy, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

JOBS = {"pipeline": "intel.jobs.pipeline", "fetch": "intel.jobs.scraper", "analyze": "intel.jobs.analyze",
        "index": "intel.rag", "digest": "intel.jobs.digest", "login": "intel.jobs.login",
        "channels": "intel.jobs.channels", "export": "intel.jobs.export_training"}

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "dashboard":
        raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(ROOT / "app" / "dashboard.py"),
                                          "--browser.gatherUsageStats", "false"], cwd=ROOT))
    if cmd == "model":
        name = sys.argv[2] if len(sys.argv) > 2 else "cyber-analyst"
        raise SystemExit(subprocess.call(["ollama", "create", name, "-f", str(ROOT / "models" / "Modelfile")]))
    if cmd in JOBS:
        sys.argv = [JOBS[cmd]] + sys.argv[2:]
        runpy.run_module(JOBS[cmd], run_name="__main__", alter_sys=True)
        return
    print(__doc__)

if __name__ == "__main__":
    main()
