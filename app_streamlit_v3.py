import pandas as pd
import streamlit as st

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="SmartValue Scanner (V3)", layout="wide")

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform?usp=sharing&ouid=116329167308565311458"

# =====================================================
# STYLE (ONGLETS + UX)
# =====================================================
st.markdown("""
<style>
button[data-testid="stTab"] {
    font-size: 18px !important;
    padding: 12px 18px !important;
    font-weight: 650 !important;
    border-radius: 12px !important;
    margin-right: 6px !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    transition: all 0.15s ease-in-out !important;
}
button[data-testid="stTab"]:hover {
    background: rgba(255,255,255,0.10) !important;
}
button[data-testid="stTab"][aria-selected="true"] {
    background: rgba(14,165,233,0.16) !important;
    border: 1px solid rgba(14,165,233,0.40) !important;
    color: #0ea5e9 !important;
    box-shadow: 0 6px 18px rgba(0,0,0,0.18) !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# SESSION STATE
# =====================================================
def init_state():
    defaults = {
        "min_score": 35,
        "min_conf": 50,
        "chosen_sectors": list(DEFAULT_UNIVERSE.keys()),
        "top_n": 15,
        "show_table": True,

        "last_results": None,
        "last_df": None,
        "last_email_md": None,
        "scan_done": False,

        # ✅ flag to apply presets safely
        "apply_recommended": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ✅ Apply recommended BEFORE widgets are created (safe)
if st.session_state.get("apply_recommended"):
    st.session_state["min_score"] = 40
    st.session_state["min_conf"] = 70
    st.session_state["apply_recommended"] = False

# =====================================================
# HEADER
# =====================================================
st.title("🔎 SmartValue Scanner (V3)")
st.caption("Scanner value long terme – clair, pédagogique, sans promesses.")

with st.expander("📘 Aide rapide : Comment lire les résultats ?"):
    st.markdown("""
**Score**  
Synthèse de plusieurs critères (valorisation, rentabilité, solidité, croissance).  
Ce n’est **pas** un signal d’achat.

**Confiance des données**  
Indique la complétude / cohérence des données utilisées.

**Tags**  
Résumé rapide du profil (VALUE, QUALITY, SAFE, GROWTH, DIVIDEND…).

👉 Toujours compléter par vos propres recherches.
""")

st.info("🧪 Version BÊTA gratuite. Vos retours servent directement à améliorer l’outil 🙏")

# =====================================================
# TABS
# =====================================================
tab_scan, tab_results, tab_feedback = st.tabs(["🧠 Scan", "📊 Résultats", "💬 Feedback"])

# =====================================================
# TAB SCAN
# =====================================================
with tab_scan:
    st.subheader("⚙️ Réglages")

    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        st.slider(
            "Score minimum",
            0, 100,
            step=1,
            key="min_score"
        )

    with c2:
        st.slider(
            "Confiance data minimum (%)",
            0, 100,
            step=5,
            key="min_conf"
        )

    with c3:
        st.write(" ")
        st.write(" ")
        if st.button("⚡ Recommandé", use_container_width=True):
            # ✅ set a flag, then rerun; preset applied at top safely
            st.session_state["apply_recommended"] = True
            st.rerun()
        st.caption("Recommandé = bon équilibre qualité / opportunités.")

    st.divider()

    # -------- Secteurs (boutons visibles) --------
    st.subheader("🏭 Secteurs")
    sectors = list(DEFAULT_UNIVERSE.keys())

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("✅ Tous", use_container_width=True):
            st.session_state.chosen_sectors = sectors.copy()
            for sec in sectors:
                st.session_state[f"sector_{sec}"] = True
            st.rerun()

    with b2:
        if st.button("❌ Aucun", use_container_width=True):
            st.session_state.chosen_sectors = []
            for sec in sectors:
                st.session_state[f"sector_{sec}"] = False
            st.rerun()

    with b3:
        if st.button("🔁 Inverser", use_container_width=True):
            current = set(st.session_state.chosen_sectors)
            new_sel = [s for s in sectors if s not in current]
            st.session_state.chosen_sectors = new_sel
            for sec in sectors:
                st.session_state[f"sector_{sec}"] = (sec in new_sel)
            st.rerun()

    st.divider()

    cols = st.columns(3)
    selected = []

    for i, sec in enumerate(sectors):
        col = cols[i % 3]
        key = f"sector_{sec}"

        if key not in st.session_state:
            st.session_state[key] = sec in st.session_state.chosen_sectors

        with col:
            st.checkbox(sec, key=key)

        if st.session_state[key]:
            selected.append(sec)

    st.session_state.chosen_sectors = selected

    st.divider()

    st.slider(
        "Nombre d’actions affichées",
        5, 50,
        step=1,
        key="top_n"
    )

    st.checkbox(
        "Afficher aussi le tableau comparatif",
        key="show_table"
    )

    st.divider()

    if st.button("🚀 Lancer le scan", use_container_width=True):
        universe = {
            k: v for k, v in DEFAULT_UNIVERSE.items()
            if k in st.session_state.chosen_sectors
        }

        scanner = SmartValueScanner(universe)

        with st.spinner("Analyse en cours..."):
            results = scanner.scan(
                min_score=st.session_state["min_score"],
                min_confidence=st.session_state["min_conf"]
            )

        st.session_state.scan_done = True

        if not results:
            st.session_state.last_results = []
            st.session_state.last_df = None
            st.session_state.last_email_md = None
        else:
            df = (
                pd.DataFrame(results)
                .sort_values("Score", ascending=False)
                .reset_index(drop=True)
            )
            st.session_state.last_results = results
            st.session_state.last_df = df
            st.session_state.last_email_md = scanner.to_email_markdown(results, top_n=5)

        st.success("Scan terminé ✅ → ouvre l’onglet **📊 Résultats**")

# =====================================================
# TAB RESULTATS
# =====================================================
with tab_results:
    if not st.session_state.scan_done:
        st.info("Lance un scan dans l’onglet **🧠 Scan**.")
    elif st.session_state.last_results == []:
        st.warning("Aucune opportunité ne correspond aux filtres actuels.")
    else:
        df = st.session_state.last_df
        results = st.session_state.last_results

        st.success(
            f"Opportunités: {len(df)} | "
            f"Score moyen: {df['Score'].mean():.1f}/100 | "
            f"Meilleur: {df['Score'].max():.1f}/100"
        )

        st.subheader("🧩 Vue Cartes")
        for r in results[: int(st.session_state["top_n"])]:
            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown(f"### {r['Score badge']} {r['Ticker']} – {r['Société']}")
                st.write(f"**Secteur:** {r['Secteur']}")
                st.write(f"**Résumé:** {r['Résumé']}")
                st.write(f"**Pourquoi:** {r['Pourquoi']}")
                st.write(f"**Tags:** {r['Tags']}")

            with col2:
                st.metric("Score", f"{r['Score']}/100")
                st.metric("Confiance", f"{r['Confiance badge']} {r['Confiance %']}%")
                st.write(f"Prix: {r['Prix']} {r['Devise']}")
                st.write(f"PER: {r['PER']}")
                st.write(f"ROE: {r['ROE %']}%")
                st.write(f"Dividende: {r['Div affichage']}%")

            st.divider()

        st.subheader("📩 Email-ready (Top 5)")
        st.code(st.session_state.last_email_md, language="markdown")

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Télécharger CSV",
            data=csv_bytes,
            file_name="smartvalue_results_v3.csv",
            mime="text/csv",
            use_container_width=True
        )

        if st.session_state["show_table"]:
            st.subheader("📊 Tableau comparatif")
            st.dataframe(df, use_container_width=True)

    # -------- Feedback visible après scan --------
    if st.session_state.scan_done:
        st.divider()
        st.markdown("### 💬 Ton avis compte vraiment")
        st.info(
            "SmartValue est en version bêta. "
            "Si tu as une remarque ou une idée, ton retour m’aide énormément 🙏"
        )
        st.link_button(
            "📝 Donner mon avis (2 minutes)",
            GOOGLE_FORM_URL,
            use_container_width=True
        )

# =====================================================
# TAB FEEDBACK
# =====================================================
with tab_feedback:
    st.subheader("💬 Feedback")
    st.write("Ton avis m’aide directement à améliorer SmartValue.")
    st.link_button(
        "📝 Donner mon avis (2 minutes)",
        GOOGLE_FORM_URL,
        use_container_width=True
    )

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.info(SOFT_DISCLAIMER)
