import pandas as pd
import streamlit as st

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER

st.set_page_config(page_title="SmartValue Scanner (V3)", layout="wide")

# ----------------------------
# Session state init (mobile UX)
# ----------------------------
if "scan_stage" not in st.session_state:
    st.session_state.scan_stage = "idle"  # "idle" | "running"
if "trigger_scan" not in st.session_state:
    st.session_state.trigger_scan = False
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "last_df" not in st.session_state:
    st.session_state.last_df = None
if "last_email_md" not in st.session_state:
    st.session_state.last_email_md = None
if "last_scanner" not in st.session_state:
    st.session_state.last_scanner = None
if "last_universe" not in st.session_state:
    st.session_state.last_universe = None
if "last_filters" not in st.session_state:
    st.session_state.last_filters = None

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
st.caption("Scanner value long terme: score, confiance data, tags, résumé, explication simple.")
st.caption("📱 Sur mobile: les réglages sont dans le menu à gauche. Après avoir lancé le scan, ferme le menu pour voir les résultats.")

# ----------------------------
# Sidebar controls
# ----------------------------
with st.sidebar:
    st.header("⚙️ Réglages")

    min_score = st.slider("Score minimum", 0, 100, 35, 1)
    min_conf = st.slider("Confiance data minimum (%)", 0, 100, 50, 5)

    sectors = list(DEFAULT_UNIVERSE.keys())
    chosen = st.multiselect("Secteurs", sectors, default=sectors)

    top_n = st.slider("Nombre d'actions affichées", 5, 50, 15, 1)
    show_table = st.checkbox("Afficher aussi le tableau", value=True)

    st.markdown("---")
    st.subheader("🚀 Scan")

    if st.session_state.scan_stage == "running":
        st.info(
            "⏳ Scan en cours…\n\n"
            "📱 Sur mobile: ferme le menu (←) pour voir les résultats quand ça termine.",
            icon="🔎"
        )
        run = False
    else:
        # Bouton normal: au clic -> on déclenche un scan et on rerun pour verrouiller l'UI
        if st.button("🚀 Lancer le scan", use_container_width=True):
            st.session_state.scan_stage = "running"
            st.session_state.trigger_scan = True
            st.rerun()
        run = False  # on ne s'appuie pas sur run directement

# ----------------------------
# Trigger scan (runs after sidebar UI is updated)
# ----------------------------
if st.session_state.scan_stage == "running" and st.session_state.trigger_scan:
    # Reset trigger so it doesn't loop
    st.session_state.trigger_scan = False

    universe = {k: v for k, v in DEFAULT_UNIVERSE.items() if k in chosen}
    scanner = SmartValueScanner(universe)

    # Store current config for reproducibility
    st.session_state.last_universe = universe
    st.session_state.last_filters = {
        "min_score": min_score,
        "min_conf": min_conf,
        "chosen": chosen,
        "top_n": top_n,
        "show_table": show_table,
    }

    with st.spinner("Analyse en cours..."):
        results = scanner.scan(min_score=min_score, min_confidence=min_conf)

    # Done scanning
    st.session_state.scan_stage = "idle"
    st.session_state.last_scanner = scanner
    st.session_state.last_results = results

    if not results:
        st.session_state.last_df = None
        st.session_state.last_email_md = None
    else:
        df = pd.DataFrame(results).sort_values("Score", ascending=False).reset_index(drop=True)
        st.session_state.last_df = df
        st.session_state.last_email_md = scanner.to_email_markdown(results, top_n=5)

    # Re-run once to refresh UI with results (and sidebar unlocked)
    st.rerun()

# ----------------------------
# Display results (from session)
# ----------------------------
results = st.session_state.last_results
df = st.session_state.last_df
email_md = st.session_state.last_email_md
scanner = st.session_state.last_scanner

if results is not None:
    if not results:
        st.error("Aucune opportunité ne passe les filtres actuels.")
        st.info(SOFT_DISCLAIMER)
    else:
        st.success(
            f"Opportunités: {len(df)} | "
            f"Score moyen: {df['Score'].mean():.1f}/100 | "
            f"Meilleur: {df['Score'].max():.1f}/100"
        )

        st.subheader("🧩 Vue Cartes (plus lisible)")
        for r in results[:top_n]:
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
        st.download_button("⬇️ Télécharger CSV", data=csv_bytes, file_name="smartvalue_results_v3.csv", mime="text/csv")

        if show_table:
            st.subheader("📊 Tableau (comparaison rapide)")
            cols = [
                "Score", "Confiance %", "Ticker", "Société", "Secteur", "Prix", "Devise",
                "PER", "P/B", "EV/EBITDA", "ROE %", "Marge %", "Dette/Equity",
                "Div %", "Croissance CA %", "Tags", "Résumé", "Pourquoi"
            ]
            st.dataframe(df[cols].head(top_n), use_container_width=True)

# ----------------------------
# Footer + disclaimer + feedback
# ----------------------------
st.markdown("---")
st.info(SOFT_DISCLAIMER)

st.divider()
st.markdown("### 💬 Feedback (Version Bêta)")
st.write("Ton avis m’aide énormément à améliorer SmartValue. Ça prend 2 minutes 🙏")

st.link_button(
    "📝 Donner mon avis (2 minutes)",
    "https://docs.google.com/forms/d/e/1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform?usp=sharing&ouid=116329167308565311458"
)
