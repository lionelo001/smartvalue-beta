import time
import numpy as np
import yfinance as yf
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests_cache
requests_cache.install_cache("smartvalue_cache", expire_after=60 * 60)  # 1h


# =========================
# CONFIG
# =========================

@dataclass
class Thresholds:
    pe_max: float = 25.0
    pb_max: float = 3.5
    ev_ebitda_max: float = 18.0
    roe_min: float = 0.08          # 8%
    margin_min: float = 0.05       # 5%
    debt_to_equity_max: float = 0.8  # 0.8 = 80% (ratio)
    rev_growth_min: float = 0.03   # 3%
    dividend_min: float = 0.01     # 1%


@dataclass
class Weights:
    valuation: float = 0.30
    profitability: float = 0.30
    financial_health: float = 0.20
    growth: float = 0.15
    dividend: float = 0.05


DEFAULT_UNIVERSE: Dict[str, List[str]] = {
    "Tech": ["AAPL", "MSFT", "GOOGL", "NVDA", "TSM", "ASML", "ADBE", "CRM", "ORCL", "INTC"],
    "Finance": ["JPM", "BAC", "WFC", "HSBC", "GS", "AXP", "PYPL", "V", "MA"],
    "Santé": ["JNJ", "PFE", "UNH", "ABBV", "TMO", "DHR", "LLY", "MRK", "ABT", "BMY"],
    "Energie": ["XOM", "CVX", "SHEL", "BP", "TTE", "COP", "EOG"],
    "Conso": ["PG", "KO", "PEP", "WMT", "COST", "MCD", "NKE", "SBUX", "HD", "LOW"],
    "Industriels": ["CAT", "BA", "HON", "GE", "MMM", "UNP", "UPS", "FDX", "DE", "ETN"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "XEL"],
}

SOFT_DISCLAIMER = (
    "ℹ️ Ces résultats sont fournis à titre indicatif pour vous aider dans votre réflexion et vos choix. "
    "Ils ne remplacent pas une analyse complète (rapports, contexte du secteur, risques, valorisation). "
    "Si une opportunité vous intéresse, prenez le temps de compléter vos recherches avant toute décision."
)


# =========================
# HELPERS
# =========================

def safe_float(x, default=0.0) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, (int, float, np.integer, np.floating)):
            return float(x)
        return float(str(x).replace(",", "."))
    except Exception:
        return default


def clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def pct(x: float) -> float:
    # Yahoo renvoie parfois ratio (0.12) parfois %
    if x <= 1.0:
        return x * 100.0
    return x


def normalize_yield_to_pct(dy) -> float:
    """
    Retourne un dividende en % (ex: 3.2 = 3.2%)
    yfinance renvoie parfois un ratio (0.032), parfois déjà un % (3.2)
    + garde-fou anti-glitch (cap > 20% -> 0)
    """
    dy = safe_float(dy, 0.0)
    if dy <= 0:
        return 0.0
    pct_val = dy if dy > 1 else dy * 100
    if pct_val > 20:
        return 0.0
    return round(pct_val, 2)


def sane_multiple(x, lo: float, hi: float) -> float:
    x = safe_float(x, 0.0)
    if x <= 0:
        return 0.0
    if x < lo or x > hi:
        return 0.0
    return x


def retry_get_info(ticker: str, tries: int = 3, sleep_s: float = 0.7) -> Optional[dict]:
    for i in range(tries):
        try:
            info = yf.Ticker(ticker).info
            if isinstance(info, dict) and len(info) > 5:
                return info
        except Exception:
            pass
        time.sleep(sleep_s * (i + 1))
    return None


def confidence_badge(conf: float) -> str:
    if conf >= 80:
        return "🟢"
    if conf >= 60:
        return "🟡"
    return "🔴"


def score_badge(score: float) -> str:
    if score >= 70:
        return "🔥"
    if score >= 55:
        return "✅"
    if score >= 40:
        return "⚠️"
    return "🧊"


def format_div(div_pct: float) -> str:
    return "—" if div_pct <= 0 else f"{div_pct:.2f}"


# =========================
# CONFIDENCE MODEL (V3)
# =========================

def quality_confidence(m: dict) -> float:
    """
    Confiance pro:
    - complétude (40%)
    - plausibilité/sanity (40%)
    - fraîcheur light (20%)
    + pénalité "agrégateur gratuit" + cap max 92
    """
    keys = ["pe", "pb", "ev_ebitda", "roe", "margin", "debt_to_equity", "rev_growth", "div_yield"]

    # 1) Complétude
    present = 0
    for k in keys:
        v = m.get(k)
        if v is None:
            continue
        fv = safe_float(v, 0.0)
        if fv != 0.0:
            present += 1
    completeness = (present / len(keys)) * 100

    # 2) Sanity checks
    penalties = 0

    pe = safe_float(m.get("pe"), 0.0)
    pb = safe_float(m.get("pb"), 0.0)
    ev = safe_float(m.get("ev_ebitda"), 0.0)
    roe = pct(safe_float(m.get("roe"), 0.0))
    margin_pct = safe_float(m.get("margin"), 0.0) * 100

    dte = safe_float(m.get("debt_to_equity"), 0.0)
    dte_ratio = (dte / 100.0) if dte > 10 else dte

    dy = normalize_yield_to_pct(m.get("div_yield"))
    rg_pct = safe_float(m.get("rev_growth"), 0.0) * 100

    if pe and (pe < 1 or pe > 120): penalties += 12
    if pb and (pb < 0.1 or pb > 50): penalties += 8
    if ev and (ev < 1.5 or ev > 80): penalties += 10
    if roe and (roe < -50 or roe > 80): penalties += 10
    if margin_pct and (margin_pct < -30 or margin_pct > 60): penalties += 10
    if dte_ratio and (dte_ratio > 5): penalties += 10
    if dy and (dy > 12): penalties += 12
    if rg_pct and (rg_pct < -50 or rg_pct > 80): penalties += 8

    sanity = clamp(100 - penalties, 0, 100)

    # 3) Fraîcheur light
    price = safe_float(m.get("price"), 0.0)
    mcap = safe_float(m.get("mcap"), 0.0)
    currency = m.get("currency")

    freshness = 100.0
    if price <= 0: freshness -= 35
    if mcap <= 0: freshness -= 25
    if not currency: freshness -= 10
    freshness = clamp(freshness, 0, 100)

    conf = 0.40 * completeness + 0.40 * sanity + 0.20 * freshness

    # pénalité pour éviter la “perfection” (Yahoo = agrégateur)
    conf -= 5.0

    # cap pro (pas de 100%)
    conf = clamp(conf, 35.0, 92.0)
    return round(conf, 1)


# =========================
# SCORER
# =========================

class SmartValueScorer:
    def __init__(self, th: Thresholds = Thresholds(), w: Weights = Weights()):
        self.th = th
        self.w = w

    def score(self, m: dict) -> Tuple[float, dict, List[str], float, List[str], str]:
        """
        Returns:
          - total_score /100
          - details par bloc
          - why (max 3)
          - confidence /100 (cap 92)
          - tags
          - résumé 1 phrase
        """
        details = {}
        why: List[str] = []

        confidence = quality_confidence(m)

        # Normalisations / sanity-friendly
        pe = sane_multiple(m.get("pe"), lo=1.0, hi=120.0)
        pb = sane_multiple(m.get("pb"), lo=0.1, hi=50.0)
        ev = sane_multiple(m.get("ev_ebitda"), lo=1.5, hi=80.0)

        roe_pct = pct(safe_float(m.get("roe"), 0.0))
        margin = safe_float(m.get("margin"), 0.0)  # ratio (ex 0.30)
        margin_pct = margin * 100

        dte = safe_float(m.get("debt_to_equity"), 0.0)
        dte_ratio = (dte / 100.0) if dte > 10 else dte

        revenue = safe_float(m.get("revenue"), 0.0)
        ocf = safe_float(m.get("ocf"), 0.0)

        rg = safe_float(m.get("rev_growth"), 0.0)
        rg_pct = rg * 100

        dy_pct = normalize_yield_to_pct(m.get("div_yield"))

        # ---------- 1) VALUATION ----------
        val = 0.0
        if 0 < pe < self.th.pe_max:
            if pe < 12:
                pe_norm = 100
                why.append(f"PER bas ({pe:.1f})")
            elif pe < 18:
                pe_norm = 80
                why.append(f"PER raisonnable ({pe:.1f})")
            else:
                pe_norm = 60
            val += pe_norm * 0.50

        if 0 < pb < self.th.pb_max:
            pb_norm = 100 * (self.th.pb_max - pb) / self.th.pb_max
            val += clamp(pb_norm) * 0.30
            if pb < 2:
                why.append(f"P/B cool ({pb:.2f})")

        if 0 < ev < self.th.ev_ebitda_max:
            ev_norm = 100 * (self.th.ev_ebitda_max - ev) / self.th.ev_ebitda_max
            val += clamp(ev_norm) * 0.20
            if ev < 12:
                why.append(f"EV/EBITDA clean ({ev:.1f})")

        details["valuation"] = round(val, 1)

        # ---------- 2) PROFITABILITY ----------
        prof = 0.0
        if roe_pct > 0:
            if roe_pct > 20:
                prof += 100 * 0.50
                why.append(f"ROE très solide ({roe_pct:.1f}%)")
            elif roe_pct > 15:
                prof += 80 * 0.50
                why.append(f"ROE solide ({roe_pct:.1f}%)")
            elif roe_pct > 10:
                prof += 60 * 0.50
            elif roe_pct > 8:
                prof += 40 * 0.50

        if margin > self.th.margin_min:
            margin_norm = (margin - self.th.margin_min) * 400  # 5%->0, 30%->100
            prof += clamp(margin_norm) * 0.50
            if margin > 0.12:
                why.append(f"Marges ok ({margin_pct:.1f}%)")

        details["profitability"] = round(prof, 1)

        # ---------- 3) FINANCIAL HEALTH ----------
        health = 0.0
        if dte_ratio > 0:
            if dte_ratio < 0.30:
                health += 100 * 0.60
                why.append("Dette faible")
            elif dte_ratio < 0.60:
                health += 70 * 0.60
            elif dte_ratio < 0.80:
                health += 40 * 0.60

        if revenue > 0 and ocf > 0:
            cf_margin = ocf / revenue
            if cf_margin > 0.15:
                health += 100 * 0.40
                why.append("Cashflow solide")
            elif cf_margin > 0.10:
                health += 70 * 0.40
            elif cf_margin > 0.05:
                health += 40 * 0.40

        details["financial_health"] = round(health, 1)

        # ---------- 4) GROWTH ----------
        growth = 0.0
        if rg > 0:
            if rg > 0.15:
                growth = 100
                why.append(f"Croissance forte ({rg_pct:.1f}%)")
            elif rg > 0.10:
                growth = 80
            elif rg > 0.05:
                growth = 60
            elif rg > 0.03:
                growth = 40
                why.append(f"Croissance OK ({rg_pct:.1f}%)")
            else:
                growth = 20

        details["growth"] = round(growth, 1)

        # ---------- 5) DIVIDEND ----------
        div = 0.0
        if dy_pct > 0:
            if dy_pct > 5:
                div = 100
                why.append(f"Dividende élevé ({dy_pct:.1f}%)")
            elif dy_pct > 4:
                div = 80
            elif dy_pct > 3:
                div = 60
                why.append(f"Dividende sympa ({dy_pct:.1f}%)")
            elif dy_pct > 2:
                div = 40
            elif dy_pct > 1:
                div = 20

        details["dividend"] = round(div, 1)

        # ---------- TOTAL ----------
        total = (
            details["valuation"] * self.w.valuation
            + details["profitability"] * self.w.profitability
            + details["financial_health"] * self.w.financial_health
            + details["growth"] * self.w.growth
            + details["dividend"] * self.w.dividend
        )

        # ---------- TAGS ----------
        tags: List[str] = []

        if pe and pe < 15:
            tags.append("VALUE")
        if pb and pb < 2:
            tags.append("ASSET")
        if roe_pct > 20 and margin > 0.10:
            tags.append("QUALITY")
        if dte_ratio and dte_ratio < 0.60:
            tags.append("SAFE")
        if rg_pct > 8:
            tags.append("GROWTH")
        if dy_pct >= 2:
            tags.append("DIVIDEND")

        # Résumé 1 phrase
        summary_parts = []
        if "VALUE" in tags: summary_parts.append("valorisation attractive")
        if "QUALITY" in tags: summary_parts.append("business rentable")
        if "SAFE" in tags: summary_parts.append("bilan sain")
        if "GROWTH" in tags: summary_parts.append("croissance correcte")
        if "DIVIDEND" in tags: summary_parts.append("dividende intéressant")
        summary = ", ".join(summary_parts[:2]) if summary_parts else "profil équilibré"

        # Why max 3
        why = why[:3]

        return round(total, 1), details, why, confidence, tags, summary


# =========================
# SCANNER
# =========================

class SmartValueScanner:
    def __init__(
        self,
        universe: Dict[str, List[str]] = DEFAULT_UNIVERSE,
        th: Thresholds = Thresholds(),
        w: Weights = Weights(),
    ):
        self.universe = universe
        self.th = th
        self.scorer = SmartValueScorer(th, w)

    def fetch_metrics(self, ticker: str) -> Optional[dict]:
        info = retry_get_info(ticker)
        if not info:
            return None

        price = safe_float(info.get("regularMarketPrice") or info.get("currentPrice"), 0.0)
        mcap = safe_float(info.get("marketCap"), 0.0)

        if price <= 0 or price > 10000:
            return None
        if mcap < 500_000_000:
            return None

        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "currency": info.get("currency", "USD"),
            "price": price,
            "mcap": mcap,

            "pe": info.get("trailingPE") or info.get("forwardPE"),
            "pb": info.get("priceToBook"),
            "ev_ebitda": info.get("enterpriseToEbitda"),

            "roe": info.get("returnOnEquity"),
            "margin": info.get("profitMargins"),

            "debt_to_equity": info.get("debtToEquity"),
            "revenue": info.get("totalRevenue"),
            "ocf": info.get("operatingCashflow"),

            "rev_growth": info.get("revenueGrowth"),
            "div_yield": info.get("dividendYield"),
        }

    def scan(self, min_score: float = 35, min_confidence: float = 50) -> List[dict]:
        results: List[dict] = []
        tickers = [(sector, t) for sector, lst in self.universe.items() for t in lst]

        for sector, t in tickers:
            m = self.fetch_metrics(t)
            if not m:
                continue

            score, details, why, confidence, tags, summary = self.scorer.score(m)

            if confidence < min_confidence:
                continue
            if score < min_score:
                continue

            div_pct = normalize_yield_to_pct(m.get("div_yield"))

            results.append(
                {
                    "Ticker": m["ticker"],
                    "Société": (m["name"][:45] + "...") if len(m["name"]) > 45 else m["name"],
                    "Secteur": sector,
                    "Prix": round(m["price"], 2),
                    "Devise": m["currency"],

                    "PER": round(safe_float(m.get("pe"), np.nan), 2) if safe_float(m.get("pe"), 0) else np.nan,
                    "P/B": round(safe_float(m.get("pb"), np.nan), 2) if safe_float(m.get("pb"), 0) else np.nan,
                    "EV/EBITDA": round(safe_float(m.get("ev_ebitda"), np.nan), 2)
                    if safe_float(m.get("ev_ebitda"), 0)
                    else np.nan,

                    "ROE %": round(pct(safe_float(m.get("roe"), 0.0)), 1) if safe_float(m.get("roe"), 0) else np.nan,
                    "Marge %": round(safe_float(m.get("margin"), 0.0) * 100, 1) if safe_float(m.get("margin"), 0) else np.nan,

                    "Dette/Equity": (
                        round((safe_float(m.get("debt_to_equity"), np.nan) / 100.0), 2)
                        if safe_float(m.get("debt_to_equity"), 0) > 10
                        else round(safe_float(m.get("debt_to_equity"), np.nan), 2)
                    ),

                    "Div %": div_pct,
                    "Div affichage": format_div(div_pct),

                    "Croissance CA %": round(safe_float(m.get("rev_growth"), 0.0) * 100, 1)
                    if safe_float(m.get("rev_growth"), 0)
                    else 0.0,

                    "Score": score,
                    "Confiance %": confidence,
                    "Score badge": score_badge(score),
                    "Confiance badge": confidence_badge(confidence),

                    "Tags": ", ".join(tags),
                    "Résumé": summary,

                    "Pourquoi": " | ".join(why),

                    "Bloc valuation": details["valuation"],
                    "Bloc rentabilité": details["profitability"],
                    "Bloc santé": details["financial_health"],
                    "Bloc croissance": details["growth"],
                    "Bloc dividende": details["dividend"],
                }
            )

            time.sleep(0.05)

        results.sort(key=lambda x: x["Score"], reverse=True)
        return results

    def to_email_markdown(self, results: List[dict], top_n: int = 5) -> str:
        top = results[:top_n]
        lines = []
        lines.append("# 🔎 SmartValue Scanner | Sélection du moment\n")

        for i, r in enumerate(top, start=1):
            lines.append(
                f"## {i}) {r['Score badge']} {r['Ticker']} ({r['Secteur']}) "
                f"| Score {r['Score']}/100 | Confiance {r['Confiance badge']} {r['Confiance %']}%\n"
            )
            lines.append(f"- Prix: {r['Prix']} {r['Devise']}")
            if not (isinstance(r["PER"], float) and np.isnan(r["PER"])):
                lines.append(f"- PER: {r['PER']} | ROE: {r['ROE %']}% | Marge: {r['Marge %']}%")
            lines.append(
                f"- Dette/Equity: {r['Dette/Equity']} | Dividende: {r['Div affichage']}% | "
                f"Croissance CA: {r['Croissance CA %']}%"
            )
            lines.append(f"- Tags: {r['Tags']}")
            lines.append(f"- Résumé: {r['Résumé']}")
            lines.append(f"- Pourquoi: {r['Pourquoi']}\n")

        lines.append(f"> {SOFT_DISCLAIMER}\n")
        return "\n".join(lines)
