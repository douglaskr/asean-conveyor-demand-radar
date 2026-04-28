from __future__ import annotations


def build_kr_texts(week_id: str) -> dict:
    return {
        "title": f"ASEAN 컨베이어 수요 레이더 ({week_id})",
        "pages": [
            "핵심 요약: 이번 주 수요 신호 및 주요 위험 요인",
            "국가별 수요 레이더",
            "산업별 수요 변화",
            "글로벌 리스크/재난 영향",
            "핵심 뉴스 하이라이트",
            "DRB 영업 시사점",
            "주간 실행 액션 리스트",
        ],
    }
