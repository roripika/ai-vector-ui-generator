import json
from pathlib import Path
from xml.etree import ElementTree as ET

from src.compiler import compile_svg
from src.validator import validate_asset

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "screen_dialog.json"
LIST_EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "list_screen.json"
GRID_EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "grid_screen.json"
HUD_EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "hud_basic.json"
HUD_MOCK_EXAMPLE_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "hud_basic.mock.json"
)
PRIMARY_BUTTON_PATH = Path(__file__).resolve().parents[1] / "examples" / "primary_action_states.json"
MODAL_PATH = Path(__file__).resolve().parents[1] / "examples" / "modal_overlay.json"
TAB_BAR_PATH = Path(__file__).resolve().parents[1] / "examples" / "tab_bar.json"
INFO_PANEL_PATH = Path(__file__).resolve().parents[1] / "examples" / "info_panel.json"
TOAST_PATH = Path(__file__).resolve().parents[1] / "examples" / "toast_feedback.json"
CUSTOM_FX_PATH = Path(__file__).resolve().parents[1] / "examples" / "custom_fx_glow.json"
GAUGE_RADIAL_PATH = Path(__file__).resolve().parents[1] / "examples" / "gauge_radial_polygon.json"
GAUGE_SEGMENTED_PATH = Path(__file__).resolve().parents[1] / "examples" / "gauge_segmented.json"


def load_asset() -> dict:
    with EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_list_asset() -> dict:
    with LIST_EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_grid_asset() -> dict:
    with GRID_EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_hud_asset() -> dict:
    with HUD_EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_hud_mock_asset() -> dict:
    with HUD_MOCK_EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_primary_button_asset() -> dict:
    with PRIMARY_BUTTON_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_modal_asset() -> dict:
    with MODAL_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_tab_bar_asset() -> dict:
    with TAB_BAR_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_info_panel_asset() -> dict:
    with INFO_PANEL_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_toast_asset() -> dict:
    with TOAST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_custom_fx_asset() -> dict:
    with CUSTOM_FX_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_gauge_radial_asset() -> dict:
    with GAUGE_RADIAL_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_gauge_segmented_asset() -> dict:
    with GAUGE_SEGMENTED_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_screen_example_validates():
    asset = load_asset()
    validate_asset(asset)

    list_asset = load_list_asset()
    validate_asset(list_asset)

    grid_asset = load_grid_asset()
    validate_asset(grid_asset)

    hud_asset = load_hud_asset()
    validate_asset(hud_asset)

    hud_mock_asset = load_hud_mock_asset()
    validate_asset(hud_mock_asset)

    validate_asset(load_primary_button_asset())
    validate_asset(load_modal_asset())
    validate_asset(load_tab_bar_asset())
    validate_asset(load_info_panel_asset())
    validate_asset(load_toast_asset())
    validate_asset(load_custom_fx_asset())
    validate_asset(load_gauge_radial_asset())
    validate_asset(load_gauge_segmented_asset())


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

    hud_svg = compile_svg(load_hud_asset())
    hud_root = ET.fromstring(hud_svg)
    assert hud_root.attrib.get("viewBox") == "0 0 1280 720"

    hud_mock_svg = compile_svg(load_hud_mock_asset())
    hud_mock_root = ET.fromstring(hud_mock_svg)
    assert hud_mock_root.attrib.get("viewBox") == "0 0 1280 720"

    primary_svg = compile_svg(load_primary_button_asset())
    primary_root = ET.fromstring(primary_svg)
    assert primary_root.attrib.get("viewBox") == "0 0 960 540"

    modal_svg = compile_svg(load_modal_asset())
    modal_root = ET.fromstring(modal_svg)
    assert modal_root.attrib.get("viewBox") == "0 0 1280 720"

    tab_svg = compile_svg(load_tab_bar_asset())
    tab_root = ET.fromstring(tab_svg)
    assert tab_root.attrib.get("viewBox") == "0 0 1280 720"

    info_svg = compile_svg(load_info_panel_asset())
    info_root = ET.fromstring(info_svg)
    assert info_root.attrib.get("viewBox") == "0 0 1280 720"

    toast_svg = compile_svg(load_toast_asset())
    toast_root = ET.fromstring(toast_svg)
    assert toast_root.attrib.get("viewBox") == "0 0 1280 720"

    custom_svg = compile_svg(load_custom_fx_asset())
    custom_root = ET.fromstring(custom_svg)
    assert custom_root.attrib.get("viewBox") == "0 0 1280 720"

    radial_svg = compile_svg(load_gauge_radial_asset())
    radial_root = ET.fromstring(radial_svg)
    assert radial_root.attrib.get("viewBox") == "0 0 1280 720"

    segmented_svg = compile_svg(load_gauge_segmented_asset())
    segmented_root = ET.fromstring(segmented_svg)
    assert segmented_root.attrib.get("viewBox") == "0 0 1280 720"
