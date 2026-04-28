from __future__ import annotations

import pandas as pd


def _signal_label(article_count: int) -> str:
    if article_count >= 40:
        return "신호 풍부"
    if article_count >= 15:
        return "보통"
    return "신호 약함"


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
        return f"{country}/{industry} 관련 리스크 연계 신호로, 공급/물류 영향 모니터링이 필요합니다."
    return f"{country}/{industry} 관련 수요 신호로, 프로젝트성 기회 검증이 필요합니다."


def build_kr_texts(
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

    s1 = [
        f"- 관련 기사 수: {article_count}건",
        f"- 주간 신호 상태: {signal_state}",
        f"- 상위 국가: {', '.join(top_countries[:3]) if top_countries else '국가 신호 약함'}",
        f"- 상위 산업: {', '.join(top_industries[:3]) if top_industries else '산업 신호 약함'}",
        "- 종합 해석: 이번 주 결과는 방향성 점검용으로 활용하고, 확정 판단은 보수적으로 유지하십시오.",
    ]

    if not top_countries:
        s2 = [
            "국가별 신호 강도가 낮은 주간입니다.",
            "- 뚜렷한 국가 집중 패턴이 확인되지 않았습니다.",
            "- 항만/물류 및 프로젝트 기사 누적 여부를 다음 주 재검증하십시오.",
        ]
    else:
        s2 = [
            "국가별 수요 신호가 일부 시장에 집중되는 초기 패턴이 보입니다.",
            *[f"- {c}" for c in top_countries[:4]],
            "- 반복 신호가 2~3주 누적되면 신뢰도를 상향하십시오.",
        ]

    if not top_industries:
        s3 = [
            "산업 신호가 얇아 방향성 해석은 예비 수준입니다.",
            "- 강한 산업 리더가 확인되지 않았습니다.",
            "- 광산/전력/물류 키워드의 다음 주 누적을 비교하십시오.",
        ]
    else:
        s3 = [
            "산업별로는 다음 영역에서 상대적으로 강한 관심이 확인되었습니다.",
            *[f"- {i}" for i in top_industries[:5]],
        ]

    risk_df = scored_news[scored_news.get("risk_topic", "none") != "none"] if not scored_news.empty else pd.DataFrame()
    if risk_df.empty:
        s4 = [
            "이번 주 글로벌 리스크 신호는 제한적이며, 해석 신뢰도는 낮은 편입니다.",
            "- 지배적인 위험 토픽이 확인되지 않았습니다.",
            "- 단, 해상운임/에너지 가격 뉴스는 지속 추적이 필요합니다.",
        ]
    else:
        top_risk = risk_df["risk_topic"].value_counts().head(4)
        s4 = ["글로벌 리스크 신호가 일부 확인되어 비용/리드타임 영향 점검이 필요합니다."]
        s4 += [f"- {k}: {v}건" for k, v in top_risk.items()]

    highlights: list[str] = []
    if not scored_news.empty:
        for _, r in scored_news.sort_values("signal_score", ascending=False).head(5).iterrows():
            title = r.get("title", "제목 없음")
            source = r.get("domain", "출처 미상")
            highlights.append(f"- {title} | {source}")
            highlights.append(f"  시사점: {_why_it_matters(r)}")
    if not highlights:
        highlights = ["- 고신뢰 하이라이트 기사 부족", "  시사점: 주간 신호가 얇아 방향성 결론은 유보가 필요합니다."]

    s6: list[str] = []
    if not demand_pressure.empty:
        for _, r in demand_pressure.head(3).iterrows():
            s6.append(f"- {r['country']}/{r['industry']}를 단기 영업 모니터링 대상으로 유지하십시오.")
    if not industry_scores.empty:
        s6.append(f"- 상위 산업 수요 변화를 검증하십시오: {', '.join(top_industries[:2]) if top_industries else 'N/A'}")
    if not sales_priority.empty:
        for _, r in sales_priority.head(2).iterrows():
            s6.append(f"- {r['country']}/{r['industry']} 제품 적합성 검토: {r.get('recommended_products', '')}")
    if not s6:
        s6 = [
            "- 영업 시사점은 보수적으로 해석하십시오(신호 부족 주간).",
            "- 공격적 가정보다는 모니터링/검증 중심 운영이 적절합니다.",
        ]

    s7 = [
        "- 상위 국가 뉴스 흐름을 모니터링하고 다음 주 confidence를 업데이트하십시오.",
        "- 상위 2개 산업 신호를 딜러/프로젝트 정보로 검증하십시오.",
        "- 전주 대비 기사 수와 점수 집중도를 비교하십시오.",
        "- 해상물류/에너지 리스크를 추적해 견적 리드타임 가정을 리뷰하십시오.",
    ]
    if not sales_priority.empty:
        s7.append("- 이번 주 우선 클러스터 기준으로 기회리스트를 업데이트하십시오.")

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
            "\n".join(s1[:5]),
            "\n".join(s2[:5]),
            "\n".join(s3[:6]),
            "\n".join(s4[:5]),
            "\n".join(highlights[:10]),
            "\n".join(s6[:5]),
            "\n".join(s7[:6]),
        ],
    }
