import pandas as pd
import streamlit as st

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER

st.set_page_config(page_title="SmartValue Scanner (V3)", layout="wide")

st.title("🔎 SmartValue Scanner (V3)")
with st.expander("ℹ️ Comment lire les résultats ?"):
    st.markdown("""
    **Score**
    - Le score synthétise plusieurs critères (valorisation, rentabilité, solidité financière, croissance).
    - Plus le score est élevé, plus l'entreprise ressort comme intéressante selon ces critères.
    - Ce n’est **pas** un signal d’achat.

    **Confiance des données**
    - Indique la fiabilité et la complétude des données utilisées.
    - Une confiance élevée signifie que les données sont cohérentes et exploitables.
    - Une confiance plus basse invite simplement à plus de prudence.

    **Tags**
    - Les tags résument le profil de l’entreprise (VALUE, QUALITY, SAFE, GROWTH, DIVIDEND…).
    - Ils servent à comprendre rapidement **pourquoi** l’entreprise ressort.

    **Important**
    - Ces résultats sont des aides à la réflexion.
    - Ils ne remplacent jamais une analyse personnelle complète.
    """)

st.info("🧪 Version BÊTA gratuite. L’objectif: tester, améliorer, et simplifier pour les investisseurs long terme. Vos retours sont les bienvenus 🙏")
st.caption("Scanner value long terme: score, confiance data, tags, résumé, explication simple.")

with st.sidebar:
    st.header("⚙️ Réglages")
    min_score = st.slider("Score minimum", 0, 100, 35, 1)
    min_conf = st.slider("Confiance data minimum (%)", 0, 100, 50, 5)

    sectors = list(DEFAULT_UNIVERSE.keys())
    chosen = st.multiselect("Secteurs", sectors, default=sectors)

    top_n = st.slider("Nombre d'actions affichées", 5, 50, 15, 1)
    show_table = st.checkbox("Afficher aussi le tableau", value=True)

    run = st.button("🚀 Lancer le scan")

if run:
    universe = {k: v for k, v in DEFAULT_UNIVERSE.items() if k in chosen}
    scanner = SmartValueScanner(universe)

    with st.spinner("Analyse en cours..."):
        results = scanner.scan(min_score=min_score, min_confidence=min_conf)

    if not results:
        st.error("Aucune opportunité ne passe les filtres actuels.")
        st.info(SOFT_DISCLAIMER)
        st.stop()

    df = pd.DataFrame(results).sort_values("Score", ascending=False).reset_index(drop=True)

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
    st.code(scanner.to_email_markdown(results, top_n=5), language="markdown")

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

st.markdown("---")
st.info(SOFT_DISCLAIMER)

