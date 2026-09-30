# extract.py - instant, no-AI keyword / IOC extraction + rule-based severity boost
import re, json
CVE = re.compile(r"CVE-\d{4}-\d{4,7}", re.I)
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HASH = re.compile(r"\b(?:[a-f0-9]{64}|[a-f0-9]{40}|[a-f0-9]{32})\b", re.I)
TTP = re.compile(r"\bT1\d{3}(?:\.\d{3})?\b")
DOMAIN = re.compile(r"\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|ru|cn|xyz|top|info|biz|onion|cc|to)\b", re.I)
THREATS = ["lockbit", "blackcat", "alphv", "clop", "akira", "play", "revil", "conti", "blackbasta", "qilin",
           "redline", "lumma", "emotet", "qakbot", "cobalt strike", "mimikatz", "metasploit", "asyncrat",
           "apt28", "apt29", "apt41", "lazarus", "sandworm", "volt typhoon", "scattered spider", "fin7", "kimsuky"]
VOCAB = ["phishing", "ransomware", "zero-day", "0day", "rce", "sql injection", "sqli", "xss", "csrf", "ssrf",
         "idor", "privilege escalation", "supply chain", "botnet", "ddos", "malware", "backdoor", "stealer",
         "data breach", "leak", "exploit", "poc", "patch", "bug bounty", "pentest", "oscp", "osint",
         "active directory", "cloud", "aws", "azure", "kubernetes", "docker", "mfa", "vpn", "firewall",
         "android", "ios", "windows", "linux", "wordpress", "api", "ai", "llm", "jailbreak"]
EXPLOIT_WORDS = ["actively exploited", "in the wild", "zero-day", "0day", "known exploited", "kev", "mass exploitation"]

def _has(word, t):
    return re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", t) is not None

def extract(text):
    t = (text or "").lower()
    ips = [i for i in set(IPV4.findall(text or "")) if all(int(p) < 256 for p in i.split("."))]
    return {"cves": sorted({c.upper() for c in CVE.findall(text or "")}), "ips": ips,
            "hashes": sorted(set(h.lower() for h in HASH.findall(text or ""))),
            "ttps": sorted(set(TTP.findall(text or ""))),
            "domains": sorted({d.lower() for d in DOMAIN.findall(text or "")})[:10],
            "threats": [w for w in THREATS if _has(w, t)],
            "keywords": [w for w in VOCAB if _has(w, t)]}

def adjust_severity(sev, text, ents=None):
    """Rules the small model gets wrong: exploited-in-the-wild or ransomware never stay 'low'."""
    ents, t = ents or extract(text), (text or "").lower()
    order = ["low", "medium", "high", "critical"]
    floor = "low"
    if ents["cves"] or "ransomware" in ents["keywords"] or ents["threats"]: floor = "medium"
    if any(w in t for w in EXPLOIT_WORDS): floor = "critical" if ents["cves"] else "high"
    if "rce" in ents["keywords"] and ents["cves"]: floor = max(floor, "high", key=order.index)
    return max(sev, floor, key=order.index)

def dumps(text): return json.dumps(extract(text))
