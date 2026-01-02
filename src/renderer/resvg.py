"""resvg CLI renderer for SVG → PNG."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional


def export_png(svg_path: Path, png_path: Path, width: Optional[int] = None, height: Optional[int] = None) -> None:
    """Export SVG to PNG using resvg CLI."""
    svg_path = Path(svg_path)
    png_path = Path(png_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    args = [_resvg_binary(), str(svg_path), str(png_path)]
    if width:
        args.extend(["--width", str(int(width))])
    if height:
        args.extend(["--height", str(int(height))])

    subprocess.run(args, check=True)


def _resvg_binary() -> str:
    binary = shutil.which("resvg")
    if not binary:
        raise RuntimeError("resvg was not found in PATH. Install it to enable rendering.")
    return binary


__all__ = ["export_png"]
