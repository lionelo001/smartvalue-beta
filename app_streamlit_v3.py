import pandas as pd
import streamlit as st

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER

st.set_page_config(page_title="SmartValue Scanner (V3)", layout="wide")
st.markdown("""
<style>
/* Agrandir les onglets */
div[data-baseweb="tab"] > button {
    font-size: 18px;
    padding: 12px 24px;
    font-weight: 600;
}

/* Onglet actif */
div[data-baseweb="tab"] > button[aria-selected="true"] {
    color: #0ea5e9;
    border-bottom: 3px solid #0ea5e9;
}
</style>
""", unsafe_allow_html=True)


GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform?usp=sharing&ouid=116329167308565311458"

# ----------------------------
# Session state init
# ----------------------------
def _init_state():
    defaults = {
        # scan status
        "scan_running": False,
        "last_results": None,   # None = jamais scanné, [] = scan fait mais 0 résultats, list = résultats
        "last_df": None,
        "last_email_md": None,

        # UI settings (persist across tabs)
        "min_score": 35,
        "min_conf": 50,
        "chosen_sectors": list(DEFAULT_UNIVERSE.keys()),
        "top_n": 15,
        "show_table": True,

        # helpers
        "go_results_hint": False,  # show "go to results" hint after scan
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ----------------------------
# Header + Help
# ----------------------------
st.title("🔎 SmartValue Scanner (V3)")
st.caption("👀 Nouveau ? Clique juste ici pour une explication rapide 👇")

with st.expander("📘 Aide rapide (clique ici) : Comment lire les résultats ?"):
    st.markdown("""
    **Score**
    - Synthèse de plusieurs critères (valorisation, rentabilité, solidité, croissance).
    - Plus il est élevé, plus l’entreprise ressort selon ces critères.
    - Ce n’est **pas** un signal d’achat.

    **Confiance des données**
    - Indique la fiabilité / complétude des données.
    - Plus c’est haut, plus c’est cohérent.
    - Plus bas = à vérifier davantage.

    **Tags**
    - Résument le profil (VALUE, QUALITY, SAFE, GROWTH, DIVIDEND…).

    **Important**
    - Résultats indicatifs, à compléter avec vos recherches.
    """)

st.info("🧪 Version BÊTA gratuite. L’objectif: tester, améliorer, et simplifier pour les investisseurs long terme. Vos retours sont les bienvenus 🙏")
st.caption("📱 Mobile-friendly: utilise les onglets **Scan / Résultats / Feedback** (en haut).")

# ----------------------------
# Top menu (tabs)
# ----------------------------
tab_scan, tab_results, tab_feedback = st.tabs(["🧠 Scan", "📊 Résultats", "💬 Feedback"])

# ----------------------------
# Helpers
# ----------------------------
def run_scan():
    """Execute scan and store results in session_state."""
    st.session_state.scan_running = True
    st.session_state.go_results_hint = False

    universe = {
        k: v for k, v in DEFAULT_UNIVERSE.items()
        if k in st.session_state.chosen_sectors
    }
    scanner = SmartValueScanner(universe)

    with st.spinner("🔎 Analyse en cours..."):
        results = scanner.scan(
            min_score=st.session_state.min_score,
            min_confidence=st.session_state.min_conf
        )

    # Store
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

    st.session_state.scan_running = False
    st.session_state.go_results_hint = True


# ----------------------------
# TAB 1: Scan
# ----------------------------
with tab_scan:
    st.subheader("⚙️ Réglages du scan")

    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        st.session_state.min_score = st.slider(
            "Score minimum",
            0, 100,
            int(st.session_state.min_score),
            1
        )

    with c2:
        st.session_state.min_conf = st.slider(
            "Confiance data minimum (%)",
            0, 100,
            int(st.session_state.min_conf),
            5
        )

    with c3:
        sectors = list(DEFAULT_UNIVERSE.keys())
        st.session_state.chosen_sectors = st.multiselect(
            "Secteurs",
            sectors,
            default=st.session_state.chosen_sectors
        )

    c4, c5 = st.columns([1, 1])
    with c4:
        st.session_state.top_n = st.slider(
            "Nombre d'actions affichées",
            5, 50,
            int(st.session_state.top_n),
            1
        )
    with c5:
        st.session_state.show_table = st.checkbox(
            "Afficher aussi le tableau",
            value=bool(st.session_state.show_table)
        )

    st.markdown("### 🚀 Lancer")

    # Button disabled while scanning (prevents double clicks)
    if st.session_state.scan_running:
        st.info("⏳ Scan en cours… tu peux ensuite aller dans l’onglet **📊 Résultats**.", icon="🔎")
        st.button("🚀 Lancer le scan", use_container_width=True, disabled=True)
    else:
        if st.button("🚀 Lancer le scan", use_container_width=True):
            run_scan()
            st.rerun()

    # After scan: show a clear call to action
    if st.session_state.go_results_hint:
        if st.session_state.last_results == []:
            st.warning("Scan terminé ✅ Aucune opportunité ne passe les filtres. Essaie de baisser le score minimum ou la confiance.")
        else:
            best = st.session_state.last_df["Score"].max()
            st.success(f"Scan terminé ✅ Opportunités: {len(st.session_state.last_df)} | Meilleur score: {best:.1f}/100")

        st.info("👉 Maintenant ouvre l’onglet **📊 Résultats** (en haut) pour voir les cartes et le top 5 email-ready.")

# ----------------------------
# TAB 2: Results
# ----------------------------
with tab_results:
    results = st.session_state.last_results
    df = st.session_state.last_df
    email_md = st.session_state.last_email_md

    if results is None:
        st.info("Lance d’abord un scan dans l’onglet **🧠 Scan**.")
    elif results == []:
        st.warning("Aucune opportunité détectée avec les filtres actuels. Essaie d’ajuster les réglages dans l’onglet **🧠 Scan**.")
    else:
        st.success(
            f"Opportunités: {len(df)} | "
            f"Score moyen: {df['Score'].mean():.1f}/100 | "
            f"Meilleur: {df['Score'].max():.1f}/100"
        )

        st.subheader("🧩 Vue Cartes (plus lisible)")
        for r in results[: st.session_state.top_n]:
            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown(f"### {r['Score badge']} {r['Ticker']} - {r['Société']}")
                st.write(f"**Secteur:** {r['Secteur']}")
                st.write(f"**Résumé:** {r['Résumé']}")
                st.write(f"**Pourquoi:** {r['Pourquoi']}")
                st.write(f"**Tags:** {r['Tags']}")

            with col2:
                st.metric("Score", f"{r['Score']}/100")
                st.metric("Confiance", f"{r['Confiance badge']} {r['Confiance %']}%")
                st.write(f"**Prix:** {r['Prix']} {r['Devise']}")
                st.write(f"**PER:** {'—' if pd.isna(r['PER']) else r['PER']}")
                st.write(f"**ROE:** {'—' if pd.isna(r['ROE %']) else str(r['ROE %']) + '%'}")
                st.write(f"**Dividende:** {r['Div affichage']}%")
                st.write(f"**Dette/Equity:** {r['Dette/Equity']}")
                st.write(f"**Croissance CA:** {r['Croissance CA %']}%")

            st.divider()

        st.subheader("📩 Email-ready (Top 5)")
        st.code(email_md if email_md else "", language="markdown")

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Télécharger CSV",
            data=csv_bytes,
            file_name="smartvalue_results_v3.csv",
            mime="text/csv",
            use_container_width=True
        )

        if st.session_state.show_table:
            st.subheader("📊 Tableau (comparaison rapide)")
            cols = [
                "Score", "Confiance %", "Ticker", "Société", "Secteur", "Prix", "Devise",
                "PER", "P/B", "EV/EBITDA", "ROE %", "Marge %", "Dette/Equity",
                "Div %", "Croissance CA %", "Tags", "Résumé", "Pourquoi"
            ]
            st.dataframe(df[cols].head(st.session_state.top_n), use_container_width=True)

    # ✅ Feedback CTA visible uniquement après un scan (même si 0 résultat)
    if results is not None:
        st.divider()
        st.markdown("### 💬 Ton avis compte vraiment")
        st.info(
            "SmartValue est en version bêta. "
            "Si tu as une remarque, une incompréhension ou une idée d’amélioration, "
            "ton retour m’aide énormément 🙏"
        )
        st.caption("Même 1 phrase, c’est déjà précieux.")
        st.link_button(
            "📝 Donner mon avis (2 minutes)",
            GOOGLE_FORM_URL,
            use_container_width=True
        )

# ----------------------------
# TAB 3: Feedback
# ----------------------------
with tab_feedback:
    st.subheader("💬 Feedback (Version Bêta)")
    st.write("Ton avis m’aide énormément à améliorer SmartValue. Ça prend 2 minutes 🙏")

    st.link_button(
        "📝 Donner mon avis (2 minutes)",
        GOOGLE_FORM_URL,
        use_container_width=True
    )

# Footer
st.markdown("---")
st.info(SOFT_DISCLAIMER)

