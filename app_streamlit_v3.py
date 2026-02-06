import pandas as pd
import streamlit as st

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER

# =====================================================
# CONFIG APP
# =====================================================
st.set_page_config(
    page_title="SmartValue Scanner d’Actions (V3)",
    layout="wide"
)

GOOGLE_FORM_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform"
)

# =====================================================
# INIT SESSION STATE
# =====================================================
def init_state():
    defaults = {
        "min_score": 35,
        "min_conf": 50,
        "chosen_sectors": list(DEFAULT_UNIVERSE.keys()),
        "top_n": 15,
        "show_table": True,
        "scan_done": False,
        "last_results": None,
        "last_df": None,
        "last_email_md": None,
        "apply_recommended": False,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()

# Apply recommended preset SAFELY (before widgets)
if st.session_state["apply_recommended"]:
    st.session_state["min_score"] = 40
    st.session_state["min_conf"] = 70
    st.session_state["apply_recommended"] = False

# =====================================================
# HEADER
# =====================================================
st.title("🔎 SmartValue Scanner d’Actions (V3)")
st.caption("Scanner value long terme — aide à la réflexion, pas une recommandation.")

with st.expander("📘 Aide rapide : Comment lire les résultats ?"):
    st.markdown(
        """
**Score**  
Synthèse de valorisation, rentabilité, solidité et croissance.  
Ce n’est **pas** un signal d’achat.

**Confiance des données**  
Indique la fiabilité et la complétude des données utilisées.

**Tags**  
Résumé rapide du profil de l’entreprise.

👉 Toujours compléter avec vos propres recherches.
"""
    )

st.info("🧪 Version BÊTA gratuite — vos retours aident directement à améliorer l’outil.")

# =====================================================
# TABS
# =====================================================
tab_scan, tab_results, tab_feedback = st.tabs(
    ["🧠 Scan", "📊 Résultats", "💬 Feedback"]
)

# =====================================================
# TAB SCAN
# =====================================================
with tab_scan:
    st.subheader("⚙️ Réglages")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.slider(
            "Score minimum",
            0,
            100,
            step=1,
            key="min_score",
        )

    with c2:
        st.slider(
            "Confiance data minimum (%)",
            0,
            100,
            step=5,
            key="min_conf",
        )

    with c3:
        st.write(" ")
        st.write(" ")
        if st.button("⚡ Recommandé", use_container_width=True):
            st.session_state["apply_recommended"] = True
            st.rerun()
        st.caption("Recommandé = équilibre qualité / opportunités")

    st.divider()

    # -------- SECTEURS --------
    st.subheader("🏭 Secteurs")

    sectors = list(DEFAULT_UNIVERSE.keys())

    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button("✅ Tous", use_container_width=True):
            st.session_state["chosen_sectors"] = sectors.copy()
            for sec in sectors:
                st.session_state[f"sector_{sec}"] = True
            st.rerun()

    with b2:
        if st.button("❌ Aucun", use_container_width=True):
            st.session_state["chosen_sectors"] = []
            for sec in sectors:
                st.session_state[f"sector_{sec}"] = False
            st.rerun()

    with b3:
        if st.button("🔁 Inverser", use_container_width=True):
            current = set(st.session_state["chosen_sectors"])
            new_sel = [s for s in sectors if s not in current]
            st.session_state["chosen_sectors"] = new_sel
            for sec in sectors:
                st.session_state[f"sector_{sec}"] = sec in new_sel
            st.rerun()

    cols = st.columns(3)
    selected = []

    for i, sec in enumerate(sectors):
        key = f"sector_{sec}"
        if key not in st.session_state:
            st.session_state[key] = sec in st.session_state["chosen_sectors"]

        with cols[i % 3]:
            st.checkbox(sec, key=key)

        if st.session_state[key]:
            selected.append(sec)

    st.session_state["chosen_sectors"] = selected

    st.divider()

    st.slider(
        "Nombre d’actions affichées",
        5,
        50,
        step=1,
        key="top_n",
    )

    st.checkbox(
        "Afficher aussi le tableau comparatif",
        key="show_table",
    )

    st.divider()

    if st.button("🚀 Lancer le scan", use_container_width=True):
        universe = {
            k: v
            for k, v in DEFAULT_UNIVERSE.items()
            if k in st.session_state["chosen_sectors"]
        }

        scanner = SmartValueScanner(universe)

        with st.spinner("Analyse en cours..."):
            results = scanner.scan(
                min_score=st.session_state["min_score"],
                min_confidence=st.session_state["min_conf"],
            )

        st.session_state["scan_done"] = True

        if not results:
            st.session_state["last_results"] = []
            st.session_state["last_df"] = None
            st.session_state["last_email_md"] = None
        else:
            df = (
                pd.DataFrame(results)
                .sort_values("Score", ascending=False)
                .reset_index(drop=True)
            )
            st.session_state["last_results"] = results
            st.session_state["last_df"] = df
            st.session_state["last_email_md"] = scanner.to_email_markdown(
                results, top_n=5
            )

        st.success("Scan terminé ✅ → ouvre l’onglet **📊 Résultats** en haut")

# =====================================================
# TAB RESULTATS
# =====================================================
with tab_results:
    if not st.session_state["scan_done"]:
        st.info("Lance un scan dans l’onglet **🧠 Scan**.")

    elif st.session_state["last_results"] == []:
        st.warning("Aucune opportunité ne correspond aux filtres actuels.")

        # Feedback visible même si aucun résultat
        st.divider()
        st.subheader("💬 Feedback (Bêta)")
        st.write("Ton avis m’aide énormément à améliorer SmartValue.")
        st.link_button(
            "📝 Donner mon avis (2 minutes)",
            GOOGLE_FORM_URL,
            use_container_width=True,
        )

    else:
        df = st.session_state["last_df"]
        results = st.session_state["last_results"]

        st.success(
            f"Opportunités: {len(df)} | "
            f"Score moyen: {df['Score'].mean():.1f}/100 | "
            f"Meilleur: {df['Score'].max():.1f}/100"
        )

        st.subheader("🧩 Cartes")

        for r in results[: st.session_state["top_n"]]:
            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown(
                    f"### {r['Score badge']} {r['Ticker']} – {r['Société']}"
                )
                st.write(f"**Secteur:** {r['Secteur']}")
                st.write(f"**Résumé:** {r['Résumé']}")
                st.write(f"**Pourquoi:** {r['Pourquoi']}")
                st.write(f"**Tags:** {r['Tags']}")

            with col2:
                st.metric("Score", f"{r['Score']}/100")
                st.metric(
                    "Confiance",
                    f"{r['Confiance badge']} {r['Confiance %']}%",
                )
                st.write(f"Prix: {r['Prix']} {r['Devise']}")
                st.write(f"PER: {r['PER']}")
                st.write(f"ROE: {r['ROE %']}%")
                st.write(f"Dividende: {r['Div affichage']}%")

            st.divider()

        # -------- EMAIL TYPE --------
        with st.expander("📩 Voir un exemple d’email hebdomadaire (Top 5)"):
            if st.session_state["last_email_md"]:
                st.code(
                    st.session_state["last_email_md"],
                    language="markdown",
                )
            else:
                st.info("Lance un scan pour générer un exemple d’email.")

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Télécharger CSV",
            data=csv_bytes,
            file_name="smartvalue_results_v3.csv",
            mime="text/csv",
            use_container_width=True,
        )

        if st.session_state["show_table"]:
            with st.expander("📊 Tableau comparatif"):
                st.dataframe(df, use_container_width=True)

        # ✅ Feedback visible à la fin du scan (comme demandé)
        st.divider()
        st.subheader("💬 Feedback (Bêta)")
        st.write(
            "Si tu as 2 minutes: ce qui est clair / pas clair, ce qui manque, "
            "ce que tu aimerais recevoir chaque semaine… ça m’aide énormément 🙏"
        )
        st.link_button(
            "📝 Donner mon avis (2 minutes)",
            GOOGLE_FORM_URL,
            use_container_width=True,
        )

# =====================================================
# TAB FEEDBACK
# =====================================================
with tab_feedback:
    st.subheader("💬 Feedback")
    st.write("Ton avis m’aide énormément à améliorer SmartValue.")
    st.link_button(
        "📝 Donner mon avis (2 minutes)",
        GOOGLE_FORM_URL,
        use_container_width=True,
    )

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.info(SOFT_DISCLAIMER)

