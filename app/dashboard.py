# dashboard.py - Streamlit UI. Start with: python run.py dashboard
# UI-only refresh: the database, pipeline, RAG, scraping, analysis and web-search
# functions remain unchanged.
import collections
import datetime as dt
import html
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from intel.config import ROOT
from intel.db import get_db
from intel.taxonomy import (
    CATEGORIES,
    SEVERITIES,
    CAT_COLORS,
    SEV_COLORS,
    norm_category,
    norm_severity,
)

st.set_page_config(
    page_title="Cybersecurity trends",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# UI-only theme state. Light mode is the default because the dashboard contains dense text.
if "ui_dark_mode" not in st.session_state:
    st.session_state["ui_dark_mode"] = False

THEMES = {
    "light": {
        "bg": "#F4F7FB", "bg2": "#EEF2F7", "panel": "#FFFFFF", "panel2": "#F8FAFC", "panel3": "#F1F5F9",
        "line": "#D9E2EC", "line_soft": "#E7EDF4", "text": "#172033", "muted": "#5B6578", "muted2": "#7A879A",
        "accent": "#0F766E", "accent2": "#2563EB", "accent_soft": "rgba(15,118,110,.10)", "blue_soft": "rgba(37,99,235,.09)",
        "header": "rgba(255,255,255,.88)", "input": "#FFFFFF", "hover": "#F3FAF8", "chart_grid": "#E6EBF2",
        "chart_axis": "#C8D2DF", "chart_text": "#536176", "heatmap_start": "#F8FAFC", "heatmap_mid": "#CDEFE7", "heatmap_end": "#0F766E",
        "shadow": "0 16px 45px rgba(31,45,61,.08)",
    },
    "dark": {
        "bg": "#0B1020", "bg2": "#0F172A", "panel": "#111827", "panel2": "#152033", "panel3": "#1B2940",
        "line": "#29384F", "line_soft": "#1E2A3D", "text": "#F7FAFC", "muted": "#AAB6C8", "muted2": "#7F8BA1",
        "accent": "#31C7A6", "accent2": "#60A5FA", "accent_soft": "rgba(49,199,166,.12)", "blue_soft": "rgba(96,165,250,.11)",
        "header": "rgba(11,16,32,.88)", "input": "#0F172A", "hover": "#142337", "chart_grid": "#233149",
        "chart_axis": "#32445F", "chart_text": "#A9B6C9", "heatmap_start": "#101827", "heatmap_mid": "#244B45", "heatmap_end": "#31C7A6",
        "shadow": "0 16px 45px rgba(0,0,0,.20)",
    },
}
UI = THEMES["dark" if st.session_state["ui_dark_mode"] else "light"]

# -----------------------------------------------------------------------------
# Visual system
# -----------------------------------------------------------------------------
_theme_vars = ";".join(f"--{k.replace('_', '-')}: {v}" for k, v in UI.items())
st.markdown(f"<style>:root{{{_theme_vars}}}</style>", unsafe_allow_html=True)
st.markdown(
    """
<style>
html, body { color:var(--text); }
[data-testid="stAppViewContainer"] { background:radial-gradient(circle at 0% 0%,var(--accent-soft),transparent 22%),radial-gradient(circle at 100% 0%,var(--blue-soft),transparent 20%),var(--bg); color:var(--text); }
[data-testid="stHeader"] { background:var(--header) !important; backdrop-filter:blur(14px); }
[data-testid="stMainBlockContainer"], .block-container { max-width:1500px; padding:1.25rem 2.15rem 5rem; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,var(--panel) 0%,var(--bg2) 100%); border-right:1px solid var(--line-soft); }
[data-testid="stSidebar"] > div:first-child { padding-top:1rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:var(--muted); }
[data-testid="stSidebar"] hr { border-color:var(--line-soft) !important; }
h1,h2,h3,h4,h5,h6,p,li,label,[data-testid="stWidgetLabel"] p { color:var(--text); }
[data-testid="stWidgetLabel"] p,label { font-size:.78rem !important; font-weight:680 !important; letter-spacing:.005em; transition:color .16s ease,transform .16s ease; }
[data-testid="stWidgetLabel"] p:hover,label:hover { color:var(--accent) !important; transform:translateX(1px); }
.small-muted { color:var(--muted) !important; font-size:.8rem; line-height:1.55; }
.eyebrow { text-transform:uppercase; letter-spacing:.15em; font-size:.66rem; font-weight:850; color:var(--accent); margin-bottom:.34rem; }
a { color:var(--accent2) !important; text-decoration:none !important; font-weight:700; transition:opacity .16s ease,color .16s ease; }
a:hover { opacity:.78; text-decoration:underline !important; }
.brand { display:flex; align-items:center; gap:.72rem; padding:.15rem .2rem .85rem; margin-bottom:.2rem; }
.brand-mark { width:44px; height:44px; display:grid; place-items:center; border:1px solid var(--line); border-radius:13px; background:linear-gradient(145deg,var(--accent-soft),var(--blue-soft)); box-shadow:var(--shadow); font-size:1.27rem; transition:transform .18s ease,box-shadow .18s ease; }
.brand-mark:hover { transform:translateY(-1px) rotate(-2deg); box-shadow:0 12px 30px rgba(15,118,110,.14); }
.brand-title { color:var(--text); font-size:1.02rem; font-weight:850; line-height:1.1; letter-spacing:.015em; }
.brand-sub { color:var(--muted); font-size:.7rem; margin-top:.23rem; }
.hero { position:relative; overflow:hidden; border:1px solid var(--line); border-radius:20px; padding:1.22rem 1.3rem; background:linear-gradient(140deg,var(--panel) 0%,var(--panel2) 100%); box-shadow:var(--shadow); }
.hero::after { content:""; position:absolute; width:170px; height:170px; right:-85px; top:-90px; border-radius:50%; background:var(--accent-soft); }
.hero-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; position:relative; z-index:1; }
.hero-title { color:var(--text); font-size:clamp(1.55rem,2.35vw,2.25rem); font-weight:880; margin:0; letter-spacing:-.035em; }
.hero-sub { margin:.38rem 0 0; color:var(--muted); font-size:.88rem; line-height:1.5; max-width:850px; }
.hero-status { display:inline-flex; align-items:center; gap:.46rem; padding:.42rem .7rem; border-radius:999px; border:1px solid var(--line); background:var(--accent-soft); color:var(--accent); font-size:.7rem; font-weight:850; letter-spacing:.055em; white-space:nowrap; }
.hero-status-dot { width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:0 0 0 4px var(--accent-soft); }
.kpi-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:.78rem; margin:1rem 0 1.1rem; }
.kpi-card { position:relative; overflow:hidden; min-height:118px; border:1px solid var(--line); border-radius:16px; padding:.98rem 1rem; background:linear-gradient(155deg,var(--panel) 0%,var(--panel2) 100%); box-shadow:0 8px 28px rgba(31,45,61,.055); transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease; }
.kpi-card::after { content:""; position:absolute; right:-35px; bottom:-58px; width:112px; height:112px; border-radius:50%; background:var(--kpi,var(--accent)); opacity:.11; }
.kpi-card:hover { transform:translateY(-2px); border-color:var(--accent); box-shadow:var(--shadow); }
.kpi-top { display:flex; justify-content:space-between; align-items:center; gap:.5rem; }
.kpi-icon { font-size:1rem; opacity:.94; }
.kpi-label { color:var(--muted); font-size:.74rem; font-weight:700; }
.kpi-value { color:var(--text); font-size:1.72rem; font-weight:880; line-height:1.1; margin-top:.58rem; letter-spacing:-.038em; }
.kpi-help { color:var(--muted-2); font-size:.71rem; margin-top:.3rem; line-height:1.4; }
.section-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:.35rem 0 .72rem; }
.section-title { color:var(--text); font-size:1.05rem; font-weight:840; margin:0; letter-spacing:-.012em; }
.section-sub { color:var(--muted); font-size:.79rem; margin:.18rem 0 0; line-height:1.45; }
.panel { border:1px solid var(--line); border-radius:17px; padding:1rem 1.02rem 1.05rem; background:var(--panel); box-shadow:0 7px 25px rgba(31,45,61,.045); }
.panel-tight { padding:.82rem .92rem; }
.panel-label { color:var(--muted-2); text-transform:uppercase; letter-spacing:.12em; font-size:.64rem; font-weight:850; margin-bottom:.58rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line) !important; border-radius:17px !important; background:var(--panel) !important; box-shadow:0 7px 25px rgba(31,45,61,.045); }
.feed-card { border:1px solid var(--line); border-left:3px solid var(--sev,#64748b); border-radius:14px; padding:.84rem .92rem; margin:.55rem 0; background:linear-gradient(160deg,var(--panel) 0%,var(--panel2) 100%); transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease,background .16s ease; }
.feed-card:hover { transform:translateY(-1px); border-color:var(--accent); background:linear-gradient(160deg,var(--hover) 0%,var(--panel) 100%); box-shadow:0 10px 28px rgba(31,45,61,.07); }
.feed-row { display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; }
.feed-title { margin:.43rem 0 .28rem; font-size:.95rem; line-height:1.48; font-weight:770; color:var(--text); }
.feed-meta { color:var(--muted); font-size:.72rem; line-height:1.5; }
.feed-badge { display:inline-flex; align-items:center; gap:.3rem; padding:.24rem .52rem; margin-right:.36rem; border:1px solid var(--line); border-radius:999px; font-size:.63rem; font-weight:850; letter-spacing:.045em; background:var(--panel2); }
.feed-dot { width:6px; height:6px; border-radius:50%; background:currentColor; }
[data-testid="stButton"] > button,[data-testid="stLinkButton"] > a { min-height:2.45rem; border-radius:12px !important; border:1px solid var(--line) !important; background:var(--panel) !important; color:var(--text) !important; font-size:.78rem !important; font-weight:760 !important; letter-spacing:.005em; box-shadow:0 3px 10px rgba(31,45,61,.035); transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease,background .16s ease,color .16s ease; }
[data-testid="stButton"] > button:hover,[data-testid="stLinkButton"] > a:hover { transform:translateY(-1px); border-color:var(--accent) !important; background:var(--hover) !important; color:var(--accent) !important; box-shadow:0 9px 22px rgba(31,45,61,.08); }
button[kind="primary"] { background:linear-gradient(135deg,var(--accent),#0B5560) !important; border-color:var(--accent) !important; color:#FFFFFF !important; box-shadow:0 8px 20px rgba(15,118,110,.18) !important; }
button[kind="primary"] p,button[kind="primary"] span { color:#FFFFFF !important; }
button[kind="primary"]:hover { filter:brightness(1.045); transform:translateY(-1px) scale(1.005); }
[data-baseweb="select"] > div,[data-baseweb="input"] > div,[data-baseweb="textarea"] > div,[data-testid="stDateInput"] input,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input { background:var(--input) !important; color:var(--text) !important; border-color:var(--line) !important; border-radius:11px !important; }
input::placeholder,textarea::placeholder { color:var(--muted-2) !important; opacity:1 !important; }
[data-baseweb="select"] span,[data-baseweb="select"] input,[data-baseweb="input"] input,[data-baseweb="textarea"] textarea { color:var(--text) !important; }
[data-baseweb="select"] > div:hover,[data-baseweb="input"] > div:hover,[data-baseweb="textarea"] > div:hover { border-color:var(--accent) !important; }
[data-baseweb="tag"] { background:var(--accent-soft) !important; color:var(--accent) !important; border:1px solid var(--line) !important; }
[data-baseweb="popover"] { background:var(--panel) !important; border-color:var(--line) !important; box-shadow:var(--shadow) !important; }
[data-testid="stMetric"] { border:1px solid var(--line); border-radius:14px; padding:.82rem .92rem; background:var(--panel); }
[data-testid="stMetricLabel"] { color:var(--muted) !important; }
[data-testid="stMetricValue"] { color:var(--text) !important; }
[data-testid="stExpander"] { border-color:var(--line) !important; border-radius:12px !important; background:var(--panel2) !important; transition:border-color .16s ease,box-shadow .16s ease; }
[data-testid="stExpander"]:hover { border-color:var(--accent) !important; box-shadow:0 7px 20px rgba(31,45,61,.05); }
[data-testid="stTabs"] button { color:var(--muted) !important; font-weight:720 !important; transition:color .16s ease,transform .16s ease; }
[data-testid="stTabs"] button:hover { color:var(--accent) !important; transform:translateY(-1px); }
[data-testid="stTabs"] button[aria-selected="true"] { color:var(--accent) !important; }
[data-testid="stChatMessage"] { border:1px solid var(--line); border-radius:14px; margin-bottom:.68rem; background:var(--panel); }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:13px; overflow:hidden; }
.suggestion-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.65rem; }
.suggestion-card { padding:.82rem; border:1px solid var(--line); border-radius:12px; background:var(--panel2); transition:transform .16s ease,border-color .16s ease,background .16s ease,box-shadow .16s ease; }
.suggestion-card:hover { transform:translateY(-1px); border-color:var(--accent); background:var(--hover); box-shadow:0 8px 22px rgba(31,45,61,.06); }
.suggestion-title { color:var(--text); font-weight:780; font-size:.84rem; }
.empty-state { border:1px dashed var(--line); border-radius:17px; padding:2.35rem 1.2rem; text-align:center; background:var(--panel); }
.empty-icon { font-size:2rem; }
.empty-title { color:var(--text); margin-top:.5rem; font-weight:820; }
.empty-sub { color:var(--muted); font-size:.82rem; margin-top:.22rem; line-height:1.5; }
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { transition:none !important; animation:none !important; } }
@media (max-width:980px) { .kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .block-container { padding-left:1rem; padding-right:1rem; } .suggestion-grid { grid-template-columns:1fr; } }
@media (max-width:640px) { .kpi-grid { grid-template-columns:1fr; } .hero-row { align-items:flex-start; flex-direction:column; } }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Data layer: intentionally unchanged in behavior
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load():
    df = pd.read_sql(
        "SELECT id,channel,date,text,summary,category,severity,entities FROM posts",
        get_db(),
    ).fillna("")
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df["category"] = [
        norm_category(c, t) for c, t in zip(df.category, df.text)
    ]
    df = df[df["category"] != "noise"]   # FIXED: actually filters noise out
    df["severity"] = df.severity.map(norm_severity)
    df["analyzed"] = df.summary != ""
    ok = df.channel.str.fullmatch(r"\w+")
    df["link"] = [
        "https://t.me/" + c + "/" + i.rsplit("_", 1)[-1] if g else ""
        for c, i, g in zip(df.channel, df.id, ok)
    ]
    return df.sort_values("date", ascending=False)


df = load()

if "view" not in st.session_state:
    st.session_state["view"] = "overview"


def set_view(name):
    st.session_state["view"] = name


def short_number(value):
    value = int(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def panel_title(title, subtitle=""):
    st.markdown(
        f'<div class="section-head"><div><div class="section-title">{html.escape(title)}</div>'
        f'{f"<div class=\"section-sub\">{html.escape(subtitle)}</div>" if subtitle else ""}'
        "</div></div>",
        unsafe_allow_html=True,
    )


def empty_state(title, message, icon="◌"):
    st.markdown(
        f'<div class="empty-state"><div class="empty-icon">{icon}</div>'
        f'<div class="empty-title">{html.escape(title)}</div>'
        f'<div class="empty-sub">{html.escape(message)}</div></div>',
        unsafe_allow_html=True,
    )


def chart_layout(fig, height=360, margin=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=UI["chart_text"], size=11),
        title=None,
        height=height,
        margin=margin or dict(l=5, r=5, t=20, b=5),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=10),
        ),
        xaxis=dict(
            gridcolor=UI["chart_grid"],
            zeroline=False,
            linecolor=UI["chart_axis"],
            tickfont=dict(color=UI["chart_text"], size=10),
        ),
        yaxis=dict(
            gridcolor=UI["chart_grid"],
            zeroline=False,
            linecolor=UI["chart_axis"],
            tickfont=dict(color=UI["chart_text"], size=10),
        ),
    )
    return fig


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
sb = st.sidebar
st.sidebar.markdown(
    '<div class="brand"><div class="brand-mark">🛡️</div><div>'
    '<div class="brand-title">CYBER INTEL</div><div class="brand-sub">Threat intelligence workspace</div>'
    "</div></div>",
    unsafe_allow_html=True,
)

sb.markdown(
    '<div style="display:flex;align-items:center;justify-content:space-between;gap:.75rem;padding:.62rem .72rem;border:1px solid var(--line);border-radius:12px;background:var(--panel-2);margin-bottom:.7rem;">'
    '<div><div style="font-size:.72rem;font-weight:800;color:var(--text);">Appearance</div>'
    '<div class="small-muted" style="font-size:.68rem;">Light for reading · Dark for low-light work</div></div>'
    '<div style="font-size:.9rem;color:var(--accent);">☀︎  /  ☾</div></div>',
    unsafe_allow_html=True,
)
sb.toggle("Dark mode", key="ui_dark_mode", help="Switch between the light and dark dashboard themes.")

if df.empty:
    empty_state("No intelligence collected yet", "Run the pipeline to fetch and analyze Telegram posts.", "🛰️")
    st.stop()

sb.markdown("<div class=\"eyebrow\">Scope & filters</div>", unsafe_allow_html=True)
d_min, d_max = df.date.min().date(), df.date.max().date()
rng = sb.date_input(
    "Date range",
    (d_min, d_max),
    min_value=d_min,
    max_value=d_max,
)
sev = sb.multiselect("Severity", SEVERITIES, SEVERITIES)
cat = sb.multiselect(
    "Category",
    CATEGORIES,
    [c for c in CATEGORIES if c in set(df.category)],
)
ch = sb.multiselect(
    "Channel",
    sorted(df.channel.unique()),
    sorted(df.channel.unique()),
)
q = sb.text_input("Search text", placeholder="ransomware, CVE, actor…")

sb.markdown("<div style='height:.35rem'></div>", unsafe_allow_html=True)
if sb.button("▶ Run pipeline", use_container_width=True, type="primary"):
    with st.spinner("Fetching and analyzing…"):
        subprocess.run(
            [sys.executable, str(ROOT / "run.py"), "pipeline"],
            cwd=ROOT,
        )
    st.cache_data.clear()
    st.rerun()

if sb.button("↻ Refresh archive", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

sb.markdown(
    f'<div style="margin-top:.7rem;padding-top:.7rem;border-top:1px solid var(--line-soft);">'
    f'<div class="small-muted">Newest post</div>'
    f'<div style="font-size:.8rem;color:var(--text);margin-top:.16rem;">{df.date.max():%d %b %Y · %H:%M} UTC</div>'
    "</div>",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Filtering: same fields, same source data
# -----------------------------------------------------------------------------
f = df[
    df.severity.isin(sev)
    & df.category.isin(cat)
    & df.channel.isin(ch)
]
if isinstance(rng, tuple) and len(rng) == 2:
    f = f[
        (f.date.dt.date >= rng[0])
        & (f.date.dt.date <= rng[1])
    ]
if q:
    f = f[
        f.text.str.contains(q, case=False, na=False)
        | f.summary.str.contains(q, case=False, na=False)
    ]

last24 = f[f.date >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=1)]
pending = int((~f.analyzed).sum())
analyzed_pct = int(round(((len(f) - pending) / len(f)) * 100)) if len(f) else 0

# -----------------------------------------------------------------------------
# Hero header
# -----------------------------------------------------------------------------
hero_left, hero_right = st.columns([5, 1])
with hero_left:
    st.markdown(
        '<div class="hero">'
        '<div class="eyebrow">Threat intelligence operations</div>'
        '<div class="hero-row">'
        '<div><div class="hero-title">Cyber Intel Board</div>'
        '<div class="hero-sub">A focused view of collected threats, vulnerabilities, IOCs and analyst context.</div></div>'
        '<div class="hero-status"><span class="hero-status-dot"></span> ARCHIVE ONLINE</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
with hero_right:
    st.write("")

# -----------------------------------------------------------------------------
# KPI band
# -----------------------------------------------------------------------------
critical_count = int((f.severity == "critical").sum())
high_count = int((f.severity == "high").sum())
channel_count = int(f.channel.nunique())

kpis = [
    ("📡", "Posts in scope", short_number(len(f)), "Current filters", UI["accent"]),
    ("⚠", "Critical alerts", short_number(critical_count), "Highest priority", SEV_COLORS["critical"]),
    ("▲", "High alerts", short_number(high_count), "Serious activity", SEV_COLORS["high"]),
    ("◷", "Last 24 hours", short_number(len(last24)), "Recent volume", UI["accent2"]),
    ("◎", "Sources", short_number(channel_count), f"{analyzed_pct}% analyzed", UI["muted2"]),
]
html_cards = ['<div class="kpi-grid">']
for icon, label, value, help_text, accent in kpis:
    html_cards.append(
        f'<div class="kpi-card" style="--kpi:{accent};">'
        f'<div class="kpi-top"><span class="kpi-icon">{icon}</span><span class="kpi-label">{label}</span></div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-help">{html.escape(help_text)}</div>'
        "</div>"
    )
html_cards.append("</div>")
st.markdown("".join(html_cards), unsafe_allow_html=True)

if pending:
    st.markdown(
        f'<div class="small-muted" style="margin:-.45rem 0 .65rem;">'
        f'ℹ {pending} posts are waiting for AI analysis. Unanalyzed records retain the existing Low fallback.</div>',
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Main navigation
# -----------------------------------------------------------------------------
view_labels = [
    ("overview", "◈ Overview"),
    ("feed", "◫ Threat feed"),
    ("iocs", "⌁ Keywords & IOCs"),
    ("chat", "✦ Ask archive"),
]
nav_cols = st.columns(4)
for col, (key, label) in zip(nav_cols, view_labels):
    with col:
        active = st.session_state["view"] == key
        if st.button(
            label,
            use_container_width=True,
            type="primary" if active else "secondary",
            key=f"nav_{key}",
        ):
            set_view(key)

# Chat input is rendered at the page bottom, independent of the selected view.
question = st.chat_input("Ask the archive…  e.g. Which ransomware groups were mentioned?")
if question:
    st.session_state["view"] = "chat"
    st.session_state["pending_question"] = question

view = st.session_state["view"]

# -----------------------------------------------------------------------------
# Overview
# -----------------------------------------------------------------------------
if view == "overview":
    if f.empty:
        empty_state("No posts match these filters", "Adjust the sidebar filters to widen the investigation scope.", "⌕")
    else:
        panel_title("Threat overview", "Use the charts to see volume, priority and source distribution.")

        left, right = st.columns([1.55, 1])
        with left:
            with st.container(border=True):
                st.markdown('<div class="panel-label">Activity trend</div>', unsafe_allow_html=True)
                day = (
                    f.assign(Day=f.date.dt.date)
                    .groupby(["Day", "severity"])
                    .size()
                    .reset_index(name="Posts")
                )
                fig = px.bar(
                    day,
                    x="Day",
                    y="Posts",
                    color="severity",
                    color_discrete_map=SEV_COLORS,
                    category_orders={"severity": SEVERITIES},
                )
                fig.update_traces(marker_line_width=0)
                chart_layout(fig, height=365)
                fig.update_layout(
                    barmode="stack",
                    legend=dict(orientation="h", y=1.02),
                    xaxis_title=None,
                    yaxis_title=None,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with right:
            with st.container(border=True):
                st.markdown('<div class="panel-label">Severity mix</div>', unsafe_allow_html=True)
                s = (
                    f.severity.value_counts()
                    .reindex(SEVERITIES)
                    .fillna(0)
                    .reset_index()
                )
                s.columns = ["Severity", "Posts"]
                fig = go.Figure(
                    go.Pie(
                        labels=s["Severity"],
                        values=s["Posts"],
                        hole=.68,
                        marker=dict(colors=[SEV_COLORS[x] for x in s["Severity"]]),
                        textinfo="percent",
                        hovertemplate="%{label}: %{value}<extra></extra>",
                    )
                )
                fig.add_annotation(
                    text=f"<b>{len(f)}</b><br><span style='font-size:11px'>posts</span>",
                    x=.5,
                    y=.5,
                    showarrow=False,
                    font=dict(color=UI["text"], size=20),
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=365,
                    margin=dict(l=5, r=5, t=10, b=5),
                    legend=dict(font=dict(color=UI["chart_text"], size=10)),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        left, right = st.columns([1, 1])
        with left:
            with st.container(border=True):
                st.markdown('<div class="panel-label">Category distribution</div>', unsafe_allow_html=True)
                c = (
                    f.category.value_counts()
                    .reindex(CATEGORIES)
                    .fillna(0)
                    .reset_index()
                )
                c.columns = ["Category", "Posts"]
                c = c[c.Posts > 0].sort_values("Posts")
                fig = px.bar(
                    c,
                    x="Posts",
                    y="Category",
                    orientation="h",
                    color="Category",
                    color_discrete_map=CAT_COLORS,
                    text="Posts",
                )
                fig.update_traces(marker_line_width=0, textposition="outside")
                chart_layout(fig, height=360)
                fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with right:
            with st.container(border=True):
                st.markdown('<div class="panel-label">Source activity</div>', unsafe_allow_html=True)
                chn = f.channel.value_counts().head(12).reset_index()
                chn.columns = ["Channel", "Posts"]
                chn = chn.sort_values("Posts")
                fig = px.bar(
                    chn,
                    x="Posts",
                    y="Channel",
                    orientation="h",
                    text="Posts",
                )
                fig.update_traces(marker_color=UI["accent"], marker_line_width=0, textposition="outside")
                chart_layout(fig, height=360)
                fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        panel_title("Category × severity", "Counts in the current filtered scope.")
        hm = (
            pd.crosstab(f.category, f.severity)
            .reindex(index=CATEGORIES, columns=SEVERITIES)
            .fillna(0)
        )
        hm = hm.loc[(hm.sum(axis=1) > 0)]
        fig = px.imshow(
            hm,
            text_auto=True,
            aspect="auto",
            color_continuous_scale=[UI["heatmap_start"], UI["heatmap_mid"], UI["heatmap_end"]],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=UI["chart_text"], size=11),
            height=340,
            margin=dict(l=5, r=5, t=12, b=5),
            coloraxis_colorbar=dict(title="Posts", tickfont=dict(color=UI["chart_text"])),
            xaxis_title=None,
            yaxis_title=None,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        panel_title("Priority queue", "The newest critical and high-severity posts in scope.")
        priority = f[f.severity.isin(["critical", "high"])].head(5)
        if priority.empty:
            st.caption("No critical or high-severity posts match the current filters.")
        else:
            for _, r in priority.iterrows():
                sev_color = SEV_COLORS.get(r.severity, "#64748b")
                cat_color = CAT_COLORS.get(r.category, "#64748b")
                title = html.escape((r.summary or r.text).replace("\n", " ")[:190])
                link = (
                    f' · <a href="{html.escape(r.link)}" target="_blank">Open source ↗</a>'
                    if r.link
                    else ""
                )
                st.markdown(
                    f'<div class="feed-card" style="--sev:{sev_color}">'
                    f'<div class="feed-row"><div>'
                    f'<span class="feed-badge" style="color:{sev_color}"><span class="feed-dot"></span>{html.escape(r.severity.upper())}</span>'
                    f'<span class="feed-badge" style="color:{cat_color}">{html.escape(r.category)}</span>'
                    f'<div class="feed-title">{title}</div>'
                    f'<div class="feed-meta">{html.escape(r.channel)} · {r.date:%d %b %Y, %H:%M} UTC{link}</div>'
                    f'</div></div></div>',
                    unsafe_allow_html=True,
                )

# -----------------------------------------------------------------------------
# Threat feed
# -----------------------------------------------------------------------------
elif view == "feed":
    panel_title("Threat feed", "Newest collected posts, ordered for quick analyst triage.")
    toolbar_left, toolbar_right = st.columns([1, 1])
    with toolbar_left:
        feed_mode = st.radio(
            "Priority",
            ["All posts", "Critical + high"],
            horizontal=True,
            label_visibility="collapsed",
            key="feed_mode",
        )
    with toolbar_right:
        n = st.slider("Rows", 10, 200, 30, step=10, label_visibility="collapsed")
    feed = f if feed_mode == "All posts" else f[f.severity.isin(["critical", "high"])]
    st.markdown(
        f'<div class="small-muted" style="margin:.15rem 0 .55rem;">Showing {min(n, len(feed))} of {len(feed)} matching posts · newest first</div>',
        unsafe_allow_html=True,
    )
    if feed.empty:
        empty_state("No matching alerts", "Switch priority mode or relax the sidebar filters.", "◌")
    else:
        for _, r in feed.head(n).iterrows():
            sev_color = SEV_COLORS.get(r.severity, "#64748b")
            cat_color = CAT_COLORS.get(r.category, "#64748b")
            title = html.escape((r.summary or r.text).replace("\n", " ")[:190])
            source_link = (
                f'<a href="{html.escape(r.link)}" target="_blank">Open Telegram ↗</a>'
                if r.link
                else "Source link unavailable"
            )
            st.markdown(
                f'<div class="feed-card" style="--sev:{sev_color}">'
                f'<div class="feed-row"><div style="min-width:0;">'
                f'<span class="feed-badge" style="color:{sev_color}"><span class="feed-dot"></span>{html.escape(r.severity.upper())}</span>'
                f'<span class="feed-badge" style="color:{cat_color}">{html.escape(r.category)}</span>'
                f'<div class="feed-title">{title}</div>'
                f'<div class="feed-meta">{html.escape(r.channel)} · {r.date:%d %b %Y, %H:%M} UTC · {source_link}</div>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )
            with st.expander("Read full post", expanded=False):
                st.text(r.text)

# -----------------------------------------------------------------------------
# Keywords & IOCs
# -----------------------------------------------------------------------------
elif view == "iocs":
    panel_title("Keywords & IOCs", "Extracted indicators from the selected posts. Counts are unique within scope.")

    ents = [json.loads(e) for e in f.entities if e]
    cnt = lambda k: collections.Counter(x for e in ents for x in e.get(k, []))

    ioc_types = [
        ("CVEs", "cves", "▣", "Official NVD lookups remain available through the archive chat's web enrichment."),
        ("IP addresses", "ips", "⌁", "IPv4 indicators extracted from collected posts."),
        ("File hashes", "hashes", "#", "MD5, SHA-1 and SHA-256 patterns found in posts."),
        ("Domains", "domains", "◉", "Observed domains extracted from post text."),
        ("ATT&CK techniques", "ttps", "⚙", "Technique IDs matching Txxxx / Txxxx.xxx patterns."),
    ]
    cards = ['<div class="kpi-grid">']
    for label, key, icon, help_text in ioc_types:
        value = len(cnt(key))
        cards.append(
            f'<div class="kpi-card" style="--kpi:#5fb3ff;">'
            f'<div class="kpi-top"><span class="kpi-icon">{icon}</span><span class="kpi-label">{html.escape(label)}</span></div>'
            f'<div class="kpi-value">{value}</div><div class="kpi-help">{html.escape(help_text[:42])}</div></div>'
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)

    if not ents:
        empty_state("No extracted indicators yet", "Run analysis on the collected posts, then refresh the archive.", "⌁")
    else:
        a, b = st.columns(2)
        with a:
            with st.container(border=True):
                st.markdown('<div class="panel-label">Top security keywords</div>', unsafe_allow_html=True)
                c = cnt("keywords").most_common(15)
                if c:
                    d = pd.DataFrame(c, columns=["Term", "Posts"]).sort_values("Posts")
                    fig = px.bar(d, x="Posts", y="Term", orientation="h", text="Posts")
                    fig.update_traces(marker_color="#5fb3ff", marker_line_width=0, textposition="outside")
                    chart_layout(fig, height=445)
                    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("No keyword data found.")
        with b:
            with st.container(border=True):
                st.markdown('<div class="panel-label">Named threats</div>', unsafe_allow_html=True)
                c = cnt("threats").most_common(15)
                if c:
                    d = pd.DataFrame(c, columns=["Threat", "Posts"]).sort_values("Posts")
                    fig = px.bar(d, x="Posts", y="Threat", orientation="h", text="Posts")
                    fig.update_traces(marker_color="#ff6677", marker_line_width=0, textposition="outside")
                    chart_layout(fig, height=445)
                    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("No named threats found.")

        tab_cve, tab_ip, tab_hash, tab_domain, tab_ttp = st.tabs(
            ["CVEs", "IP addresses", "File hashes", "Domains", "ATT&CK"]
        )

        with tab_cve:
            cv = cnt("cves").most_common(50)
            if cv:
                cve_df = pd.DataFrame(cv, columns=["CVE", "Mentions"])
                cve_df["NVD page"] = "https://nvd.nist.gov/vuln/detail/" + cve_df.CVE
                st.dataframe(
                    cve_df,
                    column_config={"NVD page": st.column_config.LinkColumn("NVD page")},
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("No CVEs found in scope.")

        with tab_ip:
            ips = cnt("ips").most_common(100)
            if ips:
                st.dataframe(
                    pd.DataFrame(ips, columns=["IP address", "Mentions"]),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("No IPv4 indicators found.")

        with tab_hash:
            hashes = cnt("hashes").most_common(100)
            if hashes:
                st.dataframe(
                    pd.DataFrame(hashes, columns=["Hash", "Mentions"]),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("No file hashes found.")

        with tab_domain:
            domains = cnt("domains").most_common(100)
            if domains:
                st.dataframe(
                    pd.DataFrame(domains, columns=["Domain", "Mentions"]),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("No domains found.")

        with tab_ttp:
            ttps = cnt("ttps").most_common(100)
            if ttps:
                st.dataframe(
                    pd.DataFrame(ttps, columns=["ATT&CK technique", "Mentions"]),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("No ATT&CK technique IDs found.")

# -----------------------------------------------------------------------------
# Ask archive / RAG
# -----------------------------------------------------------------------------
else:
    panel_title("Ask the archive", "Answers are generated from collected posts, with optional web/NVD/CISA enrichment.")

    top_left, top_mid, top_right = st.columns([2.6, 2, 1])
    with top_left:
        st.markdown(
            '<div class="panel panel-tight"><div class="panel-label">Knowledge scope</div>'
            '<div style="font-size:.88rem;font-weight:750;">Local Telegram archive</div>'
            '<div class="small-muted">Saved posts stay on your machine unless you enable web enrichment.</div></div>',
            unsafe_allow_html=True,
        )
    with top_mid:
        use_web = st.toggle("🌐 Web + NVD + CISA KEV", key="use_web")
    with top_right:
        chat_existing = st.session_state.get("chat", [])
        if st.button("Clear chat", disabled=not chat_existing, use_container_width=True):
            st.session_state["chat"] = []
            st.session_state.pop("pending_question", None)
            st.rerun()

    st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)
    chat = st.session_state.setdefault("chat", [])
    pending_question = st.session_state.pop("pending_question", None)

    if not chat and not pending_question:
        st.markdown(
            '<div class="panel" style="margin-bottom:.75rem;">'
            '<div class="panel-label">Suggested investigations</div>'
            '<div class="suggestion-grid">'
            '<div class="suggestion-card"><div class="suggestion-title">Ransomware</div><div class="small-muted">Which groups were mentioned?</div></div>'
            '<div class="suggestion-card"><div class="suggestion-title">Vulnerabilities</div><div class="small-muted">What new CVEs were discussed?</div></div>'
            '<div class="suggestion-card"><div class="suggestion-title">Critical posts</div><div class="small-muted">Summarize the highest-priority alerts.</div></div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

    def _stop():
        if st.session_state.get("chat"):
            st.session_state["chat"][-1]["stopped"] = True

    def _show(message):
        with st.chat_message(message["role"]):
            st.markdown(
                (message.get("content") or "")
                + ("\n\n*⏹ Stopped*" if message.get("stopped") else "")
            )
            if message.get("web"):
                with st.expander(f"Web sources · {len(message['web'])}"):
                    for n_, w in enumerate(message["web"], 1):
                        st.markdown(
                            f'**[W{n_}]** [{html.escape(w["title"])}]({w["url"]})  \n'
                            f'{html.escape(w["content"][:260])}…'
                        )
            if message.get("sources"):
                with st.expander(f"Archive sources · {len(message['sources'])}"):
                    for s_ in message["sources"]:
                        link = f' · [open source]({s_["link"]})' if s_["link"] else ""
                        st.markdown(
                            f'**[{s_["n"]}]** {html.escape(s_["channel"])} · {s_["date"]} · '
                            f'{html.escape(s_["category"] or "?")} · {html.escape(s_["severity"] or "?")}{link}  \n'
                            f'{html.escape(s_["snippet"])}…'
                        )

    for m in chat:
        _show(m)

    if pending_question:
        history = chat[-6:]
        chat.append({"role": "user", "content": pending_question})
        _show(chat[-1])
        chat.append({"role": "assistant", "content": "", "sources": [], "web": [], "stopped": False})
        with st.chat_message("assistant"):
            st.button("⏹ Stop generating", on_click=_stop, key="stop_btn")
            box = st.empty()
            box.markdown("*Searching the archive and thinking…*")
            from intel.rag import ask_stream
            for kind, val in ask_stream(pending_question, history, web=use_web):
                if kind == "web":
                    chat[-1]["web"] = val
                elif kind == "sources":
                    chat[-1]["sources"] = val
                else:
                    chat[-1]["content"] += val
                    box.markdown(chat[-1]["content"] + " ▌")
        st.rerun()