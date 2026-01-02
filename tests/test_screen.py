import json
from pathlib import Path
from xml.etree import ElementTree as ET

from src.compiler import compile_svg
from src.validator import validate_asset

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "screen_dialog.json"
LIST_EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "list_screen.json"
GRID_EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "grid_screen.json"


def load_asset() -> dict:
    with EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_list_asset() -> dict:
    with LIST_EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_grid_asset() -> dict:
    with GRID_EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_screen_example_validates():
    asset = load_asset()
    validate_asset(asset)

    list_asset = load_list_asset()
    validate_asset(list_asset)

    grid_asset = load_grid_asset()
    validate_asset(grid_asset)


def test_screen_compiles_with_canvas_viewbox():
    asset = load_asset()
    svg = compile_svg(asset)
    root = ET.fromstring(svg)
    assert root.attrib.get("viewBox") == "0 0 1280 720"

    list_svg = compile_svg(load_list_asset())
    list_root = ET.fromstring(list_svg)
    assert list_root.attrib.get("viewBox") == "0 0 1280 720"

    grid_svg = compile_svg(load_grid_asset())
    grid_root = ET.fromstring(grid_svg)
    assert grid_root.attrib.get("viewBox") == "0 0 1280 720"
