from __future__ import annotations

import traceback
from pathlib import Path

import pandas as pd
import yaml

from src.collectors.global_risk_news import GlobalRiskCollector
from src.collectors.news_gdelt import GDELTNewsCollector
from src.collectors.rss_news import RSSNewsCollector
from src.processing.classify_country import classify_country
from src.processing.classify_industry import classify_industry
from src.processing.classify_risk import classify_risk
from src.processing.clean_news import clean_news
from src.processing.deduplicate import deduplicate_articles
from src.processing.relevance_filter import filter_relevant_news
from src.reporting.chart_generator import generate_country_chart, generate_industry_chart
from src.reporting.debug_exporter import (
    build_article_sample,
    build_classification_summary,
    build_query_summary,
    export_debug_workbooks,
)
from src.reporting.excel_exporter import export_excel
from src.reporting.pdf_exporter import export_ppt_to_pdf
from src.reporting.ppt_report_en import build_ppt_en
from src.reporting.ppt_report_kr import build_ppt_kr
from src.reporting.report_text_en import build_en_texts
from src.reporting.report_text_kr import build_kr_texts
from src.scoring.country_score import aggregate_country_score
from src.scoring.demand_change_estimator import estimate_demand_pressure
from src.scoring.industry_score import aggregate_industry_score
from src.scoring.news_signal_score import compute_news_signal_score
from src.scoring.sales_priority import build_sales_priority
from src.storage.database import init_db
from src.storage.history_manager import save_weekly_scores
from src.utils.date_utils import week_id
from src.utils.file_utils import copy_to_latest, ensure_dir
from src.utils.logger import setup_logger


CONVEYOR_KEYWORDS = [
    "conveyor",
    "conveyor belt",
    "belt conveyor",
    "bulk material handling",
    "material handling",
    "coal handling",
    "ash handling",
    "crusher",
    "screening plant",
    "port conveyor",
    "mining conveyor",
]


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_rss_query_pack() -> list[dict[str, str]]:
    return [
        {"query_group": "asean_industry", "query_name": "ASEAN conveyor", "query_text": "ASEAN conveyor"},
        {"query_group": "asean_industry", "query_name": "ASEAN material handling", "query_text": "ASEAN material handling"},
        {"query_group": "asean_industry", "query_name": "ASEAN mining coal nickel", "query_text": "ASEAN mining coal nickel conveyor"},
        {"query_group": "asean_industry", "query_name": "ASEAN cement and power", "query_text": "ASEAN cement power plant coal handling"},
        {"query_group": "asean_industry", "query_name": "ASEAN port logistics", "query_text": "ASEAN port warehouse logistics bulk terminal"},
        {"query_group": "asean_industry", "query_name": "ASEAN food palm oil processing", "query_text": "ASEAN palm oil food processing conveyor"},
        {"query_group": "global_risk", "query_name": "Shipping disruption", "query_text": "shipping disruption red sea suez port congestion"},
        {"query_group": "global_risk", "query_name": "Commodity and energy shock", "query_text": "commodity shock energy shock oil LNG coal price"},
    ]


def run_pipeline() -> None:
    logger = setup_logger()
    wid = week_id()
    weekly_dir = ensure_dir(Path("outputs") / "weekly" / wid)
    latest_dir = Path("outputs/latest")

    countries_cfg = load_yaml("config/countries.yaml")
    industries_cfg = load_yaml("config/industries.yaml")
    risks_cfg = load_yaml("config/global_risks.yaml")
    weights_cfg = load_yaml("config/scoring_weights.yaml")
    product_cfg = load_yaml("config/product_mapping.yaml")
    report_cfg = load_yaml("config/report_settings.yaml")

    collection_mode = report_cfg.get("collection_mode", "rss")
    validation_mode = report_cfg.get("validation_mode", "rss_preferred")
    logger.info("Weekly run started for %s (collection_mode=%s, validation_mode=%s)", wid, collection_mode, validation_mode)
    init_db()

    query_meta: list[dict] = []
    news_df = pd.DataFrame()
    risk_df = pd.DataFrame()

    use_rss_primary = collection_mode == "rss" or validation_mode in {"rss_only", "rss_preferred", "gdelt_optional"}
    if use_rss_primary:
        try:
            rss_queries = build_rss_query_pack()
            query_meta.extend({"source_type": "rss", **q} for q in rss_queries)
            rss_df = RSSNewsCollector().fetch_query_pack(rss_queries)
            news_df = rss_df[rss_df["query_group"] == "asean_industry"].copy() if not rss_df.empty else pd.DataFrame()
            risk_df = rss_df[rss_df["query_group"] == "global_risk"].copy() if not rss_df.empty else pd.DataFrame()
            logger.info("Collected RSS news (industry=%d, risk=%d)", len(news_df), len(risk_df))
        except Exception as exc:
            logger.error("RSS collection failed: %s", exc)
            logger.debug(traceback.format_exc())

    # Optional only: GDELT can support RSS runs but must not be the primary source.
    should_try_gdelt = (
        report_cfg.get("enable_gdelt_fallback", True)
        and validation_mode in {"rss_preferred", "gdelt_optional"}
        and (news_df.empty and risk_df.empty)
    )
    if should_try_gdelt:
        logger.warning("Using GDELT fallback collection due to empty RSS results or gdelt_only mode.")
        try:
            collector = GDELTNewsCollector()
            asean_country_query = "(" + " OR ".join([f'"{c}"' for c in countries_cfg["countries"]]) + ")"
            conveyor_query = "(" + " OR ".join([f'"{k}"' for k in CONVEYOR_KEYWORDS]) + ")"
            query = f"{asean_country_query} AND {conveyor_query}"
            query_meta.append({"source_type": "gdelt", "query_group": "asean_industry", "query_name": "ASEAN Conveyor Core Query", "query_text": query})
            gdelt_news = collector.fetch(query)
            if not gdelt_news.empty:
                gdelt_news["source_type"] = "gdelt"
                gdelt_news["query_group"] = "asean_industry"
                gdelt_news["query_name"] = "ASEAN Conveyor Core Query"
                gdelt_news["query_text"] = query
            news_df = pd.concat([news_df, gdelt_news], ignore_index=True) if not gdelt_news.empty else news_df

            for topic in risks_cfg["global_risks"]:
                query_meta.append({"source_type": "gdelt", "query_group": "global_risk", "query_name": topic["name"], "query_text": " OR ".join(topic.get("keywords", []))})
            gdelt_risk = GlobalRiskCollector(GDELTNewsCollector()).fetch_by_topics(risks_cfg["global_risks"])
            risk_df = pd.concat([risk_df, gdelt_risk], ignore_index=True) if not gdelt_risk.empty else risk_df
            logger.info("Collected GDELT fallback news (industry=%d, risk=%d)", len(news_df), len(risk_df))
        except Exception as exc:
            logger.error("GDELT fallback failed: %s", exc)
            logger.debug(traceback.format_exc())

    all_news = pd.concat([news_df, risk_df], ignore_index=True) if not news_df.empty or not risk_df.empty else pd.DataFrame(columns=["title", "url"])

    cleaned = pd.DataFrame()
    deduped = pd.DataFrame()
    relevant = pd.DataFrame()

    try:
        expanded_keywords = set(CONVEYOR_KEYWORDS)
        for icfg in industries_cfg["industries"].values():
            expanded_keywords.update(icfg.get("keywords", []))
        for rcfg in risks_cfg["global_risks"]:
            expanded_keywords.update(rcfg.get("keywords", []))

        cleaned = clean_news(all_news)
        deduped = deduplicate_articles(cleaned)
        relevant = filter_relevant_news(deduped, list(expanded_keywords), min_relevance_score=1)
        classified = classify_country(relevant, countries_cfg["countries"])
        classified = classify_industry(classified, industries_cfg["industries"])
        classified = classify_risk(classified, risks_cfg["global_risks"])
        scored_news = compute_news_signal_score(classified, weights_cfg)
        logger.info("Processing complete. Relevant articles: %d", len(scored_news))
    except Exception as exc:
        logger.error("Processing/scoring failed: %s", exc)
        logger.debug(traceback.format_exc())
        scored_news = pd.DataFrame(columns=["country", "industry", "signal_score", "url", "title", "risk_topic"])

    country_scores = aggregate_country_score(scored_news)
    industry_scores = aggregate_industry_score(scored_news)
    demand_pressure = estimate_demand_pressure(country_scores, industry_scores)
    sales_priority = build_sales_priority(demand_pressure, product_cfg["product_mapping"])

    try:
        save_weekly_scores(wid, demand_pressure)
    except Exception as exc:
        logger.error("Saving weekly history failed: %s", exc)

    try:
        excel_path = export_excel(
            weekly_dir / f"asean_conveyor_radar_{wid}.xlsx",
            {
                "news_scored": scored_news,
                "country_scores": country_scores,
                "industry_scores": industry_scores,
                "demand_pressure": demand_pressure,
                "sales_priority": sales_priority,
            },
        )
        logger.info("Excel exported: %s", excel_path)
    except Exception as exc:
        logger.error("Excel export failed: %s", exc)

    charts: dict[str, Path] = {}
    try:
        charts["country"] = generate_country_chart(country_scores, weekly_dir)
        charts["industry"] = generate_industry_chart(industry_scores, weekly_dir)
    except Exception as exc:
        logger.error("Chart generation failed: %s", exc)

    try:
        kr_ppt = build_ppt_kr(build_kr_texts(wid), charts, weekly_dir / f"asean_conveyor_radar_{wid}_KR.pptx")
        en_ppt = build_ppt_en(build_en_texts(wid), charts, weekly_dir / f"asean_conveyor_radar_{wid}_EN.pptx")
        logger.info("PPT exported: %s, %s", kr_ppt.name, en_ppt.name)

        for p in [kr_ppt, en_ppt]:
            ok, msg = export_ppt_to_pdf(p, weekly_dir / (p.stem + ".pdf"))
            if ok:
                logger.info("%s -> PDF done", p.name)
            else:
                logger.warning("%s -> %s", p.name, msg)
    except Exception as exc:
        logger.error("PPT/PDF generation failed: %s", exc)

    try:
        query_summary = build_query_summary(
            query_meta=query_meta,
            raw_df=all_news,
            cleaned_df=cleaned,
            relevant_df=relevant,
            classified_df=scored_news,
        )
        article_sample = build_article_sample(scored_news)
        class_summary = build_classification_summary(scored_news)
        export_debug_workbooks(weekly_dir, query_summary, article_sample, class_summary)
        logger.info("Debug workbooks exported for diagnostics")
    except Exception as exc:
        logger.error("Debug export failed: %s", exc)

    try:
        copy_to_latest(weekly_dir, latest_dir)
    except Exception as exc:
        logger.error("Copy to latest failed: %s", exc)

    logger.info("Weekly run finished for %s", wid)


if __name__ == "__main__":
    run_pipeline()
