# app_streamlit_v3.py
# SmartValue Scanner d’Actions (V3) - One Page (no sidebar)

from __future__ import annotations

import uuid
from typing import Dict, List

import pandas as pd
import requests
import streamlit as st

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER


# =====================================================
# CONFIG (must be first Streamlit call)
# =====================================================
st.set_page_config(
    page_title="SmartValue Scanner d’Actions (V3)",
    layout="wide",
)


# =====================================================
# CONSTANTS
# =====================================================
FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform?usp=sharing&ouid=116329167308565311458"


# =====================================================
# GA4 (Measurement Protocol) - reliable on Streamlit
# =====================================================
def _ga_enabled() -> bool:
    return "GA_ID" in st.secrets and "GA_SECRET" in st.secrets


def ga_event(event_name: str, params: dict | None = None) -> None:
    if not _ga_enabled():
        return

    if "ga_client_id" not in st.session_state:
        st.session_state["ga_client_id"] = str(uuid.uuid4())

    ga_id = st.secrets["GA_ID"]
    ga_secret = st.secrets["GA_SECRET"]

    url = (
        "https://www.google-analytics.com/mp/collect"
        f"?measurement_id={ga_id}&api_secret={ga_secret}"
    )

    payload = {
        "client_id": st.session_state["ga_client_id"],
        "events": [
            {
                "name": event_name,
                "params": params or {},
            }
        ],
    }

    try:
        requests.post(url, json=payload, timeout=2)
    except Exception:
        pass


if "ga_open_sent" not in st.session_state:
    ga_event("app_open", {"app": "smartvalue_v3_onepage"})
    st.session_state["ga_open_sent"] = True


# =====================================================
# STATE
# =====================================================
def init_state() -> None:
    if "min_score" not in st.session_state:
        st.session_state["min_score"] = 35
    if "min_conf" not in st.session_state:
        st.session_state["min_conf"] = 50
    if "top_n" not in st.session_state:
        st.session_state["top_n"] = 15
    if "show_table" not in st.session_state:
        st.session_state["show_table"] = True

    if "sectors_selected" not in st.session_state:
        st.session_state["sectors_selected"] = {k: True for k in DEFAULT_UNIVERSE.keys()}

    if "last_results" not in st.session_state:
        st.session_state["last_results"] = []


def set_recommended() -> None:
    st.session_state["min_score"] = 35
    st.session_state["min_conf"] = 50


def build_universe() -> Dict[str, List[str]]:
    chosen = [k for k, v in st.session_state["sectors_selected"].items() if v]
    if not chosen:
        return {}
    return {k: DEFAULT_UNIVERSE[k] for k in chosen}


init_state()


# =====================================================
# HEADER
# =====================================================
st.title("🔎 SmartValue Scanner d’Actions (V3)")
st.caption("Scanner value long terme : score, confiance data, tags, résumé, explication simple.")

col_a, col_b = st.columns([3, 1])
with col_a:
    st.info(
        "🧪 Version BÊTA gratuite. Objectif : tester, améliorer, simplifier pour les investisseurs long terme. "
        "Vos retours sont précieux 🙏"
    )
with col_b:
    st.link_button("📝 Feedback (2 min)", FEEDBACK_URL, use_container_width=True)


# =====================================================
# AIDE + LEXIQUE
# =====================================================
with st.expander("📘 Aide rapide : Comment lire les résultats ?"):
    st.markdown(
        """
**Score**
- Synthèse de plusieurs critères (valorisation, rentabilité, solidité, croissance).
- Plus il est élevé, plus l’entreprise ressort selon ces critères.
- Ce n’est **pas** un signal d’achat.

**Confiance des données**
- Indique la complétude / cohérence des données.
- Plus c’est haut, plus l’analyse est fiable.
- Plus bas = à vérifier davantage.

**Tags**
- Résument le profil (VALUE, QUALITY, SAFE, GROWTH, DIVIDEND…).

**Important**
- Résultats indicatifs, à compléter avec vos recherches.
        """.strip()
    )

with st.expander("📚 Lexique (abréviations)"):
    st.markdown(
        """
- **PER (P/E)** : prix / bénéfices. Plus bas = potentiellement moins cher, mais dépend du secteur.
- **P/B** : prix / valeur comptable. Utile pour banques, industrielles, etc.
- **EV/EBITDA** : valorisation vs profit opérationnel. Souvent utile pour comparer des entreprises.
- **ROE** : rentabilité des capitaux propres. Plus haut = business efficace (à contextualiser).
- **Marge %** : profitabilité (selon données dispo).
- **Dette/Equity** : dette relative aux capitaux propres. Plus bas = bilan plus sain.
- **Croissance CA %** : évolution du chiffre d’affaires (si dispo).
- **Div %** : rendement du dividende (si versé).
        """.strip()
    )


st.divider()


# =====================================================
# RÉGLAGES (ON PAGE)
# =====================================================
st.subheader("⚙️ Réglages (simple)")

c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.1, 1.1], gap="large")

with c1:
    st.slider("Score minimum", 0, 100, int(st.session_state["min_score"]), 1, key="min_score")
with c2:
    st.slider("Confiance data minimum (%)", 0, 100, int(st.session_state["min_conf"]), 5, key="min_conf")
with c3:
    st.slider("Nombre d'actions affichées", 5, 50, int(st.session_state["top_n"]), 1, key="top_n")
with c4:
    st.checkbox("Afficher aussi le tableau", value=bool(st.session_state["show_table"]), key="show_table")
    st.button("✨ Recommandé", on_click=set_recommended, use_container_width=True)

st.markdown("### 🧩 Secteurs (coche/décoche)")
# Checkboxes in a grid (more compact)
sector_names = list(DEFAULT_UNIVERSE.keys())
cols = st.columns(3)
for i, sector in enumerate(sector_names):
    with cols[i % 3]:
        current_val = st.session_state["sectors_selected"].get(sector, True)
        st.session_state["sectors_selected"][sector] = st.checkbox(sector, value=current_val, key=f"sector_{sector}")

st.divider()

scan_col1, scan_col2, scan_col3 = st.columns([1, 1, 1])
with scan_col2:
    run = st.button("🚀 Lancer le scan", use_container_width=True)

if run:
    ga_event("scan_click", {"app": "smartvalue_v3_onepage"})
    universe = build_universe()

    if not universe:
        st.error("Sélectionne au moins 1 secteur.")
        st.stop()

    scanner = SmartValueScanner(universe)

    with st.spinner("Analyse en cours..."):
        results = scanner.scan(
            min_score=int(st.session_state["min_score"]),
            min_confidence=int(st.session_state["min_conf"]),
        )

    st.session_state["last_results"] = results

    ga_event(
        "scan_done",
        {
            "results_count": int(len(results)),
            "min_score": int(st.session_state["min_score"]),
            "min_conf": int(st.session_state["min_conf"]),
        },
    )

# =====================================================
# RESULTS (always below, same page)
# =====================================================
results = st.session_state.get("last_results", [])

st.subheader("📊 Résultats")

if not results:
    st.warning("Lance un scan pour afficher les résultats.")
else:
    df = pd.DataFrame(results).sort_values("Score", ascending=False).reset_index(drop=True)

    st.success(
        f"Opportunités: {len(df)} | "
        f"Score moyen: {df['Score'].mean():.1f}/100 | "
        f"Meilleur: {df['Score'].max():.1f}/100"
    )

    st.markdown("## 🧩 Vue Cartes (plus lisible)")
    top_n = int(st.session_state["top_n"])

    for r in results[:top_n]:
        col1, col2 = st.columns([3, 2], gap="large")

        with col1:
            st.markdown(f"### {r.get('Score badge','')} {r.get('Ticker','')} - {r.get('Société','')}")
            st.write(f"**Secteur:** {r.get('Secteur','')}")
            st.write(f"**Résumé:** {r.get('Résumé','')}")
            st.write(f"**Pourquoi:** {r.get('Pourquoi','')}")
            st.write(f"**Tags:** {r.get('Tags','')}")

        with col2:
            st.metric("Score", f"{r.get('Score', '—')}/100")
            st.metric("Confiance", f"{r.get('Confiance badge','')} {r.get('Confiance %','—')}%")
            st.write(f"**Prix:** {r.get('Prix','—')} {r.get('Devise','')}")
            per_val = r.get("PER", None)
            st.write(f"**PER:** {'—' if per_val is None or (isinstance(per_val, float) and pd.isna(per_val)) else per_val}")
            roe_val = r.get("ROE %", None)
            st.write(f"**ROE:** {'—' if roe_val is None or (isinstance(roe_val, float) and pd.isna(roe_val)) else str(roe_val) + '%'}")
            st.write(f"**Dividende:** {r.get('Div affichage','—')}%")
            st.write(f"**Dette/Equity:** {r.get('Dette/Equity','—')}")
            st.write(f"**Croissance CA:** {r.get('Croissance CA %','—')}%")

        st.divider()

    st.info("💬 Un retour rapide = énorme pour améliorer la bêta 🙏")
    st.link_button("📝 Donner mon avis (2 minutes)", FEEDBACK_URL, use_container_width=True)

    st.subheader("📩 Exemple d’email hebdo (Top 5)")
    # Rebuild scanner for email formatting (or reuse if you kept reference)
    universe = build_universe()
    scanner = SmartValueScanner(universe) if universe else SmartValueScanner(DEFAULT_UNIVERSE)
    st.code(scanner.to_email_markdown(results, top_n=5), language="markdown")

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Télécharger CSV",
        data=csv_bytes,
        file_name="smartvalue_results_v3.csv",
        mime="text/csv",
    )

    if st.session_state["show_table"]:
        st.subheader("📊 Tableau (comparaison rapide)")
        cols = [
            "Score", "Confiance %", "Ticker", "Société", "Secteur", "Prix", "Devise",
            "PER", "P/B", "EV/EBITDA", "ROE %", "Marge %", "Dette/Equity",
            "Div %", "Croissance CA %", "Tags", "Résumé", "Pourquoi"
        ]
        safe_cols = [c for c in cols if c in df.columns]
        st.dataframe(df[safe_cols].head(top_n), use_container_width=True)


# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.info(SOFT_DISCLAIMER)
st.write("### 💬 Feedback (Version Bêta)")
st.write("Ton avis m’aide énormément à améliorer SmartValue. Ça prend 2 minutes 🙏")
st.link_button("📝 Donner mon avis (2 minutes)", FEEDBACK_URL, use_container_width=True)
