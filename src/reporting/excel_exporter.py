from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_excel(output_path: Path, tables: dict[str, pd.DataFrame]) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return output_path
