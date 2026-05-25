"""
app.py — AI Multi-Site Web Scraper | Groq + httpx + BeautifulSoup
100% FREE | No browser-use | No Playwright | Works on WSL/Linux/Windows
"""

import asyncio
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from agent import run_scrape_agent
from extractor import (
    dataframe_to_excel_bytes,
    dataframe_to_json_bytes,
    merge_dataframes,
    records_to_dataframe,
)

# ── Page config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Multi-Site Scraper",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    background-color: #080c0f !important;
    color: #c8ffc8 !important;
    font-family: 'Rajdhani', sans-serif !important;
}
.stApp::before {
    content:"";position:fixed;top:0;left:0;right:0;bottom:0;
    background:repeating-linear-gradient(0deg,transparent,transparent 2px,
    rgba(0,255,65,0.02) 2px,rgba(0,255,65,0.02) 4px);
    pointer-events:none;z-index:9999;
}
.block-container { padding:2rem 3rem !important; max-width:1200px !important; }

.hero-title {
    font-family:'Share Tech Mono',monospace !important;
    font-size:2.6rem;color:#00ff41;letter-spacing:0.08em;
    text-shadow:0 0 20px #00ff4188,0 0 40px #00ff4144;
    text-align:center;margin:0;
}
.hero-sub {
    font-family:'Share Tech Mono',monospace;font-size:0.8rem;
    color:#00aa2a;letter-spacing:0.12em;text-align:center;margin-top:0.4rem;
}
.hero-badge {
    display:inline-block;background:#002b10;border:1px solid #00ff41;
    border-radius:20px;padding:0.2rem 1rem;font-family:'Share Tech Mono',monospace;
    font-size:0.72rem;color:#00ff41;letter-spacing:0.1em;margin-top:0.6rem;
}
.hero-wrap {
    padding:2rem 0 1.5rem;border-bottom:1px solid #00ff4133;
    margin-bottom:2rem;text-align:center;
}
.blink{animation:blink 1.2s step-end infinite;}
@keyframes blink{50%{opacity:0;}}

.lbl {
    font-family:'Share Tech Mono',monospace;font-size:0.68rem;
    color:#00ff41;letter-spacing:0.2em;text-transform:uppercase;
    margin-bottom:0.25rem;opacity:0.7;
}

.stTextInput>div>div>input,
.stTextArea>div>div>textarea {
    background-color:#0d1a12 !important;border:1px solid #00ff4144 !important;
    border-radius:4px !important;color:#c8ffc8 !important;
    font-family:'Share Tech Mono',monospace !important;
    font-size:0.86rem !important;caret-color:#00ff41;
}
.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus {
    border-color:#00ff41 !important;box-shadow:0 0 0 2px #00ff4122 !important;
}

.stRadio>div{flex-direction:row;gap:1.5rem;}
.stRadio label{color:#c8ffc8 !important;font-family:'Rajdhani',sans-serif !important;}

.url-card {
    background:#0a130d;border:1px solid #00ff4133;border-radius:6px;
    padding:0.75rem 1rem;margin-bottom:0.5rem;
    display:flex;align-items:center;gap:0.75rem;
    font-family:'Share Tech Mono',monospace;font-size:0.82rem;color:#c8ffc8;
}
.url-badge {
    background:#002b10;border:1px solid #00ff4166;border-radius:3px;
    color:#00ff41;padding:0.1rem 0.5rem;font-size:0.7rem;
    font-family:'Share Tech Mono',monospace;white-space:nowrap;
}
.url-text{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.status-pending{color:#555;}
.status-running{color:#44bbff;}
.status-done   {color:#00ff41;}
.status-error  {color:#ff4444;}

.prog-wrap {
    background:#0a130d;border:1px solid #00ff4133;border-radius:4px;
    height:8px;margin:0.5rem 0;overflow:hidden;
}
.prog-fill {
    height:100%;background:linear-gradient(90deg,#004d1e,#00ff41);
    transition:width 0.4s ease;border-radius:4px;box-shadow:0 0 8px #00ff4166;
}

.stButton>button {
    background:linear-gradient(135deg,#002b10 0%,#004d1e 100%) !important;
    border:1px solid #00ff41 !important;color:#00ff41 !important;
    font-family:'Share Tech Mono',monospace !important;font-size:0.95rem !important;
    letter-spacing:0.12em !important;padding:0.6rem 2rem !important;
    border-radius:4px !important;text-shadow:0 0 8px #00ff4188;
    box-shadow:0 0 12px #00ff4122;width:100%;transition:all 0.2s;
}
.stButton>button:hover {
    background:linear-gradient(135deg,#004d1e 0%,#00802f 100%) !important;
    box-shadow:0 0 24px #00ff4155 !important;transform:translateY(-1px);
}
.stDownloadButton>button {
    background:#0d1a12 !important;border:1px solid #00ff4166 !important;
    color:#00ff41 !important;font-family:'Share Tech Mono',monospace !important;
    font-size:0.82rem !important;letter-spacing:0.08em !important;
    border-radius:4px !important;width:100%;transition:all 0.2s;
}
.stDownloadButton>button:hover {
    border-color:#00ff41 !important;box-shadow:0 0 12px #00ff4133 !important;
}

.terminal-box {
    background:#050e08;border:1px solid #00ff4133;border-radius:4px;
    padding:0.8rem 1rem;font-family:'Share Tech Mono',monospace;
    font-size:0.76rem;color:#00aa2a;line-height:1.8;
    max-height:200px;overflow-y:auto;
}
.log-ok  {color:#00ff41;}
.log-info{color:#44bbff;}
.log-warn{color:#ff4444;}

.stAlert {
    background-color:#0d1a12 !important;border:1px solid #00ff4133 !important;
    border-radius:4px !important;color:#c8ffc8 !important;
}

[data-testid="metric-container"] {
    background:#0d1a12;border:1px solid #00ff4122;border-radius:6px;padding:0.8rem 1rem;
}
[data-testid="metric-container"] label {
    color:#00aa2a !important;font-family:'Share Tech Mono',monospace !important;
    font-size:0.7rem !important;letter-spacing:0.1em;
}
[data-testid="stMetricValue"] {
    color:#00ff41 !important;font-family:'Share Tech Mono',monospace !important;
    font-size:1.7rem !important;text-shadow:0 0 10px #00ff4166;
}

.stTabs [data-baseweb="tab-list"] {
    background:#050e08 !important;border-bottom:1px solid #00ff4133;
}
.stTabs [data-baseweb="tab"] {
    font-family:'Share Tech Mono',monospace !important;font-size:0.8rem !important;
    color:#006618 !important;letter-spacing:0.1em;
    border-radius:4px 4px 0 0 !important;
}
.stTabs [aria-selected="true"] {
    color:#00ff41 !important;background:#0d1a12 !important;
    border:1px solid #00ff4133 !important;border-bottom:none !important;
}

.stDataFrame{border:1px solid #00ff4122 !important;border-radius:6px;overflow:hidden;}
hr{border-color:#00ff4122 !important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#050e08;}
::-webkit-scrollbar-thumb{background:#00ff4133;border-radius:3px;}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-title">🤖 AI MULTI-SITE SCRAPER<span class="blink">_</span></div>
    <div class="hero-sub">[ GROQ LLAMA 3.3 70B + HTTPX // MULTIPLE SITES → ONE SHEET ]</div>
    <div><span class="hero-badge">⚡ POWERED BY GROQ — 100% FREE</span></div>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────────
if "urls" not in st.session_state:
    st.session_state.urls = [""]
if "merged_df" not in st.session_state:
    st.session_state.merged_df = None
if "per_site_dfs" not in st.session_state:
    st.session_state.per_site_dfs = []
if "logs" not in st.session_state:
    st.session_state.logs = []


def domain_label(url: str) -> str:
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


# ── Layout ────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:

    # Groq API Key
    st.markdown('<div class="lbl">// GROQ API KEY (FREE)</div>', unsafe_allow_html=True)
    api_key = st.text_input(
        label="groq_key", label_visibility="collapsed",
        type="password",
        placeholder="gsk_...",
        key="api_key_input",
    )
    st.markdown(
        "<small style='color:#006618;font-family:Share Tech Mono,monospace;font-size:0.68rem'>"
        "🔑 Get FREE key at <b style='color:#00ff41'>console.groq.com</b> — no billing needed!</small>",
        unsafe_allow_html=True,
    )

    # URLs
    st.markdown('<div class="lbl" style="margin-top:1.2rem">// TARGET WEBSITES</div>', unsafe_allow_html=True)
    st.markdown(
        "<small style='color:#006618;font-family:Share Tech Mono,monospace;font-size:0.68rem'>"
        "Add as many URLs as you want — all scraped and merged into one sheet.</small>",
        unsafe_allow_html=True,
    )

    urls_to_remove = []
    for i, url_val in enumerate(st.session_state.urls):
        c1, c2 = st.columns([11, 1])
        with c1:
            st.session_state.urls[i] = st.text_input(
                label=f"url_{i}", label_visibility="collapsed",
                placeholder=f"https://example-site-{i+1}.com",
                value=url_val,
                key=f"url_field_{i}",
            )
        with c2:
            if len(st.session_state.urls) > 1:
                if st.button("✕", key=f"remove_{i}"):
                    urls_to_remove.append(i)

    for idx in reversed(urls_to_remove):
        st.session_state.urls.pop(idx)
        st.rerun()

    add_col, _ = st.columns([1, 3])
    with add_col:
        if st.button("＋  Add URL", key="add_url"):
            st.session_state.urls.append("")
            st.rerun()

    # Query
    st.markdown('<div class="lbl" style="margin-top:1.2rem">// EXTRACTION QUERY</div>', unsafe_allow_html=True)
    query = st.text_area(
        label="query", label_visibility="collapsed",
        placeholder="Extract the title, price, and rating of every product on the page",
        height=110,
        key="query_input",
    )

    # Output format
    st.markdown('<div class="lbl" style="margin-top:1rem">// OUTPUT FORMAT</div>', unsafe_allow_html=True)
    output_format = st.radio(
        label="fmt", label_visibility="collapsed",
        options=["JSON", "Excel (.xlsx)"],
        horizontal=True,
    )

with col_right:

    st.markdown('<div class="lbl">// HOW IT WORKS</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="terminal-box">
            <span class="log-info">1.</span> Get FREE Groq key → console.groq.com<br>
            <span class="log-info">2.</span> Paste key (starts with gsk_...)<br>
            <span class="log-info">3.</span> Add all URLs you want to scrape<br>
            <span class="log-info">4.</span> Describe what to extract in plain English<br>
            <span class="log-ok">5.</span> All results merged into ONE sheet ✓<br>
            <span class="log-ok">   + separate tab per site in Excel ✓</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="lbl" style="margin-top:1.2rem">// EXAMPLE QUERIES</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="terminal-box">
            <span class="log-info">›</span> books.toscrape.com<br>
            <span class="log-ok">  Extract title, price, rating of first 10 books</span><br><br>
            <span class="log-info">›</span> quotes.toscrape.com<br>
            <span class="log-ok">  Extract all quotes, authors, and tags</span><br><br>
            <span class="log-info">›</span> news.ycombinator.com<br>
            <span class="log-ok">  Extract top 20 post titles and URLs</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="lbl" style="margin-top:1.2rem">// EXCEL OUTPUT</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style='font-family:Share Tech Mono,monospace;font-size:0.7rem;
                    color:#006618;line-height:2;border:1px solid #00ff4122;
                    border-radius:4px;padding:0.8rem;background:#050e08'>
        📋 Sheet 1 → <span style="color:#00ff41">All Results</span> (merged)<br>
        📋 Sheet 2 → Site 1 domain<br>
        📋 Sheet 3 → Site 2 domain<br>
        📋 Sheet N → ...<br><br>
        Each row tagged with <span style="color:#00ff41">source_url</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="lbl" style="margin-top:1.2rem">// GROQ FREE LIMITS</div>', unsafe_allow_html=True)
    st.markdown("""
        <div style='font-family:Share Tech Mono,monospace;font-size:0.7rem;
                    color:#006618;line-height:2;border:1px solid #00ff4122;
                    border-radius:4px;padding:0.8rem;background:#050e08'>
        ⚡ Model  : Llama 3.3 70B<br>
        📊 Speed  : 300+ tokens/sec<br>
        🔁 Limit  : 30 req/min<br>
        💰 Cost   : <span style="color:#00ff41">$0.00 forever</span><br>
        🔑 Signup : console.groq.com
        </div>
    """, unsafe_allow_html=True)

# ── Launch button ─────────────────────────────────────────────────────────────────
st.markdown("")
btn_col, _ = st.columns([2, 3])
with btn_col:
    start = st.button("🚀  START SCRAPING ALL SITES", key="run_btn")

# ── Run ───────────────────────────────────────────────────────────────────────────
if start:
    valid_urls = [u.strip() for u in st.session_state.urls if u.strip()]
    errors = []
    if not api_key.strip():
        errors.append("🔑 Groq API key required — get it free at console.groq.com")
    if not valid_urls:
        errors.append("🌐 Add at least one URL.")
    if not query.strip():
        errors.append("🗣️ Describe what to extract.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        st.session_state.merged_df = None
        st.session_state.per_site_dfs = []
        st.session_state.logs = []

        st.markdown("---")
        st.markdown('<div class="lbl">// SCRAPING PROGRESS</div>', unsafe_allow_html=True)

        status_placeholders = []
        for i, u in enumerate(valid_urls):
            ph = st.empty()
            ph.markdown(
                f'<div class="url-card">'
                f'<span class="url-badge">#{i+1}</span>'
                f'<span class="url-text">{u}</span>'
                f'<span class="status-pending">⏳ PENDING</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            status_placeholders.append(ph)

        progress_ph = st.empty()
        log_ph = st.empty()

        def log(msg, kind="ok"):
            css = {"ok": "log-ok", "info": "log-info", "warn": "log-warn"}.get(kind, "log-ok")
            st.session_state.logs.append(f'<span class="{css}">› {msg}</span>')
            log_ph.markdown(
                '<div class="terminal-box">' + "<br>".join(st.session_state.logs[-14:]) + "</div>",
                unsafe_allow_html=True,
            )

        def update_progress(done, total):
            pct = int(done / total * 100)
            progress_ph.markdown(
                f'<div style="font-family:Share Tech Mono,monospace;font-size:0.7rem;'
                f'color:#00aa2a;margin-bottom:0.2rem">{done}/{total} sites complete — {pct}%</div>'
                f'<div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div>',
                unsafe_allow_html=True,
            )

        all_dfs = []
        per_site_dfs = []
        total = len(valid_urls)

        for i, url in enumerate(valid_urls):
            label = domain_label(url)
            status_placeholders[i].markdown(
                f'<div class="url-card">'
                f'<span class="url-badge">#{i+1}</span>'
                f'<span class="url-text">{url}</span>'
                f'<span class="status-running">⚡ SCRAPING...</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            log(f"[{i+1}/{total}] Starting → {label}", "info")

            try:
                records = asyncio.run(run_scrape_agent(url, query, api_key.strip()))

                is_error = (
                    len(records) == 1
                    and ("error" in records[0] or "raw_output" in records[0])
                )

                df = records_to_dataframe(records, source_url=url)
                all_dfs.append(df)
                per_site_dfs.append((label, df))

                if is_error:
                    status_placeholders[i].markdown(
                        f'<div class="url-card">'
                        f'<span class="url-badge">#{i+1}</span>'
                        f'<span class="url-text">{url}</span>'
                        f'<span class="status-error">⚠ {records[0].get("error","No data")}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    log(f"[{i+1}/{total}] ⚠ {label} — {records[0].get('error','no data')}", "warn")
                else:
                    status_placeholders[i].markdown(
                        f'<div class="url-card">'
                        f'<span class="url-badge">#{i+1}</span>'
                        f'<span class="url-text">{url}</span>'
                        f'<span class="status-done">✓ {len(records)} records</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    log(f"[{i+1}/{total}] ✓ {label} — {len(records)} records extracted", "ok")

            except Exception as exc:
                status_placeholders[i].markdown(
                    f'<div class="url-card">'
                    f'<span class="url-badge">#{i+1}</span>'
                    f'<span class="url-text">{url}</span>'
                    f'<span class="status-error">✗ ERROR</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                log(f"[{i+1}/{total}] ✗ {label} — {exc}", "warn")

            update_progress(i + 1, total)

        if all_dfs:
            merged = merge_dataframes(all_dfs)
            st.session_state.merged_df = merged
            st.session_state.per_site_dfs = per_site_dfs
            log(f"Merge complete — {len(merged)} total records from {len(all_dfs)} site(s) ✓", "ok")
        else:
            log("No data extracted from any site.", "warn")
            st.error("No data could be extracted. Check your URLs and query.")

# ── Results ───────────────────────────────────────────────────────────────────────
if st.session_state.merged_df is not None:
    merged_df: pd.DataFrame = st.session_state.merged_df
    per_site: list = st.session_state.per_site_dfs

    st.markdown("---")
    st.markdown('<div class="lbl">// RESULTS</div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TOTAL RECORDS", len(merged_df))
    m2.metric("SITES SCRAPED", len(per_site))
    m3.metric("COLUMNS", len(merged_df.columns))
    m4.metric("FORMAT", output_format.split()[0])

    tab_labels = ["📋 All Results"] + [f"🌐 {label[:20]}" for label, _ in per_site]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        st.dataframe(merged_df, use_container_width=True, height=360)

    for idx, (label, site_df) in enumerate(per_site):
        with tabs[idx + 1]:
            st.markdown(
                f"<small style='font-family:Share Tech Mono,monospace;color:#006618'>"
                f"Source: {label} — {len(site_df)} records</small>",
                unsafe_allow_html=True,
            )
            st.dataframe(site_df, use_container_width=True, height=300)

    st.markdown('<div class="lbl" style="margin-top:1rem">// DOWNLOAD</div>', unsafe_allow_html=True)
    dl1, dl2 = st.columns(2)

    with dl1:
        st.download_button(
            label="⬇️  Download JSON (merged)",
            data=dataframe_to_json_bytes(merged_df),
            file_name="scraped_all_sites.json",
            mime="application/json",
            use_container_width=True,
        )
    with dl2:
        excel_bytes = dataframe_to_excel_bytes(merged_df, per_site_dfs=per_site)
        st.download_button(
            label="⬇️  Download Excel (all sheets)",
            data=excel_bytes,
            file_name="scraped_all_sites.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.markdown(
        "<small style='font-family:Share Tech Mono,monospace;color:#006618;font-size:0.68rem'>"
        "💡 Excel: Sheet 1 = All Results merged | Per-site sheets with individual data</small>",
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;margin-top:3rem;font-family:Share Tech Mono,monospace;
            font-size:0.65rem;color:#003d14;letter-spacing:0.15em'>
    AI MULTI-SITE SCRAPER // GROQ LLAMA 3.3 70B // 100% FREE
</div>
""", unsafe_allow_html=True)
