# dashboard.py - Streamlit UI.  Start with:  python run.py dashboard
import json, collections, html, subprocess, sys, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # so 'intel' can be imported
import pandas as pd, plotly.express as px, streamlit as st
from intel.config import ROOT
from intel.db import get_db
from intel.taxonomy import CATEGORIES, SEVERITIES, CAT_COLORS, SEV_COLORS, norm_category, norm_severity

st.set_page_config(page_title="Cyber Intel Board", layout="wide", page_icon="🛡️")
st.markdown("""<style>
.block-container{padding-top:1.6rem;max-width:1300px}
.kpi{background:#fff;border:1px solid #dde3ea;border-radius:8px;padding:12px 16px;border-top:4px solid var(--c)}
.kpi b{font-size:1.9rem;display:block;line-height:1.1}.kpi span{color:#5b6b7a;font-size:.85rem}
.post{background:#fff;border:1px solid #dde3ea;border-left:6px solid var(--c);border-radius:6px;padding:12px 16px;margin:10px 0 2px}
.post h4{margin:6px 0 4px;font-size:1.02rem}.post p{margin:0;color:#334155;font-size:.93rem}
.badge{display:inline-block;padding:1px 9px;border-radius:10px;font-size:.75rem;font-weight:600;color:#fff;margin-right:6px}
.meta{color:#64748b;font-size:.8rem;margin-top:6px}
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load():
    df = pd.read_sql("SELECT id,channel,date,text,summary,category,severity,entities FROM posts", get_db()).fillna("")
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df["category"] = [norm_category(c, t) for c, t in zip(df.category, df.text)]
    df["severity"] = df.severity.map(norm_severity)
    df["analyzed"] = df.summary != ""
    ok = df.channel.str.fullmatch(r"\w+")
    df["link"] = ["https://t.me/" + c + "/" + i.rsplit("_", 1)[-1] if g else "" for c, i, g in zip(df.channel, df.id, ok)]
    return df.sort_values("date", ascending=False)

df = load()
top = st.columns([5, 1])
top[0].title("🛡️ Cyber Intel Board")
if top[1].button("↻ Refresh data"): st.cache_data.clear(); st.rerun()
if df.empty:
    st.info("No posts yet. Run `python pipeline.py` to fetch and analyze channels."); st.stop()

# ---- sidebar filters
sb = st.sidebar; sb.header("Filters")
d_min, d_max = df.date.min().date(), df.date.max().date()
rng = sb.date_input("Date range", (d_min, d_max), min_value=d_min, max_value=d_max)
sev = sb.multiselect("Severity", SEVERITIES, SEVERITIES)
cat = sb.multiselect("Category", CATEGORIES, [c for c in CATEGORIES if c in set(df.category)])
ch = sb.multiselect("Channel", sorted(df.channel.unique()), sorted(df.channel.unique()))
q = sb.text_input("Search text")
if sb.button("▶ Run pipeline now"):
    with st.spinner("Fetching and analyzing..."):
        subprocess.run([sys.executable, str(ROOT / "run.py"), "pipeline"], cwd=ROOT)
    st.cache_data.clear(); st.rerun()
sb.caption(f"Newest post: {df.date.max():%d %b %Y %H:%M} UTC")

f = df[df.severity.isin(sev) & df.category.isin(cat) & df.channel.isin(ch)]
if isinstance(rng, tuple) and len(rng) == 2:
    f = f[(f.date.dt.date >= rng[0]) & (f.date.dt.date <= rng[1])]
if q: f = f[f.text.str.contains(q, case=False) | f.summary.str.contains(q, case=False)]

# ---- KPIs
last24 = f[f.date >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=1)]
kp = [("Posts shown", len(f), "#0F766E"), ("Critical", (f.severity == "critical").sum(), SEV_COLORS["critical"]),
      ("High", (f.severity == "high").sum(), SEV_COLORS["high"]), ("Last 24 hours", len(last24), "#0369A1"),
      ("Channels", f.channel.nunique(), "#64748B")]
for col, (label, val, c) in zip(st.columns(5), kp):
    col.markdown(f'<div class="kpi" style="--c:{c}"><b>{val}</b><span>{label}</span></div>', unsafe_allow_html=True)
pending = int((~f.analyzed).sum())
if pending: st.caption(f"{pending} posts are waiting for AI analysis (shown as Low until analyzed).")
st.write("")

VIEWS = ["📊 Overview", "📰 Threat feed", "🔎 Keywords & IOCs", "💬 Ask the archive"]
question = st.chat_input("Ask the archive…  (Enter or the arrow sends)")   # pinned to the bottom of the page
if question:
    st.session_state["view"] = VIEWS[3]                                     # jump to the chat view
view = st.radio("View", VIEWS, horizontal=True, key="view", label_visibility="collapsed")

if view == VIEWS[0]:
    if f.empty: st.warning("No posts match these filters.")
    else:
        a, b = st.columns(2)
        c = f.category.value_counts().reindex(CATEGORIES).dropna().reset_index()
        c.columns = ["Category", "Posts"]
        fig = px.bar(c.sort_values("Posts"), x="Posts", y="Category", orientation="h", text="Posts",
                     color="Category", color_discrete_map=CAT_COLORS, title="Posts by category")
        fig.update_layout(showlegend=False, yaxis_title=None, height=360); a.plotly_chart(fig, use_container_width=True)
        s = f.severity.value_counts().reindex(SEVERITIES).fillna(0).reset_index()
        s.columns = ["Severity", "Posts"]
        fig = px.bar(s, x="Severity", y="Posts", text="Posts", color="Severity",
                     color_discrete_map=SEV_COLORS, title="Posts by severity")
        fig.update_layout(showlegend=False, height=360); b.plotly_chart(fig, use_container_width=True)

        day = f.assign(Day=f.date.dt.date).groupby(["Day", "severity"]).size().reset_index(name="Posts")
        fig = px.bar(day, x="Day", y="Posts", color="severity", color_discrete_map=SEV_COLORS,
                     category_orders={"severity": SEVERITIES}, title="Posts per day, by severity",
                     labels={"severity": "Severity"})
        st.plotly_chart(fig, use_container_width=True)

        a, b = st.columns(2)
        hm = pd.crosstab(f.category, f.severity).reindex(index=CATEGORIES, columns=SEVERITIES).dropna(how="all").fillna(0)
        fig = px.imshow(hm, text_auto=True, aspect="auto", color_continuous_scale="OrRd",
                        title="Category × severity", labels=dict(x="Severity", y="Category", color="Posts"))
        a.plotly_chart(fig, use_container_width=True)
        chn = f.channel.value_counts().reset_index(); chn.columns = ["Channel", "Posts"]
        fig = px.bar(chn, x="Channel", y="Posts", text="Posts", title="Posts per channel",
                     color_discrete_sequence=["#0F766E"])
        b.plotly_chart(fig, use_container_width=True)

if view == VIEWS[1]:
    n = st.slider("Posts to show", 10, 200, 30, step=10)
    st.caption(f"Showing {min(n, len(f))} of {len(f)} matching posts, newest first")
    for _, r in f.head(n).iterrows():
        title = html.escape((r.summary or r.text)[:160])
        st.markdown(
            f'<div class="post" style="--c:{SEV_COLORS[r.severity]}">'
            f'<span class="badge" style="background:{SEV_COLORS[r.severity]}">{r.severity.upper()}</span>'
            f'<span class="badge" style="background:{CAT_COLORS[r.category]}">{r.category}</span>'
            f'<h4>{title}</h4><div class="meta">{html.escape(r.channel)} · {r.date:%d %b %Y, %H:%M} UTC · '
            + (f'<a href="{r.link}" target="_blank">Open on Telegram</a>' if r.link else '') + '</div></div>', unsafe_allow_html=True)
        with st.expander("Read full post"):
            st.text(r.text)

if view == VIEWS[2]:
    ents = [json.loads(e) for e in f.entities if e]
    cnt = lambda k: collections.Counter(x for e in ents for x in e.get(k, []))
    m = st.columns(5)
    for col, (lab, k) in zip(m, [("CVEs", "cves"), ("IP addresses", "ips"), ("File hashes", "hashes"),
                                 ("Domains", "domains"), ("ATT&CK techniques", "ttps")]):
        col.metric(lab, len(cnt(k)))
    if not ents: st.info("No keyword data yet. Run python analyze.py (or python pipeline.py).")
    a, b = st.columns(2)
    for box, k, title, color in [(a, "keywords", "Top security keywords", "#0369A1"), (b, "threats", "Named threats (malware, ransomware, actors)", "#B91C1C")]:
        c = cnt(k).most_common(15)
        if c:
            d = pd.DataFrame(c, columns=["Term", "Posts"]).sort_values("Posts")
            fig = px.bar(d, x="Posts", y="Term", orientation="h", text="Posts", title=title, color_discrete_sequence=[color])
            fig.update_layout(yaxis_title=None, height=440); box.plotly_chart(fig, use_container_width=True)
        else: box.caption(f"{title}: nothing found yet")
    cv = cnt("cves").most_common(30)
    if cv:
        st.subheader("CVEs mentioned")
        st.dataframe(pd.DataFrame(cv, columns=["CVE", "Mentions"]).assign(
            Details=lambda d: "https://nvd.nist.gov/vuln/detail/" + d.CVE),
            column_config={"Details": st.column_config.LinkColumn("NVD page")}, hide_index=True, use_container_width=True)

def _stop():                                    # runs first on the rerun the Stop click causes
    if st.session_state.get("chat"):
        st.session_state["chat"][-1]["stopped"] = True

def _show(m):
    with st.chat_message(m["role"]):
        st.markdown((m["content"] or "") + ("\n\n*⏹ Stopped*" if m.get("stopped") else ""))
        if m.get("web"):
            with st.expander(f"Web sources ({len(m['web'])})"):
                for n_, w in enumerate(m["web"], 1):
                    st.markdown(f"**[W{n_}]** [{w['title']}]({w['url']})  \n{w['content'][:220]}...")
        if m.get("sources"):
            with st.expander(f"Sources ({len(m['sources'])})"):
                for s_ in m["sources"]:
                    link = f" · [open]({s_['link']})" if s_["link"] else ""
                    st.markdown(f"**[{s_['n']}]** {s_['channel']} · {s_['date']} · "
                                f"{s_['category'] or '?'} · {s_['severity'] or '?'}{link}  \n{s_['snippet']}...")

if view == VIEWS[3]:
    chat = st.session_state.setdefault("chat", [])
    head = st.columns([4, 3, 1])
    head[0].caption("Answers come only from the posts you collected. First time: "
                    "ollama pull nomic-embed-text, then python run.py index")
    use_web = head[1].toggle("🌐 Use internet (web + NVD + CISA KEV)", key="use_web")
    if head[2].button("Clear chat", disabled=not chat):
        st.session_state["chat"] = []; st.rerun()
    if not chat and not question:
        st.info("Try: “Which ransomware groups were mentioned?” · “Summarize the critical posts” · "
                "“What new vulnerabilities were discussed?”")
    for m in chat:
        _show(m)
    if question:
        history = chat[-6:]
        chat.append({"role": "user", "content": question})
        _show(chat[-1])
        chat.append({"role": "assistant", "content": "", "sources": [], "web": [], "stopped": False})
        with st.chat_message("assistant"):
            st.button("⏹ Stop generating", on_click=_stop, key="stop_btn")
            box = st.empty(); box.markdown("*Searching the archive and thinking…*")
            from intel.rag import ask_stream
            for kind, val in ask_stream(question, history, web=use_web):
                if kind == "web":
                    chat[-1]["web"] = val
                elif kind == "sources":
                    chat[-1]["sources"] = val
                else:
                    chat[-1]["content"] += val
                    box.markdown(chat[-1]["content"] + " ▌")
        st.rerun()                                # redraw cleanly (removes the Stop button)
