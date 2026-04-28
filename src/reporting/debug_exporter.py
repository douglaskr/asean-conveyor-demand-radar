from __future__ import annotations

from pathlib import Path

import pandas as pd


def _count_by_query(df: pd.DataFrame, query_name: str) -> int:
    if df.empty or "query_name" not in df.columns:
        return 0
    return int((df["query_name"] == query_name).sum())


def build_query_summary(
    query_meta: list[dict],
    raw_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    relevant_df: pd.DataFrame,
    classified_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []
    for q in query_meta:
        qname = q["query_name"]
        raw_count = _count_by_query(raw_df, qname)
        cleaned_count = _count_by_query(cleaned_df, qname)
        relevant_count = _count_by_query(relevant_df, qname)

        if classified_df.empty:
            country_tagged_count = 0
            industry_tagged_count = 0
            risk_tagged_count = 0
        else:
            scope = classified_df[classified_df["query_name"] == qname] if "query_name" in classified_df.columns else pd.DataFrame()
            country_tagged_count = int(scope.get("country", pd.Series(dtype=str)).ne("Unknown").sum()) if not scope.empty else 0
            industry_tagged_count = int(scope.get("industry", pd.Series(dtype=str)).ne("other").sum()) if not scope.empty else 0
            risk_tagged_count = int(scope.get("risk_topic", pd.Series(dtype=str)).ne("none").sum()) if not scope.empty else 0

        notes: list[str] = []
        if raw_count == 0:
            notes.append("No raw results")
        if cleaned_count > 0 and relevant_count == 0:
            notes.append("Relevance filter removed all")
        if relevant_count > 0 and country_tagged_count == 0:
            notes.append("Country classifier tagged none")

        rows.append(
            {
                "source_type": q["source_type"],
                "query_group": q["query_group"],
                "query_name": qname,
                "query_text": q["query_text"],
                "raw_count": raw_count,
                "cleaned_count": cleaned_count,
                "relevant_count": relevant_count,
                "country_tagged_count": country_tagged_count,
                "industry_tagged_count": industry_tagged_count,
                "risk_tagged_count": risk_tagged_count,
                "notes": "; ".join(notes),
            }
        )

    return pd.DataFrame(rows)


def build_article_sample(scored_df: pd.DataFrame, top_n: int = 200) -> pd.DataFrame:
    if scored_df.empty:
        return pd.DataFrame(
            columns=[
                "title",
                "source",
                "published_date",
                "url",
                "query_name",
                "matched_keywords",
                "relevance_score",
                "assigned_country",
                "assigned_industry",
                "assigned_risk",
                "short_snippet",
            ]
        )

    sort_cols = [c for c in ["relevance", "signal_score"] if c in scored_df.columns]
    ranked = scored_df.sort_values(sort_cols, ascending=False) if sort_cols else scored_df
    sample = ranked.head(top_n).copy()

    out = pd.DataFrame(
        {
            "title": sample.get("title", ""),
            "source": sample.get("domain", ""),
            "published_date": sample.get("seendate", ""),
            "url": sample.get("url", ""),
            "query_name": sample.get("query_name", ""),
            "matched_keywords": sample.get("matched_keywords", ""),
            "relevance_score": sample.get("relevance", ""),
            "assigned_country": sample.get("country", "Unknown"),
            "assigned_industry": sample.get("industry", "other"),
            "assigned_risk": sample.get("risk_topic", "none"),
            "short_snippet": sample.get("title", "").astype(str).str.slice(0, 180),
        }
    )
    return out


def build_classification_summary(scored_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    def _value_counts(col: str, name: str) -> pd.DataFrame:
        if scored_df.empty or col not in scored_df.columns:
            return pd.DataFrame(columns=[name, "count"])
        return scored_df[col].fillna("(null)").value_counts().rename_axis(name).reset_index(name="count")

    country = _value_counts("country", "country")
    industry = _value_counts("industry", "industry")
    risk = _value_counts("risk_topic", "risk_topic")

    if scored_df.empty:
        unclassified = pd.DataFrame([{"metric": "unclassified_rows", "count": 0}])
    else:
        unknown_country = int(scored_df.get("country", pd.Series(dtype=str)).eq("Unknown").sum())
        other_industry = int(scored_df.get("industry", pd.Series(dtype=str)).eq("other").sum())
        no_risk = int(scored_df.get("risk_topic", pd.Series(dtype=str)).eq("none").sum())
        unclassified = pd.DataFrame(
            [
                {"metric": "unknown_country", "count": unknown_country},
                {"metric": "other_industry", "count": other_industry},
                {"metric": "none_risk_topic", "count": no_risk},
            ]
        )

    return {
        "country_counts": country,
        "industry_counts": industry,
        "risk_counts": risk,
        "unclassified": unclassified,
    }


def export_debug_workbooks(
    weekly_dir: Path,
    query_summary_df: pd.DataFrame,
    article_sample_df: pd.DataFrame,
    classification_tables: dict[str, pd.DataFrame],
) -> None:
    weekly_dir.mkdir(parents=True, exist_ok=True)

    query_path = weekly_dir / "debug_query_summary.xlsx"
    with pd.ExcelWriter(query_path, engine="openpyxl") as writer:
        query_summary_df.to_excel(writer, sheet_name="query_summary", index=False)

    sample_path = weekly_dir / "debug_articles_sample.xlsx"
    with pd.ExcelWriter(sample_path, engine="openpyxl") as writer:
        article_sample_df.to_excel(writer, sheet_name="articles_sample", index=False)

    class_path = weekly_dir / "debug_classification_summary.xlsx"
    with pd.ExcelWriter(class_path, engine="openpyxl") as writer:
        for name, table in classification_tables.items():
            table.to_excel(writer, sheet_name=name[:31], index=False)
