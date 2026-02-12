# app_streamlit_v3.py
# SmartValue Scanner d’Actions (V3) - Streamlit App (clean + stable)

from __future__ import annotations

import uuid
from typing import Dict, List

import pandas as pd
import requests
import streamlit as st

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER


# =====================================================
# CONFIG APP (must be the first Streamlit call)
# =====================================================
st.set_page_config(
    page_title="SmartValue Scanner d’Actions (V3)",
    layout="wide",
)


# =====================================================
# GA4 (Measurement Protocol) - reliable on Streamlit
# =====================================================
def _ga_enabled() -> bool:
    return "GA_ID" in st.secrets and "GA_SECRET" in st.secrets


def ga_event(event_name: str, params: dict | None = None) -> None:
    """
    Sends a GA4 event via Measurement Protocol.
    Works even if scripts are blocked by Streamlit/iframes/adblock.
    """
    if not _ga_enabled():
        return

    # One client_id per session (so returning users can be estimated)
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
        # Fail silently: analytics must never break the app
        pass


# Fire once per session open
if "ga_open_sent" not in st.session_state:
    ga_event("app_open", {"app": "smartvalue_v3"})
    st.session_state["ga_open_sent"] = True


# =====================================================
# UI HELPERS
# =====================================================
FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform?usp=sharing&ouid=116329167308565311458"


def init_state() -> None:
    if "min_score" not in st.session_state:
        st.session_state["min_score"] = 35
    if "min_conf" not in st.session_state:
        st.session_state["min_conf"] = 50
    if "top_n" not in st.session_state:
        st.session_state["top_n"] = 15
    if "show_table" not in st.session_state:
        st.session_state["show_table"] = True

    # sectors as fixed checkboxes (persistent)
    if "sectors_selected" not in st.session_state:
        st.session_state["sectors_selected"] = {k: True for k in DEFAULT_UNIVERSE.keys()}

    if "run_scan" not in st.session_state:
        st.session_state["run_scan"] = False

    if "last_results" not in st.session_state:
        st.session_state["last_results"] = []


def set_recommended() -> None:
    # Recommended default values (always works)
    st.session_state["min_score"] = 35
    st.session_state["min_conf"] = 50


def build_universe_from_state() -> Dict[str, List[str]]:
    chosen = [k for k, v in st.session_state["sectors_selected"].items() if v]
    if not chosen:
        return {}
    return {k: DEFAULT_UNIVERSE[k] for k in chosen}


def render_help() -> None:
    with st.expander("📘 Aide rapide (clique ici) : Comment lire les résultats ?"):
        st.markdown(
            """
**Score**
- Synthèse de plusieurs critères (valorisation, rentabilité, solidité, croissance).
- Plus il est élevé, plus l’entreprise ressort selon ces critères.
- Ce n’est **pas** un signal d’achat.

**Confiance des données**
- Indique la complétude / cohérence des données (qualité des champs récupérés).
- Plus c’est haut, plus l’analyse est fiable.
- Plus bas = à vérifier davantage.

**Tags**
- Résument le profil (VALUE, QUALITY, SAFE, GROWTH, DIVIDEND…).

**Important**
- Résultats indicatifs, à compléter avec vos recherches.
            """.strip()
        )


# =====================================================
# APP
# =====================================================
init_state()

st.title("🔎 SmartValue Scanner d’Actions (V3)")
st.caption("👀 Nouveau ? Clique juste ici pour une explication rapide 👇")
render_help()

st.info(
    "🧪 Version BÊTA gratuite. Objectif : tester, améliorer, simplifier pour les investisseurs long terme. "
    "Vos retours sont précieux 🙏"
)


# -------------------------
# SIDEBAR SETTINGS
# -------------------------
with st.sidebar:
    st.header("⚙️ Réglages")

    # Recommended button always works
    st.button("✨ Recommandé", on_click=set_recommended, use_container_width=True)

    st.slider(
        "Score minimum",
        min_value=0,
        max_value=100,
        value=int(st.session_state["min_score"]),
        step=1,
        key="min_score",
    )
    st.slider(
        "Confiance data minimum (%)",
        min_value=0,
        max_value=100,
        value=int(st.session_state["min_conf"]),
        step=5,
        key="min_conf",
    )

    st.subheader("Secteurs")
    # fixed list of checkboxes (no disappearing)
    for sector in DEFAULT_UNIVERSE.keys():
        key = f"sector_{sector}"
        current_val = st.session_state["sectors_selected"].get(sector, True)

        new_val = st.checkbox(sector, value=current_val, key=key)
        st.session_state["sectors_selected"][sector] = new_val

    st.slider(
        "Nombre d'actions affichées",
        min_value=5,
        max_value=50,
        value=int(st.session_state["top_n"]),
        step=1,
        key="top_n",
    )

    st.checkbox("Afficher aussi le tableau", value=bool(st.session_state["show_table"]), key="show_table")

    st.divider()
    if st.button("🚀 Lancer le scan", use_container_width=True):
        st.session_state["run_scan"] = True
        ga_event("scan_click", {"app": "smartvalue_v3"})


# -------------------------
# MAIN - SCAN
# -------------------------
if st.session_state["run_scan"]:
    universe = build_universe_from_state()
    if not universe:
        st.error("Sélectionne au moins 1 secteur dans les réglages (sidebar).")
        st.stop()

    scanner = SmartValueScanner(universe)

    with st.spinner("Analyse en cours..."):
        results = scanner.scan(
            min_score=int(st.session_state["min_score"]),
            min_confidence=int(st.session_state["min_conf"]),
        )

    st.session_state["last_results"] = results
    st.session_state["run_scan"] = False  # reset

    if not results:
        st.error("Aucune opportunité ne passe les filtres actuels.")
        st.info(SOFT_DISCLAIMER)
        st.link_button("📝 Donner mon avis (2 minutes)", FEEDBACK_URL)
        st.stop()

    df = pd.DataFrame(results).sort_values("Score", ascending=False).reset_index(drop=True)

    ga_event(
        "scan_done",
        {
            "results_count": int(len(df)),
            "min_score": int(st.session_state["min_score"]),
            "min_conf": int(st.session_state["min_conf"]),
        },
    )

    st.success(
        f"Opportunités: {len(df)} | "
        f"Score moyen: {df['Score'].mean():.1f}/100 | "
        f"Meilleur: {df['Score'].max():.1f}/100"
    )

    st.subheader("🧩 Vue Cartes (plus lisible)")
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

    # Feedback button visible AFTER scan
    st.info("💬 Un retour rapide = énorme pour améliorer la bêta 🙏")
    st.link_button("📝 Donner mon avis (2 minutes)", FEEDBACK_URL)

    st.subheader("📩 Exemple d’email hebdo (Top 5)")
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


# -------------------------
# FOOTER
# -------------------------
st.markdown("---")
st.info(SOFT_DISCLAIMER)
st.write("### 💬 Feedback (Version Bêta)")
st.write("Ton avis m’aide énormément à améliorer SmartValue. Ça prend 2 minutes 🙏")
st.link_button("📝 Donner mon avis (2 minutes)", FEEDBACK_URL)
