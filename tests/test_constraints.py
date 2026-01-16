from src.constraints import normalize_asset_constraints


def test_normalize_constraints_from_array():
    asset = {
        "assetType": "screen",
        "constraints": ["min_tap", "safe_area"],
        "components": [],
        "instances": [],
    }

    normalize_asset_constraints(asset)

    assert asset["constraint_flags"] == ["min_tap", "safe_area"]
    assert "constraint_params" not in asset


def test_normalize_constraints_from_object():
    asset = {
        "assetType": "screen",
        "components": [
            {
                "id": "panel",
                "constraints": {"padding": {"top": 8}, "safe_area": True},
                "layers": [],
                "viewBox": [0, 0, 10, 10],
            }
        ],
        "instances": [],
    }

    normalize_asset_constraints(asset)

    component = asset["components"][0]
    assert component["constraint_flags"] == ["safe_area"]
    assert component["constraint_params"] == {"padding": {"top": 8}}


def test_normalize_constraints_preserves_existing_fields():
    asset = {
        "assetType": "screen",
        "instances": [
            {
                "id": "item",
                "constraint_flags": ["overlap"],
                "constraint_params": {"min_tap": {"width": 44, "height": 44}},
                "constraints": ["safe_area"],
            }
        ],
        "components": [],
    }

    normalize_asset_constraints(asset)

    instance = asset["instances"][0]
    assert instance["constraint_flags"] == ["overlap", "safe_area"]
    assert instance["constraint_params"] == {"min_tap": {"width": 44, "height": 44}}
