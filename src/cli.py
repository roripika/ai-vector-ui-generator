"""CLI entry point for the MVP pipeline."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from src.compiler import compile_svg
from src.renderer import (
    inkscape_export_pdf,
    inkscape_export_png,
    resvg_export_png,
)
from src.validator import ValidationError, validate_asset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Vector UI Generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="validate → svg → png/pdf")
    render_parser.add_argument("--in", dest="input_path", required=True, type=Path)
    render_parser.add_argument("--out", dest="output_dir", required=True, type=Path)
    render_parser.add_argument(
        "--only",
        choices=["svg", "png", "pdf"],
        help="Generate only a single output type",
    )
    render_parser.add_argument(
        "--size",
        help="PNG export size as WIDTHxHEIGHT (e.g. 512x128)",
    )
    render_parser.add_argument(
        "--backend",
        choices=["inkscape", "resvg"],
        default="inkscape",
        help="Renderer backend for PNG export",
    )
    render_parser.set_defaults(func=cmd_render)

    return parser


def cmd_render(args: argparse.Namespace) -> int:
    asset = _load_json(args.input_path)
    try:
        validate_asset(asset)
    except ValidationError as exc:
        print(str(exc))
        return 1

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input_path.stem

    size = _parse_size(args.size)
    backend = args.backend

    png_exporter = inkscape_export_png if backend == "inkscape" else resvg_export_png
    pdf_exporter = inkscape_export_pdf if backend == "inkscape" else None

    if args.only == "svg" or args.only is None:
        svg_path = output_dir / f"{stem}.svg"
        svg_path.write_text(compile_svg(asset), encoding="utf-8")
    else:
        svg_path = None

    if args.only is None:
        svg_source = output_dir / f"{stem}.svg"
        png_exporter(svg_source, output_dir / f"{stem}.png", width=size[0], height=size[1])
        print(f"OK: {svg_source} {output_dir / f'{stem}.png'}")
        return 0

    if args.only == "svg":
        print(f"OK: {output_dir / f'{stem}.svg'}")
        return 0

    if args.only == "pdf" and pdf_exporter is None:
        raise SystemExit("PDF export requires --backend inkscape.")

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(compile_svg(asset).encode("utf-8"))

    try:
        if args.only == "png":
            png_exporter(tmp_path, output_dir / f"{stem}.png", width=size[0], height=size[1])
            print(f"OK: {output_dir / f'{stem}.png'}")
        elif args.only == "pdf":
            pdf_exporter(tmp_path, output_dir / f"{stem}.pdf")
            print(f"OK: {output_dir / f'{stem}.pdf'}")
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass

    return 0


def _load_json(path: Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_size(size_text: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not size_text:
        return None, None
    parts = size_text.lower().split("x")
    if len(parts) != 2:
        raise SystemExit("--size must be WIDTHxHEIGHT")
    width, height = parts
    if not width.isdigit() or not height.isdigit():
        raise SystemExit("--size must be WIDTHxHEIGHT")
    return int(width), int(height)


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
