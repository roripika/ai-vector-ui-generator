import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from src.compiler import compile_svg

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "button_sf.json"
EXPECTED_SHA256 = "d7bb0a16e15d64a4f5288b74b5aae0a38ed6673c1350550628719196354babcd"


def load_asset() -> dict:
    with EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
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
