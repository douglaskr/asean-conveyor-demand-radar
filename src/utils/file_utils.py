from __future__ import annotations

import shutil
from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def copy_to_latest(weekly_dir: Path, latest_dir: Path) -> None:
    ensure_dir(latest_dir)
    for f in weekly_dir.glob("*"):
        if f.is_file():
            shutil.copy2(f, latest_dir / f.name)
