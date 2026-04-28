from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def export_ppt_to_pdf(ppt_path: Path, pdf_path: Path) -> tuple[bool, str]:
    """Try LibreOffice conversion first; return gracefully if not available."""
    soffice = shutil.which("soffice")
    if not soffice:
        return False, "LibreOffice (soffice) not found; skipped PDF export."

    cmd = [soffice, "--headless", "--convert-to", "pdf", str(ppt_path), "--outdir", str(pdf_path.parent)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"PDF export failed: {result.stderr.strip()}"
    return True, "PDF exported successfully."
