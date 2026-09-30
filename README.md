# Cyber Intel Board

Collects posts from Telegram cybersecurity channels, labels them with a local AI (Ollama),
extracts keywords/IOCs, and shows everything in a dashboard with a chat that can also use the internet.

## Folder layout

```
cyber_intel/
├── run.py                  ← the ONE command you use:  python run.py <command>
├── .env                    ← your secrets and settings (copy from .env.example)
├── requirements.txt
├── app/
│   └── dashboard.py        ← the web dashboard (Streamlit)
├── intel/                  ← the code
│   ├── config.py           settings + every file path
│   ├── db.py               database setup
│   ├── taxonomy.py         fixed categories / severities / colors
│   ├── extract.py          keyword + IOC extraction, severity rules (no AI)
│   ├── llm.py              calls Ollama (thinking off = faster)
│   ├── rag.py              "Ask the archive" search + streaming answers
│   ├── web.py              internet: Ollama web search, NVD, CISA KEV
│   └── jobs/
│       ├── scraper.py      fetch new Telegram posts
│       ├── analyze.py      AI labels + keywords
│       ├── pipeline.py     fetch → analyze → index (→ digest), with --loop
│       ├── digest.py       email new critical/high posts
│       ├── login.py        one-time Telegram login
│       ├── channels.py     list your channels + exact usernames
│       └── export_training.py
├── models/Modelfile        ← custom Ollama model (cyber-analyst)
├── scripts/                ← Windows launcher + desktop shortcut maker
├── data/                   ← your database, Telegram session, caches  (git-ignored)
└── logs/                   ← pipeline.log                              (git-ignored)
```

## First-time setup (Windows)

```powershell
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # then fill in .env
ollama pull qwen3.5:2b
ollama pull nomic-embed-text
python run.py model             # builds the custom model "cyber-analyst"
python run.py login             # only if you have no data\session.session
python run.py channels          # shows exact channel usernames for CHANNELS=
```

Put `OLLAMA_MODEL=cyber-analyst` in `.env`.
Coming from the old flat folder? Copy your old `cyber.db` and `session.session` into the project
folder (or into `data/`). They are moved into `data/` automatically.

## Everyday commands

| Command | What it does |
|---|---|
| `python run.py dashboard` | Open the dashboard |
| `python run.py pipeline` | Fetch + analyze + index once |
| `python run.py pipeline --loop 60` | Repeat every 60 minutes |
| `python run.py pipeline --digest` | Also email new critical/high alerts |
| `python run.py fetch` / `analyze` / `index` | Run a single step |
| `python run.py export` | Write `data/train.jsonl` for fine-tuning |

## Desktop shortcut

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_shortcut.ps1
```
Creates "Cyber Intel Board" (starts Ollama, fetches, analyzes, opens dashboard) and a
"view only" version that skips the fetch.

## Internet for the chat

Turn on the 🌐 switch in the chat view. Optional: put `OLLAMA_API_KEY` in `.env`
(free key at ollama.com/settings/keys). Without it, a DuckDuckGo fallback is used.
CVE questions also check NVD and CISA's Known Exploited list.

Never share or commit `.env` or `data/session.session`.
