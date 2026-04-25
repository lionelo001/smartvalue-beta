"""
app_streamlit_v4.py  —  SmartValue Scanner V4
Interface Streamlit complète :
  - Recherche libre par ticker
  - Scan univers mondial par secteurs
  - Visualisation des 5 blocs de score
  - Source : FMP (fiable, officiel)
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
    page_title="SmartValue Scanner V4",
    page_icon="🔎",
    layout="wide",
)

FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform"

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
    if "FMP_API_KEY" in st.secrets:
        return st.secrets["FMP_API_KEY"]
    return ""

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
    chosen = {k: v for k, v in DEFAULT_UNIVERSE.items() if st.session_state["sectors_selected"].get(k, True)}
    return chosen

init_state()

# =====================================================
# HELPERS UI
# =====================================================
def display_score_bars(r: dict):
    """Affiche les 5 blocs de score sous forme de barres."""
    blocs = {
        "💰 Valorisation": r.get("Bloc valuation", 0),
        "📈 Rentabilité": r.get("Bloc rentabilité", 0),
        "🏦 Santé financière": r.get("Bloc santé", 0),
        "🚀 Croissance": r.get("Bloc croissance", 0),
        "💸 Dividende": r.get("Bloc dividende", 0),
    }
    for label, val in blocs.items():
        col_label, col_bar = st.columns([2, 3])
        with col_label:
            st.caption(label)
        with col_bar:
            st.progress(int(min(val, 100)) / 100, text=f"{val:.0f}/100")


def display_card(r: dict):
    """Affiche une carte résultat complète."""
    score = r.get("Score", 0)
    conf = r.get("Confiance %", 0)

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            st.markdown(f"### {r.get('Score badge','')} {r.get('Ticker','')} — {r.get('Société','')}")
            st.caption(f"🌍 {r.get('Pays','')} · {r.get('Bourse','')} · {r.get('Secteur','')}")
            st.write(f"**Résumé :** {r.get('Résumé','')}")
            st.write(f"**Pourquoi :** {r.get('Pourquoi','')}")
            st.write(f"**Tags :** {r.get('Tags','')}")

        with col2:
            st.metric("Score global", f"{score}/100")
            st.metric("Confiance données", f"{r.get('Confiance badge','')} {conf}%")
            st.write(f"**Prix :** {r.get('Prix','—')} {r.get('Devise','')}")
            per = r.get("PER")
            st.write(f"**PER :** {per if per else '—'}")
            roe = r.get("ROE %")
            st.write(f"**ROE :** {str(roe)+'%' if roe else '—'}")
            div = r.get("Div affichage", "—")
            st.write(f"**Dividende :** {div}%")

        with col3:
            st.markdown("**Détail du score**")
            display_score_bars(r)

        pb = r.get("P/B")
        ev = r.get("EV/EBITDA")
        marge = r.get("Marge %")
        dte = r.get("Dette/Equity")
        rg = r.get("Croissance CA %")

        extra_cols = st.columns(5)
        with extra_cols[0]: st.metric("P/B", pb if pb else "—")
        with extra_cols[1]: st.metric("EV/EBITDA", ev if ev else "—")
        with extra_cols[2]: st.metric("Marge %", f"{marge}%" if marge else "—")
        with extra_cols[3]: st.metric("Dette/Eq.", dte if dte else "—")
        with extra_cols[4]: st.metric("Croissance CA", f"{rg}%" if rg else "—")


# =====================================================
# HEADER
# =====================================================
st.title("🔎 SmartValue Scanner V4")
st.caption("Données : Financial Modeling Prep (FMP) · Univers mondial · Analyse fondamentale")

st.info(
    "🧪 Version BÊTA. Outil d'aide à la réflexion pour investisseurs long terme. "
    "Vos retours sont précieux 🙏"
)

# =====================================================
# AIDE + LEXIQUE
# =====================================================
with st.expander("📘 Comment lire les résultats ?"):
    st.markdown("""
**Score (0–100)** — Synthèse de 5 blocs : valorisation, rentabilité, santé financière, croissance, dividende. Ce n'est **pas** un signal d'achat.

**Confiance (0–92%)** — Complétude et cohérence des données. En dessous de 60%, vérifier manuellement.

**Tags** — VALUE, QUALITÉ, SÛR, CROISSANCE, DIVIDENDE, ACTIFS — résument le profil de l'action.

**Important** — Ces résultats sont indicatifs. Complétez toujours avec vos propres recherches.
    """)

with st.expander("📚 Lexique"):
    st.markdown("""
- **PER** : Prix / Bénéfices. Bas = potentiellement sous-évalué.
- **P/B** : Prix / Valeur comptable. < 1 = sous valeur d'actifs.
- **EV/EBITDA** : Valorisation totale / profit opérationnel.
- **ROE %** : Rentabilité des capitaux propres.
- **Marge %** : Bénéfice net / Chiffre d'affaires.
- **Dette/Equity** : Endettement relatif aux capitaux propres.
- **Croissance CA %** : Évolution du chiffre d'affaires.
- **Div %** : Rendement du dividende annuel.
    """)

st.divider()

# =====================================================
# TABS : SCAN UNIVERS | RECHERCHE LIBRE
# =====================================================
tab_scan, tab_search = st.tabs(["🌍 Scanner l'univers", "🔍 Recherche par ticker"])

# ─────────────────────────────────────────────────────
# TAB 1 : SCAN UNIVERS
# ─────────────────────────────────────────────────────
with tab_scan:
    st.subheader("⚙️ Réglages")

    col_h1, col_h2 = st.columns([4, 1])
    with col_h2:
        st.button("✨ Réglages recommandés", on_click=set_recommended, use_container_width=True)

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

    st.markdown("### 🧩 Secteurs")

    # Boutons tout sélectionner / tout déselectionner
    btn_col1, btn_col2, _ = st.columns([1, 1, 4])
    with btn_col1:
        if st.button("✅ Tout sélectionner"):
            for k in DEFAULT_UNIVERSE:
                st.session_state["sectors_selected"][k] = True
    with btn_col2:
        if st.button("❌ Tout déselectionner"):
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

    st.divider()

    _, scan_mid, _ = st.columns([1, 1, 1])
    with scan_mid:
        run_scan = st.button("🚀 Lancer le scan", use_container_width=True, type="primary")

    if run_scan:
        if not API_KEY:
            st.error("Clé API FMP manquante. Ajoute FMP_API_KEY dans tes secrets Streamlit.")
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

        progress.progress(1.0, text="Analyse terminée ✅")
        st.session_state["scan_results"] = results
        ga_event("scan_done_v4", {"count": len(results)})

    # Résultats scan
    results = st.session_state.get("scan_results", [])

    if results:
        st.subheader("📊 Résultats")
        df = pd.DataFrame(results)

        st.success(
            f"**{len(results)} opportunités trouvées** · "
            f"Score moyen : {df['Score'].mean():.1f}/100 · "
            f"Meilleur : {df['Score'].max():.1f}/100"
        )

        top_n = st.session_state["top_n"]

        for r in results[:top_n]:
            display_card(r)

        # Email preview
        with st.expander("📩 Aperçu email hebdo (Top 5)"):
            scanner_email = SmartValueScanner(api_key=API_KEY, universe=build_universe())
            st.code(scanner_email.to_email_markdown(results, top_n=5), language="markdown")

        # Tableau
        with st.expander("📊 Tableau comparatif complet"):
            cols = [
                "Score", "Confiance %", "Ticker", "Société", "Secteur", "Pays",
                "Prix", "Devise", "PER", "P/B", "EV/EBITDA", "ROE %", "Marge %",
                "Dette/Equity", "Div %", "Croissance CA %", "Tags", "Résumé",
            ]
            safe_cols = [c for c in cols if c in df.columns]
            st.dataframe(df[safe_cols].head(top_n), use_container_width=True)

        # Export CSV
        st.download_button(
            "⬇️ Télécharger les résultats (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="smartvalue_v4_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.divider()
        st.markdown("### 💬 Feedback")
        st.write("Ton avis aide à améliorer SmartValue 🙏")
        st.link_button("📝 Donner mon avis (2 min)", FEEDBACK_URL, use_container_width=True)

    elif not run_scan:
        st.info("Configure tes réglages et lance le scan pour voir les résultats.")

# ─────────────────────────────────────────────────────
# TAB 2 : RECHERCHE LIBRE
# ─────────────────────────────────────────────────────
with tab_search:
    st.subheader("🔍 Analyser une action par ticker")
    st.caption("Entrez le ticker exact (ex: AAPL, MC.PA, ASML, LVMH.PA, 9988.HK)")

    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        ticker_input = st.text_input(
            "Ticker",
            placeholder="ex: AAPL, MC.PA, NESN.SW, 005930.KS...",
            label_visibility="collapsed",
        ).strip().upper()
    with search_col2:
        analyze_btn = st.button("Analyser", use_container_width=True, type="primary")

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
            st.warning(
                f"Aucune donnée trouvée pour **{ticker_input}**. "
                "Vérifiez le ticker (format: AAPL, MC.PA, ASML...)"
            )
            st.session_state["search_result"] = None

    search_result = st.session_state.get("search_result")
    if search_result:
        st.subheader(f"Résultat : {search_result['Ticker']}")
        display_card(search_result)

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.info(SOFT_DISCLAIMER)
