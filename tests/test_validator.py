import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.validator import ValidationError, validate_asset

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "button_sf.json"


def load_asset() -> dict:
    with EXAMPLE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_valid_asset_passes():
    asset = load_asset()
    validate_asset(asset)


def test_rejects_precision_overflow():
    asset = load_asset()
    asset["layers"][0]["rect"]["width"] = 120.123
    with pytest.raises(ValidationError) as excinfo:
        validate_asset(asset)
    assert "decimal" in str(excinfo.value)


def test_rejects_negative_or_small_dimensions():
    asset = load_asset()
    asset["layers"][0]["rect"]["width"] = 0.5
    with pytest.raises(ValidationError) as excinfo:
        validate_asset(asset)
    assert "width" in str(excinfo.value)


def test_rejects_viewbox_violations():
    asset = load_asset()
    asset["layers"][0]["rect"]["x"] = 300
    with pytest.raises(ValidationError) as excinfo:
        validate_asset(asset)
    assert "viewBox" in str(excinfo.value)


def test_rejects_negative_stroke_width():
    asset = load_asset()
    asset["layers"][0]["style"]["strokeWidth"] = -1
    with pytest.raises(ValidationError):
        validate_asset(asset)
