import pandas as pd
import streamlit as st

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="SmartValue Scanner (V3)", layout="wide")

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform?usp=sharing&ouid=116329167308565311458"

# =====================================================
# STYLE (tabs + structure)
# =====================================================
st.markdown("""
<style>
/* Tabs */
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

/* Cards / sections */
.sv-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 16px;
    padding: 16px 16px;
    margin: 12px 0px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.10);
}
.sv-card h3 {
    margin-top: 0px;
    margin-bottom: 8px;
}
.sv-muted {
    color: rgba(255,255,255,0.72);
    font-size: 0.92rem;
}
.sv-pill {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.14);
    background: rgba(255,255,255,0.06);
    font-size: 0.85rem;
    margin-right: 6px;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

def card_start(title: str, subtitle: str | None = None):
    st.markdown('<div class="sv-card">', unsafe_allow_html=True)
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f'<div class="sv-muted">{subtitle}</div>', unsafe_allow_html=True)

def card_end():
    st.markdown("</div>", unsafe_allow_html=True)

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

        "apply_recommended": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# Apply recommended preset BEFORE widgets
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
**Score** : synthèse (valorisation, rentabilité, solidité, croissance).  
**Confiance** : qualité/cohérence des données.  
**Tags** : profil rapide (VALUE, QUALITY, SAFE, GROWTH, DIVIDEND).  
👉 Toujours compléter par vos recherches.
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
    card_start("⚙️ Réglages", "Choisis un niveau de filtre, ou clique sur Recommandé pour lancer vite.")
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        st.slider("Score minimum", 0, 100, step=1, key="min_score")

    with c2:
        st.slider("Confiance data minimum (%)", 0, 100, step=5, key="min_conf")

    with c3:
        st.write(" ")
        st.write(" ")
        if st.button("⚡ Recommandé", use_container_width=True):
            st.session_state["apply_recommended"] = True
            st.rerun()
        st.caption("Recommandé = équilibre qualité / opportunités.")
    card_end()

    card_start("🏭 Secteurs", "Clique pour activer / désactiver. (✅ Tous / ❌ Aucun / 🔁 Inverser)")
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

    st.markdown(" ")
    st.markdown(
        " ".join([f'<span class="sv-pill">{s}</span>' for s in st.session_state.chosen_sectors[:8]])
        + (f'<span class="sv-pill">+{max(0, len(st.session_state.chosen_sectors)-8)} autres</span>'
           if len(st.session_state.chosen_sectors) > 8 else ""),
        unsafe_allow_html=True
    )
    card_end()

    card_start("📌 Affichage", "Réduit le bruit: affiche plus ou moins d’actions, et le tableau si besoin.")
    c4, c5 = st.columns([1, 1])
    with c4:
        st.slider("Nombre d’actions affichées", 5, 50, step=1, key="top_n")
    with c5:
        st.checkbox("Afficher aussi le tableau comparatif", key="show_table")
    card_end()

    card_start("🚀 Lancer", "Clique, puis va dans l’onglet Résultats.")
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
    card_end()

# =====================================================
# TAB RESULTATS
# =====================================================
with tab_results:
    if not st.session_state.scan_done:
        card_start("📊 Résultats", "Lance un scan dans l’onglet Scan pour voir les opportunités.")
        st.info("👉 Va dans **🧠 Scan** puis clique sur **🚀 Lancer le scan**.")
        card_end()

    elif st.session_state.last_results == []:
        card_start("📊 Résultats", "Aucune opportunité ne correspond aux filtres actuels.")
        st.warning("Essaie de baisser le **Score minimum** ou la **Confiance minimum**.")
        card_end()

    else:
        df = st.session_state.last_df
        results = st.session_state.last_results

        card_start("✅ Résumé", "Vue rapide avant de scroller.")
        st.success(
            f"Opportunités: {len(df)} | "
            f"Score moyen: {df['Score'].mean():.1f}/100 | "
            f"Meilleur: {df['Score'].max():.1f}/100"
        )
        card_end()

        card_start("🧩 Cartes (lisible)", "Chaque carte résume une opportunité: score, confiance, tags, et explication.")
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
        card_end()

        # Email-ready + Tableau en "détails"
        with st.expander("📩 Email-ready (Top 5)"):
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
            with st.expander("📊 Tableau comparatif (avancé)"):
                st.dataframe(df, use_container_width=True)

    # Feedback visible après scan
    if st.session_state.scan_done:
        card_start("💬 Feedback", "Ton avis aide à améliorer SmartValue (2 minutes).")
        st.info("Même une phrase, c’est déjà précieux 🙏")
        st.link_button("📝 Donner mon avis (2 minutes)", GOOGLE_FORM_URL, use_container_width=True)
        card_end()

# =====================================================
# TAB FEEDBACK
# =====================================================
with tab_feedback:
    card_start("💬 Feedback", "Tu peux laisser un retour même sans lancer de scan.")
    st.write("Ton avis m’aide directement à améliorer SmartValue.")
    st.link_button("📝 Donner mon avis (2 minutes)", GOOGLE_FORM_URL, use_container_width=True)
    card_end()

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.info(SOFT_DISCLAIMER)
