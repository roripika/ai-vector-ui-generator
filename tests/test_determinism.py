import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from src.compiler import compile_svg

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "button_sf.json"
EXPECTED_SHA256 = "d7bb0a16e15d64a4f5288b74b5aae0a38ed6673c1350550628719196354babcd"
SCREEN_DIALOG_PATH = Path(__file__).resolve().parents[1] / "examples" / "screen_dialog.json"
LIST_SCREEN_PATH = Path(__file__).resolve().parents[1] / "examples" / "list_screen.json"
GRID_SCREEN_PATH = Path(__file__).resolve().parents[1] / "examples" / "grid_screen.json"
HUD_MOCK_PATH = Path(__file__).resolve().parents[1] / "examples" / "hud_basic.mock.json"

EXPECTED_SCREEN_DIALOG_SHA256 = "ee898454cf36103d348c513279fd9ae0a48860e0480517f55ecb39176ba01f24"
EXPECTED_LIST_SCREEN_SHA256 = "52b9b50408ec34f419102e53f147c0a96006a58ef55c09bea5d8884992be4613"
EXPECTED_GRID_SCREEN_SHA256 = "7080800a9adf6f5e42475fa5cd90335069cfcbd742bd37a39e82a43c2d1255be"
EXPECTED_HUD_MOCK_SHA256 = "5a434e957e8c046dc51567847b3620070594e56860b619d51244f51bee1d0082"


def load_asset() -> dict:
    with EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_svg(svg_text: str) -> bytes:
    root = ET.fromstring(svg_text)
    _normalize_element(root)
    return ET.tostring(root, encoding="utf-8")


def _normalize_element(element: ET.Element) -> None:
    if element.text is None or element.text.strip() == "":
        element.text = ""
    if element.tail is None or element.tail.strip() == "":
        element.tail = ""

    if element.attrib:
        ordered = {key: element.attrib[key] for key in sorted(element.attrib)}
        element.attrib.clear()
        element.attrib.update(ordered)

    for child in list(element):
        _normalize_element(child)


def _hash_svg(svg_text: str) -> str:
    normalized = normalize_svg(svg_text)
    return hashlib.sha256(normalized).hexdigest()


def test_svg_hash_is_deterministic_and_matches_snapshot():
    asset = load_asset()

    first_hash = _hash_svg(compile_svg(asset))
    second_hash = _hash_svg(compile_svg(asset))

    assert first_hash == second_hash
    assert first_hash == EXPECTED_SHA256


def test_screen_svg_hashes_are_deterministic_and_match_snapshots():
    fixtures = [
        (SCREEN_DIALOG_PATH, EXPECTED_SCREEN_DIALOG_SHA256),
        (LIST_SCREEN_PATH, EXPECTED_LIST_SCREEN_SHA256),
        (GRID_SCREEN_PATH, EXPECTED_GRID_SCREEN_SHA256),
        (HUD_MOCK_PATH, EXPECTED_HUD_MOCK_SHA256),
    ]

    for path, expected in fixtures:
        asset = load_json(path)
        first_hash = _hash_svg(compile_svg(asset))
        second_hash = _hash_svg(compile_svg(asset))

        assert first_hash == second_hash
        assert first_hash == expected
