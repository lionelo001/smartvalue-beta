# app_streamlit_v3.py
# SmartValue Scanner d’Actions (V3) - One Page (no sidebar)
# Email preview + table are collapsible (expanders)
# Recommended button near "Réglages" + toast
# Tags translated for francophones (UI + email + export)
# GA4 tracking via Measurement Protocol (reliable on Streamlit)

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
# TAGS TRANSLATION
# =====================================================
TAG_MAP = {
    "GROWTH": "CROISSANCE",
    "QUALITY": "QUALITÉ",
    "SAFE": "SÛR",
    "DIVIDEND": "DIVIDENDE",
    "ASSET": "ACTIFS",
    "VALUE": "VALUE",  # OK en FR (et connu)
    "DATA_CHECK": "VÉRIF. DONNÉES",
}


def translate_text(s: str) -> str:
    """Replace English tags/keywords inside a string."""
    if not isinstance(s, str) or not s.strip():
        return s
    out = s
    # Replace longer tokens first to avoid partial weirdness
    for k, v in TAG_MAP.items():
        out = out.replace(k, v)
    return out


def translate_tags_field(tags_field) -> str:
    """Translate a tags field that may be a string like 'QUALITY, SAFE, GROWTH'."""
    if tags_field is None:
        return ""
    if isinstance(tags_field, float) and pd.isna(tags_field):
        return ""
    return translate_text(str(tags_field))


# =====================================================
# GA4 (Measurement Protocol) - reliable on Streamlit
# =====================================================
def _ga_enabled() -> bool:
    return "GA_ID" in st.secrets and "GA_SECRET" in st.secrets


def ga_event(event_name: str, params: dict | None = None) -> None:
    """Send a GA4 event via Measurement Protocol."""
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
        "events": [{"name": event_name, "params": params or {}}],
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

    if "sectors_selected" not in st.session_state:
        st.session_state["sectors_selected"] = {k: True for k in DEFAULT_UNIVERSE.keys()}

    if "last_results" not in st.session_state:
        st.session_state["last_results"] = []

    if "recommended_just_applied" not in st.session_state:
        st.session_state["recommended_just_applied"] = False


def set_recommended() -> None:
    # Stricter defaults (more pro)
    st.session_state["min_score"] = 40
    st.session_state["min_conf"] = 70
    st.session_state["recommended_just_applied"] = True


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

st.info(
    "🧪 Version BÊTA gratuite. Objectif : tester, améliorer, et simplifier pour les investisseurs long terme. "
    "Vos retours seront utiles pour la suite 🙏"
)


# =====================================================
# HELP + LEXICON
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
- Résument le profil (VALUE, QUALITÉ, SÛR, CROISSANCE, DIVIDENDE…).

**Important**
- Résultats indicatifs, à compléter avec vos recherches.
        """.strip()
    )

with st.expander("📚 Lexique (abréviations)"):
    st.markdown(
        """
- **PER (P/E)** : prix / bénéfices.
- **P/B** : prix / valeur comptable.
- **EV/EBITDA** : valorisation vs profit opérationnel.
- **ROE** : rentabilité des capitaux propres.
- **Marge %** : profitabilité (si donnée dispo).
- **Dette/Equity** : dette relative aux capitaux propres.
- **Croissance CA %** : évolution du chiffre d’affaires (si donnée dispo).
- **Div %** : rendement du dividende (si versé).
        """.strip()
    )

st.divider()


# =====================================================
# SETTINGS (ON PAGE)
# =====================================================
header_left, header_right = st.columns([3, 1])
with header_left:
    st.subheader("⚙️ Réglages")
with header_right:
    st.button("✨ Recommandé", on_click=set_recommended, use_container_width=True)

# Toast after recommended is applied
if st.session_state.get("recommended_just_applied"):
    st.toast("Réglages recommandés appliqués ✅", icon="✅")
    st.session_state["recommended_just_applied"] = False

c1, c2, c3 = st.columns([1.1, 1.1, 1.1], gap="large")
with c1:
    st.slider("Score minimum", 0, 100, int(st.session_state["min_score"]), 1, key="min_score")
with c2:
    st.slider("Confiance data minimum (%)", 0, 100, int(st.session_state["min_conf"]), 5, key="min_conf")
with c3:
    st.slider("Nombre d'actions affichées", 5, 50, int(st.session_state["top_n"]), 1, key="top_n")

st.markdown("### 🧩 Secteurs (coche/décoche)")

sector_names = list(DEFAULT_UNIVERSE.keys())
grid = st.columns(3, gap="large")
for i, sector in enumerate(sector_names):
    with grid[i % 3]:
        current_val = st.session_state["sectors_selected"].get(sector, True)
        st.session_state["sectors_selected"][sector] = st.checkbox(
            sector,
            value=current_val,
            key=f"sector_{sector}",
        )

st.divider()

scan_left, scan_mid, scan_right = st.columns([1, 1, 1], gap="large")
with scan_mid:
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
    # Build dataframe
    df = pd.DataFrame(results).sort_values("Score", ascending=False).reset_index(drop=True)

    # Translate tags in df for display + export
    if "Tags" in df.columns:
        df["Tags"] = df["Tags"].apply(translate_tags_field)

    st.success(
        f"Opportunités: {len(df)} | "
        f"Score moyen: {df['Score'].mean():.1f}/100 | "
        f"Meilleur: {df['Score'].max():.1f}/100"
    )

    st.markdown("## 🧩 Vue Cartes")
    top_n = int(st.session_state["top_n"])

    # Also translate tags for cards without mutating original dicts
    for r in results[:top_n]:
        col1, col2 = st.columns([3, 2], gap="large")

        tags_fr = translate_tags_field(r.get("Tags", ""))

        with col1:
            st.markdown(f"### {r.get('Score badge','')} {r.get('Ticker','')} - {r.get('Société','')}")
            st.write(f"**Secteur:** {r.get('Secteur','')}")
            st.write(f"**Résumé:** {translate_text(r.get('Résumé',''))}")
            st.write(f"**Pourquoi:** {translate_text(r.get('Pourquoi',''))}")
            st.write(f"**Tags:** {tags_fr}")

        with col2:
            st.metric("Score", f"{r.get('Score', '—')}/100")
            st.metric("Confiance", f"{r.get('Confiance badge','')} {r.get('Confiance %','—')}%")
            st.write(f"**Prix:** {r.get('Prix','—')} {r.get('Devise','')}")
            per_val = r.get("PER", None)
            st.write(f"**PER:** {'—' if per_val is None or (isinstance(per_val, float) and pd.isna(per_val)) else per_val}")
            roe_val = r.get("ROE %", None)
            st.write(
                f"**ROE:** {'—' if roe_val is None or (isinstance(roe_val, float) and pd.isna(roe_val)) else str(roe_val) + '%'}"
            )
            st.write(f"**Dividende:** {r.get('Div affichage','—')}%")
            st.write(f"**Dette/Equity:** {r.get('Dette/Equity','—')}")
            st.write(f"**Croissance CA:** {r.get('Croissance CA %','—')}%")

        st.divider()

    # Collapsible email preview (translated)
    with st.expander("📩 Exemple d’email hebdo (Top 5) — cliquer pour afficher"):
        universe = build_universe()
        scanner = SmartValueScanner(universe) if universe else SmartValueScanner(DEFAULT_UNIVERSE)
        email_md = scanner.to_email_markdown(results, top_n=5)
        email_md = translate_text(email_md)
        st.code(email_md, language="markdown")

    # Collapsible table (always available)
    with st.expander("📊 Tableau comparatif — cliquer pour afficher"):
        cols = [
            "Score", "Confiance %", "Ticker", "Société", "Secteur", "Prix", "Devise",
            "PER", "P/B", "EV/EBITDA", "ROE %", "Marge %", "Dette/Equity",
            "Div %", "Croissance CA %", "Tags", "Résumé", "Pourquoi",
        ]
        safe_cols = [c for c in cols if c in df.columns]
        st.dataframe(df[safe_cols].head(top_n), use_container_width=True)

    # Export after table/email (with French tags)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Télécharger au format tableur (Excel/CSV)",
        data=csv_bytes,
        file_name="smartvalue_results_v3.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # Single feedback button only here (after scan, bottom)
    st.divider()
    st.markdown("### 💬 Feedback (Version Bêta)")
    st.write("Ton avis m’aide énormément à améliorer SmartValue. Ça prend 2 minutes 🙏")
    st.link_button("📝 Donner mon avis (2 minutes)", FEEDBACK_URL, use_container_width=True)


# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.info(SOFT_DISCLAIMER)
