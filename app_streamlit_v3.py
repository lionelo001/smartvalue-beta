import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="SmartValue Scanner d’Actions (V3)",
    layout="wide"
)

GA_ID = "G-M4S6VSF3W5"

# Injecte la balise Google dans la page (pas dans un iframe)
st.html(f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>
""")

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER

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

# Apply recommended preset SAFELY (before widgets are created)
if st.session_state["apply_recommended"]:
    st.session_state["min_score"] = 40
    st.session_state["min_conf"] = 70
    st.session_state["apply_recommended"] = False

# =====================================================
# HEADER
# =====================================================
st.title("🔎 SmartValue Scanner d’Actions (V3)")
st.caption("Un scanner pour repérer des actions à creuser (long terme), avec explication du pourquoi.")

st.info("🧪 Version BÊTA gratuite — vos retours aident directement à améliorer l’outil.")

with st.expander("🎬 Comment ça marche (30 sec)"):
    st.markdown(
        """
1) Choisis tes réglages (ou clique **Recommandé**)  
2) Clique **Lancer le scan**  
3) Lis les résultats: score, confiance data, tags, explication  
4) Si une action t’intéresse: complète avec tes recherches (rapport annuel, secteur, risques, valorisation)
"""
    )

with st.expander("📚 Lexique (abréviations)"):
    st.markdown(
        """
**PER (P/E)** : prix / bénéfice. Plus bas = parfois moins cher, mais à contextualiser (secteur, cycle).  
**ROE** : rentabilité des fonds propres. Plus haut = souvent business efficace (attention aux effets de levier).  
**P/B** : prix / valeur comptable. Utile sur banques/assurances/indus (moins sur tech).  
**EV/EBITDA** : valorisation globale vs profits opérationnels. Sert à comparer des entreprises.  
**Dette/Equity** : niveau d’endettement. Plus bas = bilan souvent plus “safe”.  
**Croissance CA** : évolution du chiffre d’affaires. Plus haut = dynamique, mais à vérifier (durable ?).
"""
    )

st.divider()

# =====================================================
# RÉGLAGES
# =====================================================
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
    st.caption("Recommandé = bon équilibre qualité / opportunités")

st.divider()

# =====================================================
# SECTEURS
# =====================================================
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

# =====================================================
# AFFICHAGE
# =====================================================
st.subheader("📌 Affichage")

c4, c5 = st.columns(2)

with c4:
    st.slider(
        "Nombre d’actions affichées",
        5,
        50,
        step=1,
        key="top_n",
    )

with c5:
    st.checkbox(
        "Afficher aussi le tableau comparatif (avancé)",
        key="show_table",
    )

st.divider()

# =====================================================
# LANCER LE SCAN
# =====================================================
st.subheader("🚀 Scan")

run = st.button("🚀 Lancer le scan", use_container_width=True)

if run:
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
        st.session_state["last_email_md"] = scanner.to_email_markdown(results, top_n=5)

    st.success("✅ Scan terminé — les résultats sont juste en dessous 👇")

st.divider()

# =====================================================
# RÉSULTATS (INLINE)
# =====================================================
st.subheader("📊 Résultats du dernier scan")

if not st.session_state["scan_done"]:
    st.info("Lance un scan pour afficher les résultats.")
else:
    if st.session_state["last_results"] == []:
        st.warning("Aucune opportunité ne correspond aux filtres actuels.")
    else:
        df = st.session_state["last_df"]
        results = st.session_state["last_results"]

        st.success(
            f"Opportunités: {len(df)} | "
            f"Score moyen: {df['Score'].mean():.1f}/100 | "
            f"Meilleur: {df['Score'].max():.1f}/100"
        )

        st.markdown("### 🧩 Cartes (lisible)")

        for r in results[: st.session_state["top_n"]]:
            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown(f"#### {r['Score badge']} {r['Ticker']} – {r['Société']}")
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

        # Email type (hidden)
        with st.expander("📩 Voir un exemple d’email hebdomadaire (Top 5)"):
            if st.session_state["last_email_md"]:
                st.code(st.session_state["last_email_md"], language="markdown")
            else:
                st.info("Lance un scan pour générer un exemple d’email.")

        # Export CSV
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Télécharger CSV",
            data=csv_bytes,
            file_name="smartvalue_results_v3.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Table advanced
        if st.session_state["show_table"]:
            with st.expander("📊 Tableau comparatif (avancé)"):
                st.dataframe(df, use_container_width=True)

    # Feedback (always after a scan, even if no results)
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
# FOOTER
# =====================================================
st.markdown("---")
st.info(SOFT_DISCLAIMER)




