import json
from pathlib import Path
from xml.etree import ElementTree as ET

from src.compiler import compile_svg

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "button_sf.json"


def load_asset() -> dict:
    with EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_compiler_outputs_groups_and_rects():
    asset = load_asset()
    svg = compile_svg(asset)
    root = ET.fromstring(svg)

    ns = {"svg": "http://www.w3.org/2000/svg"}
    groups = root.findall("svg:g", ns)
    assert groups

    expected_ids = {layer["id"] for layer in asset["layers"]}
    group_ids = {group.attrib.get("id") for group in groups}
    assert expected_ids == group_ids

    for group in groups:
        rect = group.find("svg:rect", ns)
        text = group.find("svg:text", ns)
        assert rect is not None or text is not None


def test_compiler_emits_glow_filter():
    asset = load_asset()
    svg = compile_svg(asset)
    root = ET.fromstring(svg)

    ns = {"svg": "http://www.w3.org/2000/svg"}
    defs = root.find("svg:defs", ns)
    assert defs is not None

    glow_filter = defs.find("svg:filter[@id='ui-softGlow']", ns)
    assert glow_filter is not None
