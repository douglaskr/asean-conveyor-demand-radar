from __future__ import annotations

import pandas as pd


def _top_items(df: pd.DataFrame, key_col: str, score_col: str, n: int = 3) -> str:
    if df.empty or key_col not in df.columns:
        return "N/A"
    cols = [key_col] + ([score_col] if score_col in df.columns else [])
    items = []
    for _, row in df.head(n)[cols].iterrows():
        label = str(row[key_col])
        if score_col in row.index:
            label = f"{label} ({float(row[score_col]):.2f})"
        items.append(label)
    return ", ".join(items) if items else "N/A"


def build_en_texts(
    week_id: str,
    scored_news: pd.DataFrame,
    country_scores: pd.DataFrame,
    industry_scores: pd.DataFrame,
    demand_pressure: pd.DataFrame,
    sales_priority: pd.DataFrame,
) -> dict:
    article_count = len(scored_news)
    top_countries = _top_items(country_scores, "country", "country_score", 3)
    top_industries = _top_items(industry_scores, "industry", "industry_score", 3)

    risk_df = scored_news[scored_news.get("risk_topic", "none") != "none"] if not scored_news.empty else pd.DataFrame()
    if risk_df.empty:
        risk_summary = "Risk signal was low this week; no dominant global disruption theme was detected in collected articles."
    else:
        top_risks = risk_df["risk_topic"].value_counts().head(3)
        risk_summary = "Top risk topics: " + ", ".join([f"{k} ({v})" for k, v in top_risks.items()])

    highlights = []
    if not scored_news.empty:
        for _, row in scored_news.sort_values("signal_score", ascending=False).head(5).iterrows():
            highlights.append(f"- {row.get('title', 'No title')} ({row.get('country', 'Unknown')}/{row.get('industry', 'other')})")
    if not highlights:
        highlights = ["- No high-confidence highlight article this week."]

    sales_lines = []
    if not sales_priority.empty:
        for _, row in sales_priority.head(5).iterrows():
            sales_lines.append(
                f"- {row.get('country', 'Unknown')} / {row.get('industry', 'other')}: {row.get('recommended_products', '')}"
            )
    else:
        sales_lines = ["- No priority cluster reached action threshold this week. Monitor next-week signal build-up."]

    action_lines = [
        "- Recheck top-country project pipeline and distributor activity for confirmed demand pockets.",
        "- Validate top-industry replacement cycle opportunities from identified highlight articles.",
        "- Track shipping and energy shocks for lead-time and pricing impact on sales quotes.",
    ]
    if not demand_pressure.empty:
        strongest = demand_pressure.head(3)
        action_lines.append(
            "- Focus weekly outreach on: "
            + ", ".join([f"{r['country']}/{r['industry']}" for _, r in strongest.iterrows()])
            + "."
        )

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
            f"Collected {article_count} relevant articles. Top countries: {top_countries}. Top industries: {top_industries}.",
            f"Country signal leaders: {top_countries}. Confidence improves as repeated country aliases and project mentions increase.",
            f"Industry demand direction is led by: {top_industries}. Compare with prior week for acceleration/deceleration.",
            risk_summary,
            "\n".join(highlights),
            "\n".join(sales_lines),
            "\n".join(action_lines[:5]),
        ],
    }
