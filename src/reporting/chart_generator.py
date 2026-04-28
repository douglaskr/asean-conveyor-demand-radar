from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def generate_country_chart(country_df: pd.DataFrame, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "country_scores.png"
    plt.figure(figsize=(8, 4))
    top = country_df.head(10)
    plt.bar(top["country"], top["country_score"], color="#00897B")
    plt.xticks(rotation=45, ha="right")
    plt.title("Country Demand Signal")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def generate_industry_chart(industry_df: pd.DataFrame, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "industry_scores.png"
    plt.figure(figsize=(8, 4))
    top = industry_df.head(10)
    plt.bar(top["industry"], top["industry_score"], color="#1B3A57")
    plt.xticks(rotation=45, ha="right")
    plt.title("Industry Demand Change")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path
