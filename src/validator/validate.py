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
    asset_type = asset.get("assetType", "button")
    if asset_type == "screen":
        issues.extend(_check_screen(asset))
    else:
        issues.extend(_check_button(asset))
    return issues


def _check_button(asset: dict[str, Any]) -> List[str]:
    view_box = _coerce_view_box(asset.get("viewBox"))
    return _check_layers(asset.get("layers") or [], view_box, "/layers")


def _check_screen(asset: dict[str, Any]) -> List[str]:
    issues: List[str] = []
    canvas = asset.get("canvas", {})
    width = canvas.get("width")
    height = canvas.get("height")
    if _is_number(width) and width < 1:
        issues.append("/canvas/width: width must be >= 1")
    if _is_number(height) and height < 1:
        issues.append("/canvas/height: height must be >= 1")

    safe_area = canvas.get("safeArea")
    if safe_area:
        issues.extend(_check_safe_area(safe_area, width, height))

    components = asset.get("components") or []
    for index, component in enumerate(components):
        view_box = _coerce_view_box(component.get("viewBox"))
        issues.extend(
            _check_layers(
                component.get("layers") or [],
                view_box,
                f"/components/{index}/layers",
            )
        )

    instances = asset.get("instances") or []
    issues.extend(_check_instances(instances, components))
    return issues


def _check_safe_area(
    safe_area: dict[str, Any],
    canvas_width: Any,
    canvas_height: Any,
) -> List[str]:
    issues: List[str] = []
    for key in ("x", "y", "width", "height"):
        value = safe_area.get(key)
        if value is None:
            continue
        if not _is_number(value):
            issues.append(f"/canvas/safeArea/{key}: expected number, got {type(value).__name__}")
            continue
        if not math.isfinite(float(value)):
            issues.append(f"/canvas/safeArea/{key}: value must be finite")

    if _is_number(canvas_width) and _is_number(canvas_height):
        x = float(safe_area.get("x", 0))
        y = float(safe_area.get("y", 0))
        w = float(safe_area.get("width", 0))
        h = float(safe_area.get("height", 0))
        if x < 0 or y < 0 or x + w > float(canvas_width) or y + h > float(canvas_height):
            issues.append("/canvas/safeArea: safeArea must fit inside canvas")
    return issues


def _check_instances(instances: list[dict[str, Any]], components: list[dict[str, Any]]) -> List[str]:
    issues: List[str] = []
    component_ids = {component.get("id") for component in components}
    instance_ids = {instance.get("id") for instance in instances}

    for index, instance in enumerate(instances):
        prefix = f"/instances/{index}"
        component_id = instance.get("componentId")
        if component_id not in component_ids:
            issues.append(f"{prefix}/componentId: '{component_id}' is not defined")

        anchor_to = instance.get("anchorTo")
        if anchor_to != "canvas" and anchor_to not in instance_ids:
            issues.append(f"{prefix}/anchorTo: '{anchor_to}' is not defined")
        if anchor_to == instance.get("id"):
            issues.append(f"{prefix}/anchorTo: anchorTo cannot reference itself")

        offset = instance.get("offset", {})
        size = instance.get("size", {})
        issues.extend(_check_vector(offset, f"{prefix}/offset"))
        issues.extend(_check_size(size, f"{prefix}/size"))

    issues.extend(_detect_anchor_cycles(instances))
    return issues


def _detect_anchor_cycles(instances: list[dict[str, Any]]) -> List[str]:
    issues: List[str] = []
    instances_by_id = {instance.get("id"): instance for instance in instances}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(instance_id: str) -> None:
        if instance_id in visited:
            return
        if instance_id in visiting:
            issues.append("/instances: anchorTo cycle detected")
            return
        visiting.add(instance_id)
        instance = instances_by_id.get(instance_id)
        if instance:
            anchor_to = instance.get("anchorTo")
            if anchor_to and anchor_to != "canvas" and anchor_to in instances_by_id:
                visit(anchor_to)
        visiting.remove(instance_id)
        visited.add(instance_id)

    for instance_id in instances_by_id:
        visit(instance_id)
    return issues


def _check_layers(
    layers: list[dict[str, Any]],
    view_box: Optional[tuple[float, float, float, float]],
    base_path: str,
) -> List[str]:
    issues: List[str] = []
    if view_box:
        vb_x, vb_y, vb_w, vb_h = view_box
    else:
        vb_x = vb_y = vb_w = vb_h = None

    for index, layer in enumerate(layers):
        rect = layer.get("rect", {})
        shape = layer.get("shape")
        path_prefix = f"{base_path}/{index}/rect"
        width = rect.get("width")
        height = rect.get("height")

        rect_keys = ("x", "y", "width", "height")
        if shape == "roundedRect":
            rect_keys = rect_keys + ("radius",)

        for key in rect_keys:
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
                issues.append(f"{base_path}/{index}/style/strokeWidth: must be a number")
            else:
                if stroke_width < 0:
                    issues.append(f"{base_path}/{index}/style/strokeWidth: must be >= 0")
                if not _has_at_most_two_decimals(stroke_width):
                    issues.append(
                        f"{base_path}/{index}/style/strokeWidth: value must have at most 2 decimal places"
                    )

        if shape == "text":
            issues.extend(_check_text(layer.get("text", {}), f"{base_path}/{index}/text"))
        if shape in ("layoutRow", "layoutColumn", "layoutGrid"):
            issues.extend(_check_layout_layer(layer, f"{base_path}/{index}"))

    return issues


def _check_vector(vector: dict[str, Any], base_path: str) -> List[str]:
    issues: List[str] = []
    for key in ("x", "y"):
        value = vector.get(key)
        if value is None:
            continue
        if not _is_number(value):
            issues.append(f"{base_path}/{key}: expected number, got {type(value).__name__}")
            continue
        if not math.isfinite(float(value)):
            issues.append(f"{base_path}/{key}: value must be finite")
        if not _has_at_most_two_decimals(value):
            issues.append(f"{base_path}/{key}: value must have at most 2 decimal places")
    return issues


def _check_size(size: dict[str, Any], base_path: str) -> List[str]:
    issues: List[str] = []
    for key in ("width", "height"):
        value = size.get(key)
        if value is None:
            continue
        if not _is_number(value):
            issues.append(f"{base_path}/{key}: expected number, got {type(value).__name__}")
            continue
        if value < 1:
            issues.append(f"{base_path}/{key}: value must be >= 1")
        if not _has_at_most_two_decimals(value):
            issues.append(f"{base_path}/{key}: value must have at most 2 decimal places")
    return issues


def _check_text(text: dict[str, Any], base_path: str) -> List[str]:
    issues: List[str] = []
    value = text.get("value")
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{base_path}/value: must be a non-empty string")

    font = text.get("font")
    if not isinstance(font, str) or not font:
        issues.append(f"{base_path}/font: must be a token string")

    size = text.get("size")
    if size is None:
        issues.append(f"{base_path}/size: must be provided")
    elif not _is_number(size):
        issues.append(f"{base_path}/size: expected number, got {type(size).__name__}")
    else:
        if size <= 0:
            issues.append(f"{base_path}/size: value must be > 0")
        if not _has_at_most_two_decimals(size):
            issues.append(f"{base_path}/size: value must have at most 2 decimal places")

    max_lines = text.get("maxLines")
    if not isinstance(max_lines, int) or isinstance(max_lines, bool):
        issues.append(f"{base_path}/maxLines: must be an integer")
    elif max_lines < 1:
        issues.append(f"{base_path}/maxLines: must be >= 1")

    overflow = text.get("overflow")
    if overflow not in ("ellipsis", "clip"):
        issues.append(f"{base_path}/overflow: must be 'ellipsis' or 'clip'")

    fit = text.get("fit")
    if fit not in ("none", "shrink"):
        issues.append(f"{base_path}/fit: must be 'none' or 'shrink'")

    align = text.get("align")
    if align is not None and align not in ("left", "center", "right"):
        issues.append(f"{base_path}/align: must be 'left', 'center', or 'right'")

    return issues


def _check_layout_layer(layer: dict[str, Any], base_path: str) -> List[str]:
    issues: List[str] = []
    shape = layer.get("shape")
    layout = layer.get("layout", {})
    items = layer.get("items", [])

    if not isinstance(items, list) or not items:
        issues.append(f"{base_path}/items: must be a non-empty array")
        return issues

    issues.extend(_check_layout_config(layout, shape, f"{base_path}/layout"))

    for index, item in enumerate(items):
        item_path = f"{base_path}/items/{index}"
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            issues.append(f"{item_path}/id: must be a non-empty string")

        component_id = item.get("componentId")
        if not isinstance(component_id, str) or not component_id:
            issues.append(f"{item_path}/componentId: must be a non-empty string")

        size = item.get("size", {})
        issues.extend(_check_size(size, f"{item_path}/size"))

    return issues


def _check_layout_config(layout: dict[str, Any], shape: str, base_path: str) -> List[str]:
    issues: List[str] = []
    align = layout.get("align")
    if align is not None and align not in ("start", "center", "end", "stretch"):
        issues.append(f"{base_path}/align: must be 'start', 'center', 'end', or 'stretch'")

    padding = layout.get("padding", {})
    if isinstance(padding, dict):
        for key in ("top", "right", "bottom", "left"):
            value = padding.get(key)
            if value is None:
                continue
            if not _is_number(value):
                issues.append(f"{base_path}/padding/{key}: expected number, got {type(value).__name__}")
                continue
            if value < 0:
                issues.append(f"{base_path}/padding/{key}: value must be >= 0")
            if not _has_at_most_two_decimals(value):
                issues.append(f"{base_path}/padding/{key}: value must have at most 2 decimal places")
    else:
        issues.append(f"{base_path}/padding: must be an object")

    if shape in ("layoutRow", "layoutColumn"):
        gap = layout.get("gap")
        if gap is not None:
            if not _is_number(gap):
                issues.append(f"{base_path}/gap: expected number, got {type(gap).__name__}")
            elif gap < 0:
                issues.append(f"{base_path}/gap: value must be >= 0")
            elif not _has_at_most_two_decimals(gap):
                issues.append(f"{base_path}/gap: value must have at most 2 decimal places")

    if shape == "layoutGrid":
        columns = layout.get("columns")
        if not isinstance(columns, int) or isinstance(columns, bool):
            issues.append(f"{base_path}/columns: must be an integer")
        elif columns < 1:
            issues.append(f"{base_path}/columns: must be >= 1")

        for key in ("rowGap", "colGap"):
            value = layout.get(key)
            if value is None:
                continue
            if not _is_number(value):
                issues.append(f"{base_path}/{key}: expected number, got {type(value).__name__}")
                continue
            if value < 0:
                issues.append(f"{base_path}/{key}: value must be >= 0")
            if not _has_at_most_two_decimals(value):
                issues.append(f"{base_path}/{key}: value must have at most 2 decimal places")

    return issues


def _coerce_view_box(view_box: Any) -> Optional[tuple[float, float, float, float]]:
    if isinstance(view_box, list) and len(view_box) == 4:
        return tuple(float(value) for value in view_box)
    return None


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
