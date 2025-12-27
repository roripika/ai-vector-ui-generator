"""Schema + semantic validator for UI asset JSON."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable, List, Optional

from jsonschema import Draft7Validator

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "ui_asset.schema.json"
_VALIDATOR_CACHE: dict[Path, Draft7Validator] = {}


class ValidationError(Exception):
    """Raised when a JSON asset fails schema or semantic validation."""

    def __init__(self, issues: Iterable[str]) -> None:
        self.issues = list(issues)
        message = "Validation failed:\n" + "\n".join(f"- {issue}" for issue in self.issues)
        super().__init__(message)


def validate_asset(asset: dict[str, Any], schema_path: Optional[Path] = None) -> None:
    """Validate an in-memory JSON object. Raises ValidationError on failure."""
    validator = _get_validator(schema_path)
    issues: List[str] = []

    for error in sorted(validator.iter_errors(asset), key=_error_sort_key):
        issues.append(f"{_format_path(error.path)}: {error.message}")

    issues.extend(_semantic_checks(asset))

    if issues:
        raise ValidationError(issues)


def _get_validator(schema_path: Optional[Path]) -> Draft7Validator:
    path = Path(schema_path).resolve() if schema_path else SCHEMA_PATH.resolve()
    if path not in _VALIDATOR_CACHE:
        with path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        _VALIDATOR_CACHE[path] = Draft7Validator(schema)
    return _VALIDATOR_CACHE[path]


def _semantic_checks(asset: dict[str, Any]) -> List[str]:
    issues: List[str] = []
    view_box = asset.get("viewBox")
    vb = view_box if isinstance(view_box, list) and len(view_box) == 4 else None
    if vb:
        vb_x, vb_y, vb_w, vb_h = map(float, vb)
    else:
        vb_x = vb_y = vb_w = vb_h = None

    layers = asset.get("layers") or []
    for index, layer in enumerate(layers):
        rect = layer.get("rect", {})
        path_prefix = f"/layers/{index}/rect"
        width = rect.get("width")
        height = rect.get("height")

        for key in ("x", "y", "width", "height", "radius"):
            value = rect.get(key)
            if value is None:
                continue
            if not _is_number(value):
                issues.append(f"{path_prefix}/{key}: expected number, got {type(value).__name__}")
                continue
            if not math.isfinite(float(value)):
                issues.append(f"{path_prefix}/{key}: value must be finite")
            if not _has_at_most_two_decimals(value):
                issues.append(f"{path_prefix}/{key}: value must have at most 2 decimal places")

        if _is_number(width) and width < 1:
            issues.append(f"{path_prefix}/width: width must be >= 1")
        if _is_number(height) and height < 1:
            issues.append(f"{path_prefix}/height: height must be >= 1")

        if vb_x is not None and _is_number(width) and _is_number(rect.get("x")):
            x = float(rect["x"])
            if x < vb_x or x + float(width) > vb_x + vb_w:
                issues.append(f"{path_prefix}: rectangle exceeds viewBox horizontally")
        if vb_y is not None and _is_number(height) and _is_number(rect.get("y")):
            y = float(rect["y"])
            if y < vb_y or y + float(height) > vb_y + vb_h:
                issues.append(f"{path_prefix}: rectangle exceeds viewBox vertically")

        stroke_width = layer.get("style", {}).get("strokeWidth")
        if stroke_width is not None:
            if not _is_number(stroke_width):
                issues.append(f"/layers/{index}/style/strokeWidth: must be a number")
            else:
                if stroke_width < 0:
                    issues.append(f"/layers/{index}/style/strokeWidth: must be >= 0")
                if not _has_at_most_two_decimals(stroke_width):
                    issues.append(
                        f"/layers/{index}/style/strokeWidth: value must have at most 2 decimal places"
                    )

    return issues


def _format_path(path: Iterable[Any]) -> str:
    segments = [str(part) for part in path]
    return "/" + "/".join(segments) if segments else "$"


def _error_sort_key(error: Any) -> tuple[int, str]:
    return (len(error.path), "/".join(str(part) for part in error.path))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _has_at_most_two_decimals(value: float) -> bool:
    scaled = round(float(value) * 100)
    return math.isclose(float(value), scaled / 100.0, rel_tol=0, abs_tol=1e-9)


__all__ = ["ValidationError", "validate_asset"]
