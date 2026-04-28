from __future__ import annotations

import pandas as pd


def _top_items(df: pd.DataFrame, key_col: str, score_col: str, n: int = 3) -> str:
    if df.empty or key_col not in df.columns:
        return "해당 없음"
    cols = [key_col] + ([score_col] if score_col in df.columns else [])
    items = []
    for _, row in df.head(n)[cols].iterrows():
        label = str(row[key_col])
        if score_col in row.index:
            label = f"{label} ({float(row[score_col]):.2f})"
        items.append(label)
    return ", ".join(items) if items else "해당 없음"


def build_kr_texts(
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
        risk_summary = "이번 주 글로벌 리스크 신호는 낮은 수준이며, 지배적인 충격 이슈는 확인되지 않았습니다."
    else:
        top_risks = risk_df["risk_topic"].value_counts().head(3)
        risk_summary = "주요 리스크 토픽: " + ", ".join([f"{k} ({v})" for k, v in top_risks.items()])

    highlights = []
    if not scored_news.empty:
        for _, row in scored_news.sort_values("signal_score", ascending=False).head(5).iterrows():
            highlights.append(f"- {row.get('title', '제목 없음')} ({row.get('country', 'Unknown')}/{row.get('industry', 'other')})")
    if not highlights:
        highlights = ["- 이번 주 고신뢰 하이라이트 뉴스가 부족합니다."]

    sales_lines = []
    if not sales_priority.empty:
        for _, row in sales_priority.head(5).iterrows():
            sales_lines.append(
                f"- {row.get('country', 'Unknown')} / {row.get('industry', 'other')}: 추천 제품 {row.get('recommended_products', '')}"
            )
    else:
        sales_lines = ["- 우선 영업 대상 클러스터가 제한적입니다. 다음 주 신호 누적을 모니터링하십시오."]

    action_lines = [
        "- 상위 국가 중심으로 프로젝트 파이프라인/딜러 반응을 재점검하십시오.",
        "- 상위 산업군에서 교체수요/신설수요 기회를 영업 이슈로 분류하십시오.",
        "- 해상물류 및 에너지 가격 리스크가 견적 리드타임/원가에 미치는 영향을 추적하십시오.",
    ]
    if not demand_pressure.empty:
        strongest = demand_pressure.head(3)
        action_lines.append(
            "- 주간 집중 공략 대상: " + ", ".join([f"{r['country']}/{r['industry']}" for _, r in strongest.iterrows()]) + "."
        )

    return {
        "title": f"ASEAN 컨베이어 수요 레이더 ({week_id})",
        "pages": [
            "Executive Summary",
            "국가별 수요 레이더",
            "산업별 수요 변화",
            "글로벌 리스크/재난 영향",
            "핵심 뉴스 하이라이트",
            "DRB 영업 시사점",
            "주간 실행 액션 리스트",
        ],
        "summaries": [
            f"이번 주 관련 기사 {article_count}건을 수집했습니다. 상위 국가: {top_countries}. 상위 산업: {top_industries}.",
            f"국가별 선행 신호 상위: {top_countries}. 동일 국가에서 반복 기사/프로젝트 언급이 증가할수록 신뢰도가 높아집니다.",
            f"산업별 수요 방향 상위: {top_industries}. 전주 대비 가속/둔화 여부를 함께 점검하십시오.",
            risk_summary,
            "\n".join(highlights),
            "\n".join(sales_lines),
            "\n".join(action_lines[:5]),
        ],
    }
