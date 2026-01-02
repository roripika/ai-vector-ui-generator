import json
from pathlib import Path
from xml.etree import ElementTree as ET

from src.compiler import compile_svg
from src.validator import validate_asset

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "screen_dialog.json"


def load_asset() -> dict:
    with EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_screen_example_validates():
    asset = load_asset()
    validate_asset(asset)


def test_screen_compiles_with_canvas_viewbox():
    asset = load_asset()
    svg = compile_svg(asset)
    root = ET.fromstring(svg)
    assert root.attrib.get("viewBox") == "0 0 1280 720"
