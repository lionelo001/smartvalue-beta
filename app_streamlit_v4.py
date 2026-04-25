"""
app_streamlit_v4.py — SmartValue Scanner V4
Design : terminal financier premium
Technique : st.components.v1.html pour l'UI custom + Streamlit pour la logique
"""

from __future__ import annotations
import uuid
import json
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from scanner_core import SmartValueScanner, DEFAULT_UNIVERSE, SOFT_DISCLAIMER

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="SmartValue Scanner", page_icon="🔎", layout="wide")

FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSftKDyx2BZ0BnMgn6JOsDGYpNxK0YTqqKgXASrTlz2UfFwbvQ/viewform"

# ─────────────────────────────────────────────────────────────
# CSS GLOBAL — cache tout le chrome Streamlit
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{background:#080909!important;color:#ECEEF2!important;font-family:'DM Sans',sans-serif!important;}
#MainMenu,footer,header,.stDeployButton{visibility:hidden!important;display:none!important;}
.main .block-container{padding:0!important;max-width:100%!important;}
section[data-testid="stSidebar"]{display:none!important;}
.stButton>button{
  background:#C8F135!important;color:#080909!important;border:none!important;
  font-family:'Syne',sans-serif!important;font-weight:700!important;font-size:0.75rem!important;
  letter-spacing:0.05em!important;text-transform:uppercase!important;border-radius:0!important;
  padding:0.5rem 1.2rem!important;
}
.stButton>button:hover{background:#8BDE0F!important;}
.stButton>button[kind="secondary"]{
  background:transparent!important;color:#ECEEF2!important;
  border:1px solid rgba(255,255,255,0.1)!important;
}
.stButton>button[kind="secondary"]:hover{border-color:rgba(255,255,255,0.25)!important;background:transparent!important;}
.stProgress>div>div>div{background:#C8F135!important;}
.stProgress>div>div{background:rgba(255,255,255,0.04)!important;}
.stAlert,[data-testid="stInfoBox"],[data-testid="stSuccessBox"],[data-testid="stWarningBox"]{
  background:#0F1012!important;border:1px solid rgba(255,255,255,0.06)!important;
  border-radius:0!important;color:#8A8F9B!important;font-size:0.82rem!important;
}
.stDownloadButton>button{
  background:transparent!important;border:1px solid rgba(255,255,255,0.1)!important;
  color:#ECEEF2!important;font-family:'Syne',sans-serif!important;border-radius:0!important;
}
.stDownloadButton>button:hover{border-color:#C8F135!important;color:#C8F135!important;background:transparent!important;}
.stLinkButton>a{background:transparent!important;border:1px solid rgba(255,255,255,0.1)!important;color:#ECEEF2!important;border-radius:0!important;text-decoration:none!important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# GA4
# ─────────────────────────────────────────────────────────────
def ga_event(name, params=None):
    if "GA_ID" not in st.secrets or "GA_SECRET" not in st.secrets:
        return
    if "ga_cid" not in st.session_state:
        st.session_state["ga_cid"] = str(uuid.uuid4())
    try:
        requests.post(
            f"https://www.google-analytics.com/mp/collect?measurement_id={st.secrets['GA_ID']}&api_secret={st.secrets['GA_SECRET']}",
            json={"client_id": st.session_state["ga_cid"], "events": [{"name": name, "params": params or {}}]},
            timeout=2,
        )
    except Exception:
        pass

if "ga_sent" not in st.session_state:
    ga_event("app_open_v4")
    st.session_state["ga_sent"] = True

# ─────────────────────────────────────────────────────────────
# API KEY + STATE
# ─────────────────────────────────────────────────────────────
API_KEY = st.secrets.get("FMP_API_KEY", "")

def init_state():
    d = {
        "min_score": 35, "min_conf": 50, "top_n": 15,
        "sectors": {k: True for k in DEFAULT_UNIVERSE},
        "results": [], "search_result": None,
        "active_view": "scanner",
    }
    for k, v in d.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────────────────────
# HTML HELPERS
# ─────────────────────────────────────────────────────────────
FONTS = "@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');"

BASE_CSS = f"""
<style>
{FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{
  --bg:#080909;--bg2:#0F1012;--bg3:#16181C;
  --accent:#C8F135;--text:#ECEEF2;--muted:#5A5F6B;--muted2:#8A8F9B;
  --border:rgba(255,255,255,0.06);--border2:rgba(255,255,255,0.10);
}}
body{{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;}}
</style>
"""

def fmt(v, suffix=""):
    if v is None:
        return "—"
    return f"{v}{suffix}"

def render_tags(tags_str):
    if not tags_str:
        return ""
    html = ""
    for t in tags_str.split(","):
        t = t.strip()
        if t:
            html += f'<span style="font-size:0.58rem;font-family:DM Mono,monospace;letter-spacing:0.06em;padding:0.15rem 0.45rem;border:1px solid rgba(200,241,53,0.2);color:#C8F135;margin-right:4px;">{t}</span>'
    return html

def render_score_bars(r):
    blocs = [
        ("Val.", r.get("Bloc valuation", 0), "#C8F135"),
        ("Rent.", r.get("Bloc rentabilité", 0), "#6EE7B7"),
        ("Santé", r.get("Bloc santé", 0), "#93C5FD"),
        ("Crois.", r.get("Bloc croissance", 0), "#FCD34D"),
        ("Div.", r.get("Bloc dividende", 0), "#F9A8D4"),
    ]
    html = '<div style="width:90px;margin-top:6px;">'
    for label, val, color in blocs:
        pct = min(int(val), 100)
        w = int(90 * pct / 100)
        html += f"""
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:4px;">
          <div style="width:28px;font-size:0.55rem;color:#5A5F6B;text-align:right;flex-shrink:0;">{label}</div>
          <div style="background:rgba(255,255,255,0.04);height:2px;flex:1;position:relative;">
            <div style="background:{color};height:2px;width:{w}px;max-width:100%;"></div>
          </div>
        </div>"""
    html += "</div>"
    return html

def render_card(r, rank):
    score = r.get("Score", 0)
    conf = r.get("Confiance %", 0)
    return f"""
    <div style="background:#0F1012;border:1px solid rgba(255,255,255,0.06);padding:1rem 1.25rem;margin-bottom:8px;display:grid;grid-template-columns:28px 1fr 100px;gap:12px;align-items:start;"
         onmouseover="this.style.borderColor='rgba(200,241,53,0.15)'"
         onmouseout="this.style.borderColor='rgba(255,255,255,0.06)'">
      <div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:#5A5F6B;padding-top:2px;">#{str(rank).zfill(2)}</div>
      <div>
        <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px;">
          <span style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;letter-spacing:-0.02em;">{r.get("Ticker","")}</span>
          <span style="font-size:0.72rem;color:#5A5F6B;">{r.get("Société","")} · {r.get("Secteur","")} · {r.get("Pays","")}</span>
        </div>
        <div style="margin-bottom:6px;">{render_tags(r.get("Tags",""))}</div>
        <div style="font-size:0.72rem;color:#7A7F8C;line-height:1.5;border-left:2px solid rgba(200,241,53,0.2);padding-left:8px;margin-bottom:10px;">
          {r.get("Résumé","")} — {r.get("Pourquoi","")}
        </div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;">
          {_metric("Prix", f"{r.get('Prix','—')} {r.get('Devise','')}")}
          {_metric("PER", fmt(r.get("PER")))}
          {_metric("P/B", fmt(r.get("P/B")))}
          {_metric("ROE", fmt(r.get("ROE %"), "%"))}
          {_metric("Marge", fmt(r.get("Marge %"), "%"))}
          {_metric("EV/EBITDA", fmt(r.get("EV/EBITDA")))}
          {_metric("Dette/Eq.", fmt(r.get("Dette/Equity")))}
          {_metric("Croissance", fmt(r.get("Croissance CA %"), "%"))}
          {_metric("Div.", r.get("Div affichage","—") + "%")}
        </div>
      </div>
      <div style="text-align:right;">
        <div style="font-family:'DM Mono',monospace;font-size:2rem;font-weight:500;color:#C8F135;line-height:1;">{score}</div>
        <div style="font-size:0.55rem;color:#5A5F6B;text-transform:uppercase;letter-spacing:0.07em;">/100</div>
        {render_score_bars(r)}
        <div style="font-size:0.58rem;color:#5A5F6B;font-family:'DM Mono',monospace;margin-top:6px;">{r.get("Confiance badge","")} {conf}%</div>
      </div>
    </div>"""

def _metric(label, value):
    return f"""
    <div>
      <div style="font-family:'DM Mono',monospace;font-size:0.75rem;font-weight:500;color:#ECEEF2;">{value}</div>
      <div style="font-size:0.55rem;color:#5A5F6B;text-transform:uppercase;letter-spacing:0.06em;margin-top:1px;">{label}</div>
    </div>"""

# ─────────────────────────────────────────────────────────────
# TOPBAR + SIDEBAR HTML
# ─────────────────────────────────────────────────────────────
def render_shell(results_count=0, avg_score=0, best_score=0, avg_conf=0):
    sectors_active = sum(1 for v in st.session_state["sectors"].values() if v)
    return f"""
    {BASE_CSS}
    <div style="display:grid;grid-template-columns:220px 1fr;min-height:100vh;background:#080909;">

      <!-- SIDEBAR -->
      <div style="background:#0F1012;border-right:1px solid rgba(255,255,255,0.06);display:flex;flex-direction:column;padding:1.5rem 0;">
        <div style="padding:0 1.5rem 1.5rem;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:1rem;">
          <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;letter-spacing:-0.02em;">
            Smart<span style="color:#C8F135;">Value</span>
          </div>
          <div style="font-size:0.6rem;color:#5A5F6B;letter-spacing:0.1em;text-transform:uppercase;margin-top:3px;">Scanner V4 · FMP Data</div>
        </div>

        <div style="padding:0 1rem;margin-bottom:0.5rem;">
          <div style="font-size:0.58rem;color:#5A5F6B;letter-spacing:0.1em;text-transform:uppercase;padding:0 0.5rem;margin-bottom:0.5rem;margin-top:0.75rem;">Navigation</div>
          <div style="display:flex;align-items:center;gap:8px;padding:0.45rem 0.75rem;font-size:0.78rem;background:rgba(200,241,53,0.08);color:#C8F135;margin-bottom:2px;">
            <div style="width:4px;height:4px;border-radius:50%;background:#C8F135;flex-shrink:0;"></div>Scanner univers
          </div>
          <div style="display:flex;align-items:center;gap:8px;padding:0.45rem 0.75rem;font-size:0.78rem;color:#5A5F6B;margin-bottom:2px;">
            <div style="width:4px;height:4px;border-radius:50%;background:currentColor;flex-shrink:0;"></div>Recherche ticker
          </div>
        </div>

        <div style="padding:0 1rem;margin-top:0.5rem;">
          <div style="font-size:0.58rem;color:#5A5F6B;letter-spacing:0.1em;text-transform:uppercase;padding:0 0.5rem;margin-bottom:0.5rem;">Secteurs actifs ({sectors_active})</div>
          {''.join(f'<div style="display:flex;align-items:center;gap:8px;padding:0.35rem 0.75rem;font-size:0.72rem;color:{("#C8F135" if v else "#3A3F4B")};"><div style="width:4px;height:4px;border-radius:50%;background:currentColor;"></div>{k}</div>' for k, v in list(st.session_state["sectors"].items())[:8])}
        </div>

        <div style="margin-top:auto;padding:1rem 1.5rem;border-top:1px solid rgba(255,255,255,0.06);">
          <div style="font-size:0.58rem;color:#5A5F6B;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.75rem;">Filtres actifs</div>
          {_sb_filter("Score min", st.session_state["min_score"], 100)}
          {_sb_filter("Confiance min", st.session_state["min_conf"], 100)}
        </div>
      </div>

      <!-- MAIN -->
      <div style="display:flex;flex-direction:column;overflow:hidden;">
        <!-- TOPBAR -->
        <div style="display:flex;align-items:center;justify-content:space-between;padding:0.9rem 1.5rem;border-bottom:1px solid rgba(255,255,255,0.06);">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-family:'Syne',sans-serif;font-size:0.85rem;font-weight:700;">Résultats du scan</span>
            <span style="background:rgba(200,241,53,0.1);border:1px solid rgba(200,241,53,0.2);color:#C8F135;font-size:0.58rem;font-family:'DM Mono',monospace;letter-spacing:0.06em;padding:0.2rem 0.5rem;">FMP · LIVE</span>
          </div>
          <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.65rem;color:#5A5F6B;font-family:'DM Mono',monospace;">
            Trié par score · {results_count} résultats
          </div>
        </div>

        <!-- STATS -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:rgba(255,255,255,0.06);border-bottom:1px solid rgba(255,255,255,0.06);">
          {_stat(results_count, "Opportunités")}
          {_stat(f"{avg_score:.1f}", "Score moyen")}
          {_stat(f"{best_score:.1f}", "Meilleur score")}
          {_stat(f"{avg_conf:.0f}%", "Confiance moy.")}
        </div>

        <!-- RESULTS AREA placeholder — rempli par Python -->
        <div id="results-area" style="padding:1.25rem 1.5rem;flex:1;overflow:auto;">
        </div>
      </div>
    </div>"""

def _sb_filter(label, val, max_val):
    pct = int((val / max_val) * 100)
    return f"""
    <div style="margin-bottom:10px;">
      <div style="font-size:0.65rem;color:#8A8F9B;margin-bottom:4px;">{label}</div>
      <div style="background:#16181C;height:2px;width:100%;position:relative;">
        <div style="background:#C8F135;height:2px;width:{pct}%;"></div>
      </div>
      <div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:#C8F135;margin-top:2px;">{val}</div>
    </div>"""

def _stat(val, label):
    return f"""
    <div style="background:#080909;padding:0.9rem 1.5rem;">
      <div style="font-family:'DM Mono',monospace;font-size:1.4rem;font-weight:500;color:#C8F135;letter-spacing:-0.02em;">{val}</div>
      <div style="font-size:0.58rem;color:#5A5F6B;text-transform:uppercase;letter-spacing:0.07em;margin-top:3px;">{label}</div>
    </div>"""

# ─────────────────────────────────────────────────────────────
# LAYOUT PRINCIPAL
# ─────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 2.8])

with left_col:
    st.markdown(f"""
    <div style="background:#0F1012;border:1px solid rgba(255,255,255,0.06);padding:1.5rem;">
      <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;letter-spacing:-0.02em;margin-bottom:0.25rem;">
        Smart<span style="color:#C8F135;">Value</span> Scanner
      </div>
      <div style="font-size:0.62rem;color:#5A5F6B;letter-spacing:0.08em;text-transform:uppercase;border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:1rem;margin-bottom:1rem;">
        V4 · Financial Modeling Prep
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

    with st.expander("⚙️ Réglages"):
        st.slider("Score minimum", 0, 100, key="min_score")
        st.slider("Confiance minimum (%)", 0, 100, step=5, key="min_conf")
        st.slider("Résultats affichés", 5, 50, key="top_n")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✨ Recommandés"):
                st.session_state["min_score"] = 45
                st.session_state["min_conf"] = 70
                st.toast("Réglages recommandés ✅")
                st.rerun()

    with st.expander("🧩 Secteurs"):
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Tout ✓", key="all"):
                for k in DEFAULT_UNIVERSE:
                    st.session_state["sectors"][k] = True
                st.rerun()
        with b2:
            if st.button("Tout ✗", key="none", type="secondary"):
                for k in DEFAULT_UNIVERSE:
                    st.session_state["sectors"][k] = False
                st.rerun()
        for sector in DEFAULT_UNIVERSE:
            st.session_state["sectors"][sector] = st.checkbox(
                sector,
                value=st.session_state["sectors"].get(sector, True),
                key=f"s_{sector}",
            )

    st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

    run = st.button("🚀 Lancer le scan", use_container_width=True, type="primary")

    st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

    with st.expander("🔍 Recherche ticker"):
        ticker_input = st.text_input("Ticker", placeholder="AAPL · MC.PA · NESN.SW", label_visibility="collapsed").strip().upper()
        if st.button("Analyser →", use_container_width=True):
            if not API_KEY:
                st.error("Clé API manquante.")
            elif ticker_input:
                with st.spinner(f"Analyse {ticker_input}..."):
                    sc = SmartValueScanner(api_key=API_KEY)
                    res = sc.scan_ticker(ticker_input)
                if res:
                    st.session_state["search_result"] = res
                    st.session_state["results"] = [res]
                    st.rerun()
                else:
                    st.warning(f"Ticker introuvable : {ticker_input}")

    with st.expander("📘 Aide"):
        st.markdown("""
**Score** — Synthèse de 5 blocs (valorisation, rentabilité, santé, croissance, dividende). Pas un signal d'achat.

**Confiance** — Qualité et complétude des données FMP. < 60% → vérifier manuellement.

**Tags** — VALUE · QUALITÉ · SÛR · CROISSANCE · DIVIDENDE
        """)
    with st.expander("📚 Lexique"):
        st.markdown("""
- **PER** : Prix/Bénéfices · **P/B** : Prix/Valeur comptable
- **EV/EBITDA** : Valorisation/profit opérationnel
- **ROE** : Rentabilité des capitaux propres
- **Marge** : Bénéfice net/CA · **Div** : Rendement dividende
        """)

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    st.link_button("📝 Feedback (2 min)", FEEDBACK_URL, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# SCAN
# ─────────────────────────────────────────────────────────────
with right_col:
    if run:
        if not API_KEY:
            st.error("Clé API FMP manquante. Ajoute FMP_API_KEY dans les secrets Streamlit.")
            st.stop()
        universe = {k: v for k, v in DEFAULT_UNIVERSE.items() if st.session_state["sectors"].get(k, True)}
        if not universe:
            st.error("Sélectionne au moins un secteur.")
            st.stop()
        ga_event("scan_v4", {"sectors": len(universe)})
        scanner = SmartValueScanner(api_key=API_KEY, universe=universe)
        prog = st.progress(0, text="Démarrage...")
        def cb(pct, msg): prog.progress(pct, text=msg)
        results = scanner.scan(
            min_score=st.session_state["min_score"],
            min_confidence=st.session_state["min_conf"],
            progress_callback=cb,
        )
        prog.progress(1.0, text="Terminé ✅")
        st.session_state["results"] = results
        ga_event("scan_done_v4", {"count": len(results)})

    results = st.session_state.get("results", [])

    if results:
        df = pd.DataFrame(results)
        top_n = st.session_state["top_n"]
        avg_score = df["Score"].mean()
        best_score = df["Score"].max()
        avg_conf = df["Confiance %"].mean()

        # Topbar + stats + cartes — tout en components.html
        full_html = f"""{BASE_CSS}
        <div style="background:#0F1012;border:1px solid rgba(255,255,255,0.06);margin-bottom:8px;">
          <div style="display:flex;align-items:center;justify-content:space-between;padding:0.9rem 1.25rem;border-bottom:1px solid rgba(255,255,255,0.06);">
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="font-family:'Syne',sans-serif;font-size:0.85rem;font-weight:700;color:#ECEEF2;">Résultats</span>
              <span style="background:rgba(200,241,53,0.1);border:1px solid rgba(200,241,53,0.2);color:#C8F135;font-size:0.58rem;font-family:DM Mono,monospace;letter-spacing:0.06em;padding:0.2rem 0.5rem;">FMP · LIVE</span>
            </div>
            <span style="font-size:0.65rem;color:#5A5F6B;font-family:DM Mono,monospace;">Trié par score · {len(results)} résultats</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:rgba(255,255,255,0.06);">
            {_stat(len(results), "Opportunités")}
            {_stat(f"{avg_score:.1f}", "Score moyen")}
            {_stat(f"{best_score:.1f}", "Meilleur")}
            {_stat(f"{avg_conf:.0f}%", "Confiance moy.")}
          </div>
        </div>"""
        for i, r in enumerate(results[:top_n], 1):
            full_html += render_card(r, i)
        components.html(full_html, height=min(len(results[:top_n]) * 240 + 160, 5000), scrolling=True)

        # Export + tableau
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "⬇️ Exporter CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="smartvalue_v4.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_b:
            pass

        with st.expander("📊 Tableau comparatif"):
            cols = ["Score","Confiance %","Ticker","Société","Secteur","Pays","Prix","Devise",
                    "PER","P/B","EV/EBITDA","ROE %","Marge %","Dette/Equity","Div %","Croissance CA %","Tags"]
            safe_cols = [c for c in cols if c in df.columns]
            st.dataframe(df[safe_cols].head(top_n), use_container_width=True)

        with st.expander("📩 Aperçu email (Top 5)"):
            universe = {k: v for k, v in DEFAULT_UNIVERSE.items() if st.session_state["sectors"].get(k, True)}
            sc2 = SmartValueScanner(api_key=API_KEY, universe=universe or DEFAULT_UNIVERSE)
            st.code(sc2.to_email_markdown(results, top_n=5), language="markdown")

    else:
        components.html(f"""{BASE_CSS}
        <div style="background:#0F1012;border:1px solid rgba(255,255,255,0.06);padding:5rem 2rem;text-align:center;">
          <div style="font-family:DM Mono,monospace;font-size:2.5rem;color:rgba(200,241,53,0.12);margin-bottom:1.5rem;">&lt;/&gt;</div>
          <div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;color:#8A8F9B;margin-bottom:0.5rem;">Prêt à analyser</div>
          <div style="font-size:0.82rem;color:#5A5F6B;line-height:1.6;">Configure tes filtres et secteurs, puis lance le scan pour voir les résultats.</div>
        </div>
        """, height=260)

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="border-top:1px solid rgba(255,255,255,0.06);padding:1rem 0;margin-top:1rem;font-size:0.72rem;color:#5A5F6B;line-height:1.7;">
{SOFT_DISCLAIMER}
</div>
""", unsafe_allow_html=True)
