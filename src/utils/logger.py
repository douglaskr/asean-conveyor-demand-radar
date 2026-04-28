from __future__ import annotations

import logging
from pathlib import Path


def setup_logger(log_path: str = "logs/weekly_run.log") -> logging.Logger:
    """Create a reusable logger for the weekly pipeline."""
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("asean_conveyor_radar")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    return logger
