from __future__ import annotations


def build_en_texts(week_id: str) -> dict:
    return {
        "title": f"ASEAN Conveyor Demand Radar ({week_id})",
        "pages": [
            "Executive Summary: Weekly demand signals and top risks",
            "Country Demand Radar",
            "Industry Demand Change",
            "Global Risk & Disaster Impact",
            "Key News Highlights",
            "DRB Sales Implications",
            "Weekly Action List",
        ],
    }
