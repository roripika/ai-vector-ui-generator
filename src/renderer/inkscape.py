"""Inkscape CLI renderer for SVG → PNG/PDF."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

DEFAULT_TIMEOUT_SECONDS = 120


def export_png(
    svg_path: Path,
    png_path: Path,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> None:
    """Export SVG to PNG using Inkscape CLI."""
    svg_path = Path(svg_path)
    png_path = Path(png_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    args = [
        _inkscape_binary(),
        str(svg_path),
        "--export-type=png",
        f"--export-filename={png_path}",
        "--export-area-page",
    ]
    if width:
        args.append(f"--export-width={int(width)}")
    if height:
        args.append(f"--export-height={int(height)}")

    _run_inkscape(args)


def export_pdf(svg_path: Path, pdf_path: Path) -> None:
    """Export SVG to PDF using Inkscape CLI."""
    svg_path = Path(svg_path)
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    args = [
        _inkscape_binary(),
        str(svg_path),
        "--export-type=pdf",
        f"--export-filename={pdf_path}",
        "--export-area-page",
    ]
    _run_inkscape(args)


def _inkscape_binary() -> str:
    binary = shutil.which("inkscape")
    if not binary:
        raise RuntimeError("Inkscape was not found in PATH. Install it to enable rendering.")
    return binary


def _run_inkscape(args: list[str]) -> None:
    try:
        subprocess.run(args, check=True, timeout=DEFAULT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Inkscape timed out. Launch the GUI once to finish initial setup and retry."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Inkscape failed with exit code {exc.returncode}.") from exc


__all__ = ["export_png", "export_pdf"]
