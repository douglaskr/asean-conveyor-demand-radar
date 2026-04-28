from __future__ import annotations

import pandas as pd


def _signal_label(article_count: int) -> str:
    if article_count >= 40:
        return "signal-rich"
    if article_count >= 15:
        return "moderate"
    return "signal-light"


def _top(df: pd.DataFrame, name_col: str, score_col: str, n: int = 5) -> list[str]:
    if df.empty or name_col not in df.columns:
        return []
    out: list[str] = []
    for _, r in df.head(n).iterrows():
        score = float(r.get(score_col, 0.0))
        out.append(f"{r.get(name_col, 'N/A')} ({score:.2f})")
    return out


def _why_it_matters(row: pd.Series) -> str:
    country = row.get("country", "Unknown")
    industry = row.get("industry", "other")
    risk = row.get("risk_topic", "none")
    if risk != "none":
        return f"Risk-linked signal for {country}/{industry}; monitor disruption exposure."
    return f"Demand-related signal for {country}/{industry}; validate project-level opportunity."


def build_en_texts(
    week_id: str,
    scored_news: pd.DataFrame,
    country_scores: pd.DataFrame,
    industry_scores: pd.DataFrame,
    demand_pressure: pd.DataFrame,
    sales_priority: pd.DataFrame,
) -> dict:
    article_count = len(scored_news)
    signal_state = _signal_label(article_count)

    top_countries = _top(country_scores, "country", "country_score", 4)
    top_industries = _top(industry_scores, "industry", "industry_score", 5)

    # Slide 1
    s1 = [
        f"- Relevant article count: {article_count}",
        f"- Weekly signal condition: {signal_state}",
        f"- Top countries: {', '.join(top_countries[:3]) if top_countries else 'No strong country leader'}",
        f"- Top industries: {', '.join(top_industries[:3]) if top_industries else 'No strong industry leader'}",
        "- Interpretation: treat this as directional validation, not a final demand forecast.",
    ]

    # Slide 2
    if not top_countries:
        s2 = [
            "Country signals were weak this week.",
            "- No clear country-level concentration was confirmed.",
            "- Continue monitoring port/logistics and project news by country alias.",
        ]
    else:
        s2 = [
            "Country-level signals show early concentration in selected markets.",
            *[f"- {c}" for c in top_countries[:4]],
            "- Confidence remains moderate until multi-week repetition is confirmed.",
        ]

    # Slide 3
    if not top_industries:
        s3 = [
            "Industry signals were thin this week.",
            "- No strong sector direction was confirmed.",
            "- Keep monitoring mining/power/logistics terms for next-week accumulation.",
        ]
    else:
        s3 = [
            "Industry direction shows where the strongest weekly attention appeared.",
            *[f"- {i}" for i in top_industries[:5]],
        ]

    # Slide 4
    risk_df = scored_news[scored_news.get("risk_topic", "none") != "none"] if not scored_news.empty else pd.DataFrame()
    if risk_df.empty:
        s4 = [
            "Risk signal was limited this week, so disruption interpretation is low-confidence.",
            "- No dominant global risk cluster was confirmed.",
            "- Still track shipping and energy headlines for sudden changes.",
        ]
    else:
        top_risk = risk_df["risk_topic"].value_counts().head(4)
        s4 = ["Global risk signals were present and should be monitored for cost/lead-time impact."]
        s4 += [f"- {k}: {v} articles" for k, v in top_risk.items()]

    # Slide 5
    highlights: list[str] = []
    if not scored_news.empty:
        for _, r in scored_news.sort_values("signal_score", ascending=False).head(5).iterrows():
            title = r.get("title", "No title")
            source = r.get("domain", "Unknown source")
            highlights.append(f"- {title} | {source}")
            highlights.append(f"  why it matters: {_why_it_matters(r)}")
    if not highlights:
        highlights = ["- No high-confidence article highlight this week.", "  why it matters: signal quality is too thin for directional conclusion."]

    # Slide 6
    s6: list[str] = []
    if not demand_pressure.empty:
        for _, r in demand_pressure.head(3).iterrows():
            s6.append(f"- Monitor {r['country']}/{r['industry']} as near-term sales watchlist.")
    if not industry_scores.empty:
        s6.append(f"- Validate top-industry demand shift: {', '.join(top_industries[:2]) if top_industries else 'N/A'}.")
    if not sales_priority.empty:
        for _, r in sales_priority.head(2).iterrows():
            s6.append(f"- Review product fit for {r['country']}/{r['industry']}: {r.get('recommended_products', '')}.")
    if not s6:
        s6 = [
            "- Signals were limited; keep sales implications monitoring-oriented this week.",
            "- Avoid aggressive commitment until stronger repeated evidence appears.",
        ]

    # Slide 7
    s7 = [
        "- Monitor top-country headlines daily and update country confidence next week.",
        "- Validate top two industry signals with distributor/project checks.",
        "- Compare this week vs prior week article volume and score concentration.",
        "- Track shipping/energy risk headlines for quote lead-time impact.",
    ]
    if not sales_priority.empty:
        s7.append("- Review and update DRB opportunity list using this week's priority clusters.")

    return {
        "title": f"ASEAN Conveyor Demand Radar ({week_id})",
        "pages": [
            "Executive Summary",
            "Country Demand Radar",
            "Industry Demand Change",
            "Global Risk & Disaster Impact",
            "Key News Highlights",
            "DRB Sales Implications",
            "Weekly Action List",
        ],
        "summaries": [
            "\n".join(s1[:5]),
            "\n".join(s2[:5]),
            "\n".join(s3[:6]),
            "\n".join(s4[:5]),
            "\n".join(highlights[:10]),
            "\n".join(s6[:5]),
            "\n".join(s7[:6]),
        ],
    }
