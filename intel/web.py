# web.py - internet access for the chat. Only the QUESTION text leaves your PC, never your saved posts.
import os, re, json, time, urllib.request
from .extract import CVE
from .config import KEV_CACHE
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId="

def _http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "cyber-intel/1.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.load(r)

def web_search(query, n=5):
    """1) Ollama web search API (needs OLLAMA_API_KEY)  2) fallback: ddgs (no key, less reliable)."""
    key = os.getenv("OLLAMA_API_KEY")
    if key:
        try:
            r = _http("https://ollama.com/api/web_search",
                      json.dumps({"query": query, "max_results": n}).encode(),
                      {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            return [dict(title=x["title"], url=x["url"], content=x["content"][:800]) for x in r["results"]]
        except Exception:
            pass
    try:
        from ddgs import DDGS
        return [dict(title=x["title"], url=x["href"], content=x["body"][:800])
                for x in DDGS().text(query, max_results=n)]
    except Exception:
        return []

def _kev():
    path = KEV_CACHE
    if not os.path.exists(path) or time.time() - os.path.getmtime(path) > 12 * 3600:
        with open(path, "w") as f: json.dump(_http(KEV_URL), f)
    return {v["cveID"]: v for v in json.load(open(path))["vulnerabilities"]}

def cve_info(cve):
    """Official facts: NVD description + CVSS score, and whether CISA lists it as exploited."""
    parts, url = [], f"https://nvd.nist.gov/vuln/detail/{cve}"
    try:
        c = _http(NVD_URL + cve)["vulnerabilities"][0]["cve"]
        desc = next((d["value"] for d in c["descriptions"] if d["lang"] == "en"), "")
        parts.append(f"NVD: {desc[:600]}")
        for k in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30"):
            if c.get("metrics", {}).get(k):
                m = c["metrics"][k][0]["cvssData"]; parts.append(f"CVSS {m['baseScore']} ({m['baseSeverity']})"); break
        parts.append(f"Published {c.get('published', '')[:10]}")
    except Exception:
        parts.append("NVD lookup failed or CVE not found")
    try:
        k = _kev().get(cve)
        parts.append(f"CISA KEV: YES - actively exploited (added {k['dateAdded']}, ransomware use: {k['knownRansomwareCampaignUse']})"
                     if k else "CISA KEV: not listed")
    except Exception:
        pass
    return dict(title=cve, url=url, content=" | ".join(parts))

def context(question, extra_cves=()):
    """Everything the model gets from the internet for one question."""
    cves = list(dict.fromkeys([c.upper() for c in CVE.findall(question)] + list(extra_cves)))[:3]
    return [cve_info(c) for c in cves] + web_search(question[:200])
