"""
app_streamlit_v4.py  —  SmartValue Scanner V4
Design premium dark mode — palette vert acidulé
"""

from __future__ import annotations

import uuid
import pandas as pd
import requests
import streamlit as st

from scanner_core import (
    SmartValueScanner,
    DEFAULT_UNIVERSE,
    SOFT_DISCLAIMER,
)

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="SmartValue Scanner",
    page_icon="🔎",
    layout="wide",
)

FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform"

# =====================================================
# CSS PREMIUM
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #0A0B0E !important;
    color: #F0F2F5 !important;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

.main .block-container {
    padding: 2rem 3rem 4rem !important;
    max-width: 1200px !important;
}

h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    color: #F0F2F5 !important;
}
h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    color: #F0F2F5 !important;
    letter-spacing: -0.02em !important;
}
h2 { font-size: 1.3rem !important; }
h3 { font-size: 1.1rem !important; }

.stButton > button {
    background: #C8F135 !important;
    color: #0A0B0E !important;
    border: none !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    border-radius: 0 !important;
    padding: 0.6rem 1.5rem !important;
}
.stButton > button:hover {
    background: #8BDE0F !important;
    color: #0A0B0E !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #F0F2F5 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: rgba(255,255,255,0.3) !important;
    background: transparent !important;
    color: #F0F2F5 !important;
}

.stSlider > div > div > div > div { background: #C8F135 !important; }
.stSlider [data-testid="stThumbValue"] {
    color: #C8F135 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #7A8090 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    border: none !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #C8F135 !important;
    border-bottom: 2px solid #C8F135 !important;
}

.streamlit-expanderHeader {
    background: #111318 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 0 !important;
    font-size: 0.88rem !important;
    color: #B0B5BF !important;
}
.streamlit-expanderContent {
    background: #0E0F13 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-top: none !important;
}

.stAlert {
    background: #111318 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 0 !important;
    color: #B0B5BF !important;
    font-size: 0.85rem !important;
}
[data-testid="stInfoBox"] {
    background: rgba(200,241,53,0.05) !important;
    border-left: 2px solid #C8F135 !important;
    border-radius: 0 !important;
}
[data-testid="stSuccessBox"] {
    background: rgba(200,241,53,0.06) !important;
    border-left: 2px solid #C8F135 !important;
    border-radius: 0 !important;
    color: #C8F135 !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.3rem !important;
    font-weight: 700 !important;
    color: #F0F2F5 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    color: #7A8090 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

.stTextInput > div > div > input {
    background: #111318 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 0 !important;
    color: #F0F2F5 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #C8F135 !important;
    box-shadow: none !important;
}

.stProgress > div > div > div { background: #C8F135 !important; }
.stProgress > div > div { background: rgba(255,255,255,0.05) !important; }

hr { border-color: rgba(255,255,255,0.07) !important; }

.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #F0F2F5 !important;
    font-family: 'Syne', sans-serif !important;
    border-radius: 0 !important;
}
.stDownloadButton > button:hover {
    border-color: #C8F135 !important;
    color: #C8F135 !important;
    background: transparent !important;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: #7A8090 !important;
    font-size: 0.8rem !important;
}

/* CUSTOM CLASSES */
.section-label {
    font-size: 0.7rem;
    color: #C8F135;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 0.75rem;
    font-family: 'Syne', sans-serif;
}
.app-header {
    border-bottom: 1px solid rgba(255,255,255,0.07);
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
}
.app-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #F0F2F5;
}
.app-title span { color: #C8F135; }
.app-subtitle { font-size: 0.82rem; color: #7A8090; margin-top: 0.3rem; }

.result-card {
    background: #111318;
    border: 1px solid rgba(255,255,255,0.07);
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    transition: border-color 0.2s;
}
.result-card:hover { border-color: rgba(200,241,53,0.2); }
.card-ticker {
    font-family: 'Syne', sans-serif;
    font-size: 1.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #F0F2F5;
}
.card-score {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: #C8F135;
    letter-spacing: -0.03em;
    line-height: 1;
}
.card-tag {
    display: inline-block;
    background: rgba(200,241,53,0.08);
    border: 1px solid rgba(200,241,53,0.25);
    color: #C8F135;
    font-family: 'Syne', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    padding: 0.2rem 0.6rem;
    margin-right: 0.3rem;
    margin-bottom: 0.3rem;
}
.card-why {
    font-size: 0.85rem;
    color: #B0B5BF;
    line-height: 1.6;
    border-left: 2px solid rgba(200,241,53,0.3);
    padding-left: 0.75rem;
    margin: 0.75rem 0;
}
.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    margin-top: 0.75rem;
}
.metric-item {
    background: #0A0B0E;
    border: 1px solid rgba(255,255,255,0.05);
    padding: 0.5rem 0.75rem;
}
.metric-label {
    font-size: 0.65rem;
    color: #7A8090;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.15rem;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: #F0F2F5;
}
.stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.07);
    margin: 1.5rem 0 2rem;
}
.stat-item { background: #0A0B0E; padding: 1rem 1.5rem; text-align: center; }
.stat-num {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #C8F135;
    letter-spacing: -0.03em;
}
.stat-lbl {
    font-size: 0.7rem;
    color: #7A8090;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-top: 0.2rem;
}
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #7A8090;
    border: 1px dashed rgba(255,255,255,0.07);
    margin-top: 1rem;
}
.empty-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: #B0B5BF;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# GA4
# =====================================================
def _ga_enabled() -> bool:
    return "GA_ID" in st.secrets and "GA_SECRET" in st.secrets

def ga_event(name: str, params: dict = None) -> None:
    if not _ga_enabled():
        return
    if "ga_client_id" not in st.session_state:
        st.session_state["ga_client_id"] = str(uuid.uuid4())
    try:
        requests.post(
            f"https://www.google-analytics.com/mp/collect"
            f"?measurement_id={st.secrets['GA_ID']}&api_secret={st.secrets['GA_SECRET']}",
            json={"client_id": st.session_state["ga_client_id"], "events": [{"name": name, "params": params or {}}]},
            timeout=2,
        )
    except Exception:
        pass

if "ga_open_sent" not in st.session_state:
    ga_event("app_open_v4")
    st.session_state["ga_open_sent"] = True


# =====================================================
# API KEY
# =====================================================
def get_api_key() -> str:
    return st.secrets.get("FMP_API_KEY", "")

API_KEY = get_api_key()


# =====================================================
# STATE
# =====================================================
def init_state():
    defaults = {
        "min_score": 35,
        "min_conf": 50,
        "top_n": 15,
        "sectors_selected": {k: True for k in DEFAULT_UNIVERSE.keys()},
        "scan_results": [],
        "search_result": None,
        "recommended_applied": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def set_recommended():
    st.session_state["min_score"] = 45
    st.session_state["min_conf"] = 70
    st.session_state["recommended_applied"] = True

def build_universe() -> dict:
    return {k: v for k, v in DEFAULT_UNIVERSE.items() if st.session_state["sectors_selected"].get(k, True)}

init_state()


# =====================================================
# HELPERS UI
# =====================================================
def render_score_bars(r: dict):
    blocs = {
        "Valorisation": r.get("Bloc valuation", 0),
        "Rentabilité": r.get("Bloc rentabilité", 0),
        "Santé fin.": r.get("Bloc santé", 0),
        "Croissance": r.get("Bloc croissance", 0),
        "Dividende": r.get("Bloc dividende", 0),
    }
    bars_html = '<div style="margin-top:1rem;">'
    for label, val in blocs.items():
        pct = min(int(val), 100)
        bars_html += f"""
        <div style="margin-bottom:7px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                <span style="font-size:0.68rem;color:#7A8090;text-transform:uppercase;letter-spacing:0.06em;font-family:'DM Sans',sans-serif;">{label}</span>
                <span style="font-family:'Syne',sans-serif;font-size:0.7rem;font-weight:700;color:#C8F135;">{val:.0f}</span>
            </div>
            <div style="background:rgba(255,255,255,0.05);height:2px;width:100%;border-radius:0;">
                <div style="background:#C8F135;height:2px;width:{pct}%;"></div>
            </div>
        </div>"""
    bars_html += "</div>"
    st.markdown(bars_html, unsafe_allow_html=True)


def render_tags(tags_str: str) -> str:
    if not tags_str:
        return ""
    return "".join(
        f'<span class="card-tag">{t.strip()}</span>'
        for t in tags_str.split(",") if t.strip()
    )


def fmt(v, suffix="") -> str:
    return f"{v}{suffix}" if v is not None else "—"


def display_card(r: dict):
    score = r.get("Score", 0)
    conf = r.get("Confiance %", 0)

    st.markdown(f"""
    <div class="result-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.75rem;">
            <div style="flex:1;">
                <div class="card-ticker">
                    {r.get('Score badge','')} {r.get('Ticker','')}
                    <span style="font-size:0.95rem;font-weight:400;color:#7A8090;"> — {r.get('Société','')}</span>
                </div>
                <div style="font-size:0.78rem;color:#7A8090;margin-top:0.3rem;">
                    🌍 {r.get('Pays','')} · {r.get('Bourse','')} · {r.get('Secteur','')}
                </div>
                <div style="margin-top:0.6rem;">{render_tags(r.get('Tags',''))}</div>
            </div>
            <div style="text-align:right;margin-left:1.5rem;flex-shrink:0;">
                <div class="card-score">{score}</div>
                <div style="font-size:0.65rem;color:#7A8090;text-transform:uppercase;letter-spacing:0.08em;">/100</div>
                <div style="font-size:0.75rem;color:#7A8090;margin-top:0.3rem;">{r.get('Confiance badge','')} {conf}%</div>
            </div>
        </div>
        <div class="card-why">{r.get('Résumé','')} — {r.get('Pourquoi','')}</div>
        <div class="metric-grid">
            <div class="metric-item"><div class="metric-label">Prix</div><div class="metric-value">{r.get('Prix','—')} {r.get('Devise','')}</div></div>
            <div class="metric-item"><div class="metric-label">PER</div><div class="metric-value">{fmt(r.get('PER'))}</div></div>
            <div class="metric-item"><div class="metric-label">P/B</div><div class="metric-value">{fmt(r.get('P/B'))}</div></div>
            <div class="metric-item"><div class="metric-label">ROE</div><div class="metric-value">{fmt(r.get('ROE %'), '%')}</div></div>
            <div class="metric-item"><div class="metric-label">Marge</div><div class="metric-value">{fmt(r.get('Marge %'), '%')}</div></div>
            <div class="metric-item"><div class="metric-label">EV/EBITDA</div><div class="metric-value">{fmt(r.get('EV/EBITDA'))}</div></div>
            <div class="metric-item"><div class="metric-label">Dette/Eq.</div><div class="metric-value">{fmt(r.get('Dette/Equity'))}</div></div>
            <div class="metric-item"><div class="metric-label">Croissance</div><div class="metric-value">{fmt(r.get('Croissance CA %'), '%')}</div></div>
            <div class="metric-item"><div class="metric-label">Dividende</div><div class="metric-value">{r.get('Div affichage','—')}%</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_score_bars(r)


# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="app-header">
    <div class="app-title">Smart<span>Value</span> Scanner</div>
    <div class="app-subtitle">Données : Financial Modeling Prep · Univers mondial · Analyse fondamentale</div>
</div>
""", unsafe_allow_html=True)

with st.expander("📘 Comment lire les résultats ?"):
    st.markdown("""
**Score (0–100)** — Synthèse de 5 blocs : valorisation, rentabilité, santé financière, croissance, dividende. Ce n'est **pas** un signal d'achat.

**Confiance (0–92%)** — Complétude et cohérence des données. En dessous de 60% → vérifier manuellement.

**Tags** — VALUE, QUALITÉ, SÛR, CROISSANCE, DIVIDENDE — résument le profil de l'action.
    """)

with st.expander("📚 Lexique"):
    st.markdown("""
- **PER** : Prix / Bénéfices · **P/B** : Prix / Valeur comptable · **EV/EBITDA** : Valorisation / profit opérationnel
- **ROE %** : Rentabilité des capitaux propres · **Marge %** : Bénéfice net / CA
- **Dette/Equity** : Endettement relatif · **Croissance CA %** : Évolution du chiffre d'affaires · **Div %** : Rendement dividende
    """)

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# =====================================================
# TABS
# =====================================================
tab_scan, tab_search = st.tabs(["🌍  Scanner l'univers", "🔍  Recherche par ticker"])

# ─────────────────────────────────────────────────────
# TAB 1 — SCAN
# ─────────────────────────────────────────────────────
with tab_scan:
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Réglages</div>', unsafe_allow_html=True)

    col_rec, _ = st.columns([1, 3])
    with col_rec:
        st.button("✨ Réglages recommandés", on_click=set_recommended, key="btn_recommended")

    if st.session_state.get("recommended_applied"):
        st.toast("Réglages recommandés appliqués ✅")
        st.session_state["recommended_applied"] = False

    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.slider("Score minimum", 0, 100, key="min_score")
    with c2:
        st.slider("Confiance minimum (%)", 0, 100, step=5, key="min_conf")
    with c3:
        st.slider("Nombre de résultats", 5, 50, key="top_n")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Secteurs</div>', unsafe_allow_html=True)

    b1, b2, _ = st.columns([1, 1, 4])
    with b1:
        if st.button("Tout sélectionner", key="btn_all"):
            for k in DEFAULT_UNIVERSE:
                st.session_state["sectors_selected"][k] = True
    with b2:
        if st.button("Tout déselectionner", key="btn_none", type="secondary"):
            for k in DEFAULT_UNIVERSE:
                st.session_state["sectors_selected"][k] = False

    sector_names = list(DEFAULT_UNIVERSE.keys())
    grid = st.columns(3, gap="large")
    for i, sector in enumerate(sector_names):
        with grid[i % 3]:
            st.session_state["sectors_selected"][sector] = st.checkbox(
                sector,
                value=st.session_state["sectors_selected"].get(sector, True),
                key=f"sector_{sector}",
            )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        run_scan = st.button("🚀 Lancer le scan", use_container_width=True, type="primary", key="btn_scan")

    if run_scan:
        if not API_KEY:
            st.error("Clé API FMP manquante. Ajoute FMP_API_KEY dans les secrets Streamlit.")
            st.stop()
        universe = build_universe()
        if not universe:
            st.error("Sélectionne au moins un secteur.")
            st.stop()

        ga_event("scan_v4", {"sectors": len(universe)})
        scanner = SmartValueScanner(api_key=API_KEY, universe=universe)
        progress = st.progress(0, text="Démarrage de l'analyse...")

        def update_progress(pct, msg):
            progress.progress(pct, text=msg)

        results = scanner.scan(
            min_score=st.session_state["min_score"],
            min_confidence=st.session_state["min_conf"],
            progress_callback=update_progress,
        )
        progress.progress(1.0, text="Terminé ✅")
        st.session_state["scan_results"] = results
        ga_event("scan_done_v4", {"count": len(results)})

    results = st.session_state.get("scan_results", [])

    if results:
        df = pd.DataFrame(results)
        top_n = st.session_state["top_n"]
        st.markdown(f"""
        <div class="stats-row">
            <div class="stat-item"><div class="stat-num">{len(results)}</div><div class="stat-lbl">Opportunités</div></div>
            <div class="stat-item"><div class="stat-num">{df['Score'].mean():.1f}</div><div class="stat-lbl">Score moyen</div></div>
            <div class="stat-item"><div class="stat-num">{df['Score'].max():.1f}</div><div class="stat-lbl">Meilleur score</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label">Résultats</div>', unsafe_allow_html=True)
        for r in results[:top_n]:
            display_card(r)

        with st.expander("📩 Aperçu email (Top 5)"):
            sc = SmartValueScanner(api_key=API_KEY, universe=build_universe())
            st.code(sc.to_email_markdown(results, top_n=5), language="markdown")

        with st.expander("📊 Tableau comparatif"):
            cols = ["Score","Confiance %","Ticker","Société","Secteur","Pays","Prix","Devise",
                    "PER","P/B","EV/EBITDA","ROE %","Marge %","Dette/Equity","Div %","Croissance CA %","Tags"]
            safe_cols = [c for c in cols if c in df.columns]
            st.dataframe(df[safe_cols].head(top_n), use_container_width=True)

        st.download_button(
            "⬇️ Télécharger les résultats (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="smartvalue_v4.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Feedback</div>', unsafe_allow_html=True)
        st.link_button("📝 Donner mon avis (2 min)", FEEDBACK_URL, use_container_width=True)

    elif not run_scan:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-title">Prêt à analyser</div>
            <div style="font-size:0.85rem;">Configure tes réglages et lance le scan.</div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# TAB 2 — RECHERCHE LIBRE
# ─────────────────────────────────────────────────────
with tab_search:
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Analyser une action</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#7A8090;font-size:0.85rem;margin-bottom:1rem;'>"
        "Ticker exact — ex: AAPL · MC.PA · ASML · NESN.SW · 005930.KS"
        "</p>",
        unsafe_allow_html=True
    )

    s1, s2 = st.columns([4, 1])
    with s1:
        ticker_input = st.text_input(
            "Ticker",
            placeholder="AAPL · MC.PA · NESN.SW · 9988.HK",
            label_visibility="collapsed",
            key="ticker_search",
        ).strip().upper()
    with s2:
        analyze_btn = st.button("Analyser →", use_container_width=True, type="primary", key="btn_analyze")

    if analyze_btn and ticker_input:
        if not API_KEY:
            st.error("Clé API FMP manquante.")
            st.stop()
        ga_event("search_v4", {"ticker": ticker_input})
        with st.spinner(f"Récupération des données pour {ticker_input}..."):
            scanner = SmartValueScanner(api_key=API_KEY)
            result = scanner.scan_ticker(ticker_input)
        if result:
            st.session_state["search_result"] = result
        else:
            st.warning(f"Aucune donnée trouvée pour **{ticker_input}**. Vérifiez le ticker.")
            st.session_state["search_result"] = None

    search_result = st.session_state.get("search_result")
    if search_result:
        st.markdown(
            f'<div class="section-label" style="margin-top:1.5rem;">Résultat — {search_result["Ticker"]}</div>',
            unsafe_allow_html=True
        )
        display_card(search_result)
    elif not analyze_btn:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-title">Recherche libre</div>
            <div style="font-size:0.85rem;">Entrez n'importe quel ticker mondial et analysez-le instantanément.</div>
        </div>
        """, unsafe_allow_html=True)


# =====================================================
# FOOTER
# =====================================================
st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
st.markdown(f"""
<div style="border-top:1px solid rgba(255,255,255,0.07);padding-top:1.5rem;font-size:0.75rem;color:#7A8090;line-height:1.7;">
{SOFT_DISCLAIMER}
</div>
""", unsafe_allow_html=True)
