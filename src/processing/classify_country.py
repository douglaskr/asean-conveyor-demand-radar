from __future__ import annotations

import pandas as pd


COUNTRY_ALIASES: dict[str, list[str]] = {
    "Indonesia": ["indonesia", "jakarta", "surabaya", "balikpapan", "morowali", "halmahera", "belawan", "tanjung priok"],
    "Vietnam": ["vietnam", "viet nam", "ho chi minh", "hanoi", "haiphong", "hai phong", "vung tau", "da nang"],
    "Thailand": ["thailand", "bangkok", "laem chabang", "map ta phut", "rayong", "chonburi"],
    "Malaysia": ["malaysia", "kuala lumpur", "johor", "bintulu", "port klang", "penang", "sarawak"],
    "Philippines": ["philippines", "manila", "subic", "batangas", "cebu", "mindanao", "davao"],
    "Singapore": ["singapore", "tuas", "jurong"],
    "Cambodia": ["cambodia", "phnom penh", "sihanoukville"],
    "Laos": ["laos", "lao pdr", "vientiane", "savannakhet"],
    "Myanmar": ["myanmar", "yangon", "thilawa", "mandalay"],
}


def classify_country(df: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    if df.empty:
        df["country"] = []
        return df

    enabled = {country: COUNTRY_ALIASES.get(country, [country.lower()]) for country in countries}

    def guess_country(text: str) -> str:
        lower = text.lower()
        for country, aliases in enabled.items():
            if any(alias in lower for alias in aliases):
                return country
        return "Unknown"

    out = df.copy()
    search_text = out["title"].fillna("") + " " + out.get("snippet", pd.Series("", index=out.index)).fillna("")
    out["country"] = search_text.apply(guess_country)
    return out
