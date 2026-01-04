import json
from pathlib import Path
from xml.etree import ElementTree as ET

from src.compiler import compile_svg
from src.validator import validate_asset

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "button_theme.json"


def load_asset() -> dict:
    with EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_theme_overrides_apply_to_text():
    asset = load_asset()
    validate_asset(asset)

    svg = compile_svg(asset)
    root = ET.fromstring(svg)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    text = root.find(".//svg:text", ns)
    assert text is not None
    assert text.attrib.get("fill") == "#FBE5A6"
    assert text.attrib.get("font-family") == "Georgia"
