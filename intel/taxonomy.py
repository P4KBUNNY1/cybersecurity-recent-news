# taxonomy.py - one fixed set of labels, so charts never show junk categories
CATEGORIES = ["Vulnerability", "Malware", "Ransomware", "Threat News",
              "Privacy & Data Leak", "Research & Tools", "Bug Bounty",
              "Promotion / Other"]
SEVERITIES = ["critical", "high", "medium", "low"]

CAT_COLORS = dict(zip(CATEGORIES, ["#C2410C", "#7C3AED", "#BE123C", "#0369A1",
                                   "#0F766E", "#4D7C0F", "#B45309", "#64748B"]))
SEV_COLORS = {"critical": "#B91C1C", "high": "#EA580C", "medium": "#CA8A04", "low": "#15803D"}

_KEYWORDS = [  # first match wins
    ("Ransomware", ["ransomware", "lockbit", "ransom"]),
    ("Malware", ["malware", "trojan", "botnet", "stealer", "backdoor", "apt"]),
    ("Vulnerability", ["cve-", "vulnerab", "exploit", "rce", "zero-day", "0day", "sqli", "xss", "patch"]),
    ("Bug Bounty", ["bug bounty", "bugbounty", "hackerone", "bugcrowd", "payout", "bounty"]),
    ("Privacy & Data Leak", ["leak", "breach", "privacy", "data exposed"]),
    ("Research & Tools", ["tool", "research", "paper", "github", "checklist", "writeup", "poc"]),
    ("Threat News", ["attack", "campaign", "news", "advisory"]),
]

def norm_category(value, text=""):
    v = (value or "").strip().lower()
    if v and " or " not in v:            # " or " = model echoed the prompt list
        for c in CATEGORIES:
            if v == c.lower():
                return c
        alias = {"vuln": "Vulnerability", "news": "Threat News", "privacy": "Privacy & Data Leak",
                 "research": "Research & Tools", "malware": "Malware", "ransomware": "Ransomware",
                 "bug bounty": "Bug Bounty", "bugbounty": "Bug Bounty"}
        if v in alias:
            return alias[v]
    t = (text or "").lower()
    for cat, words in _KEYWORDS:
        if any(w in t for w in words):
            return cat
    return "Promotion / Other"

def norm_severity(value):
    v = (value or "").strip().lower()
    return v if v in SEVERITIES else "low"
