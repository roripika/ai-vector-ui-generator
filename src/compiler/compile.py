"""JSON → SVG compiler for UI assets."""
from __future__ import annotations

import math
from xml.etree import ElementTree as ET
from typing import Any, Dict, Iterable, Tuple

from .tokens import GlowDef, LinearGradientDef, TokenRegistry


def compile_svg(asset: Dict[str, Any]) -> str:
    """Convert a validated JSON asset into SVG markup."""
    asset_type = asset.get("assetType", "button")
    if asset_type == "screen":
        return _compile_screen(asset)
    return _compile_button(asset)


def _compile_button(asset: Dict[str, Any]) -> str:
    registry = TokenRegistry()
    view_box = asset["viewBox"]
    svg = _build_svg_root(view_box)

    defs = ET.SubElement(svg, "defs")
    gradient_ids: set[str] = set()
    glow_ids: set[str] = set()
    _collect_defs(asset["layers"], registry, defs, gradient_ids, glow_ids, view_box)

    if len(defs) == 0:
        svg.remove(defs)

    _append_layers(svg, asset["layers"], registry, id_prefix="")
    return ET.tostring(svg, encoding="unicode")


def _compile_screen(asset: Dict[str, Any]) -> str:
    registry = TokenRegistry()
    canvas = asset["canvas"]
    view_box = [0, 0, canvas["width"], canvas["height"]]
    svg = _build_svg_root(view_box)

    components = {component["id"]: component for component in asset["components"]}
    instances = asset["instances"]

    defs = ET.SubElement(svg, "defs")
    gradient_ids: set[str] = set()
    glow_ids: set[str] = set()
    for component in asset["components"]:
        _collect_defs(component["layers"], registry, defs, gradient_ids, glow_ids, view_box)

    if len(defs) == 0:
        svg.remove(defs)

    instance_order = sorted(instances, key=lambda item: (item.get("zIndex", 0), item["id"]))
    resolved = _resolve_instances(instance_order, components, view_box)

    for instance in instance_order:
        instance_id = instance["id"]
        component = components[instance["componentId"]]
        rect = resolved[instance_id]
        transform = _build_instance_transform(rect, component["viewBox"])
        group = ET.SubElement(svg, "g", {"id": instance_id, "transform": transform})
        _append_layers(group, component["layers"], registry, id_prefix=f"{instance_id}--")

    return ET.tostring(svg, encoding="unicode")


def _build_rect_attrs(layer: Dict[str, Any], registry: TokenRegistry) -> Dict[str, str]:
    rect = layer["rect"]
    style = layer.get("style", {})
    attrs: Dict[str, str] = {
        "x": _fmt(rect["x"]),
        "y": _fmt(rect["y"]),
        "width": _fmt(rect["width"]),
        "height": _fmt(rect["height"]),
        "rx": _fmt(rect["radius"]),
        "ry": _fmt(rect["radius"]),
        "fill": _resolve_fill(style.get("fill"), registry),
    }

    stroke_token = style.get("stroke")
    stroke_color = registry.get_color(stroke_token)
    stroke_width = style.get("strokeWidth")
    if stroke_color and stroke_width is not None:
        attrs["stroke"] = stroke_color
        attrs["stroke-width"] = _fmt(stroke_width)
    else:
        attrs["stroke"] = "none"

    glow_token = style.get("glow")
    if glow_token and registry.get_glow(glow_token):
        attrs["filter"] = f"url(#{_token_id(glow_token)})"

    return attrs


def _build_svg_root(view_box: list[int]) -> ET.Element:
    width = str(view_box[2])
    height = str(view_box[3])
    return ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "version": "1.1",
            "viewBox": " ".join(str(value) for value in view_box),
            "width": width,
            "height": height,
        },
    )


def _append_layers(
    parent: ET.Element,
    layers: Iterable[Dict[str, Any]],
    registry: TokenRegistry,
    id_prefix: str,
) -> None:
    for layer in layers:
        group = ET.SubElement(parent, "g", {"id": f"{id_prefix}{layer['id']}"})
        rect_attrs = _build_rect_attrs(layer, registry)
        ET.SubElement(group, "rect", rect_attrs)


def _collect_defs(
    layers: Iterable[Dict[str, Any]],
    registry: TokenRegistry,
    defs: ET.Element,
    gradient_ids: set[str],
    glow_ids: set[str],
    view_box: list[int],
) -> None:
    for layer in layers:
        style = layer.get("style", {})
        fill_token = style.get("fill")
        gradient_def = registry.get_linear_gradient(fill_token)
        if gradient_def and fill_token not in gradient_ids:
            defs.append(_build_linear_gradient(fill_token, gradient_def))
            gradient_ids.add(fill_token)

        glow_token = style.get("glow")
        glow_def = registry.get_glow(glow_token)
        if glow_def and glow_token not in glow_ids:
            defs.append(_build_glow_filter(glow_token, glow_def, view_box))
            glow_ids.add(glow_token)


def _resolve_instances(
    instances: Iterable[Dict[str, Any]],
    components: Dict[str, Dict[str, Any]],
    view_box: list[int],
) -> Dict[str, Tuple[float, float, float, float]]:
    instances_by_id = {instance["id"]: instance for instance in instances}
    resolved: Dict[str, Tuple[float, float, float, float]] = {}
    visiting: set[str] = set()

    def resolve(instance_id: str) -> Tuple[float, float, float, float]:
        if instance_id in resolved:
            return resolved[instance_id]
        if instance_id in visiting:
            raise ValueError(f"Anchor cycle detected at instance '{instance_id}'.")
        visiting.add(instance_id)
        instance = instances_by_id[instance_id]
        parent_rect = _resolve_parent_rect(instance, instances_by_id, view_box, resolve)

        size = instance["size"]
        rect = _place_rect(parent_rect, size, instance["anchor"], instance["offset"])
        resolved[instance_id] = rect
        visiting.remove(instance_id)
        return rect

    for instance in instances:
        resolve(instance["id"])

    return resolved


def _resolve_parent_rect(
    instance: Dict[str, Any],
    instances_by_id: Dict[str, Dict[str, Any]],
    view_box: list[int],
    resolve: Any,
) -> Tuple[float, float, float, float]:
    anchor_to = instance["anchorTo"]
    if anchor_to == "canvas":
        return (float(view_box[0]), float(view_box[1]), float(view_box[2]), float(view_box[3]))
    if anchor_to not in instances_by_id:
        raise ValueError(f"anchorTo '{anchor_to}' is not defined.")
    return resolve(anchor_to)


def _place_rect(
    parent_rect: Tuple[float, float, float, float],
    size: Dict[str, Any],
    anchor: str,
    offset: Dict[str, Any],
) -> Tuple[float, float, float, float]:
    parent_x, parent_y, parent_w, parent_h = parent_rect
    child_w = float(size["width"])
    child_h = float(size["height"])
    anchor_x, anchor_y = _anchor_point(parent_x, parent_y, parent_w, parent_h, anchor)
    offset_x, offset_y = _anchor_offset(child_w, child_h, anchor)
    x = anchor_x - offset_x + float(offset["x"])
    y = anchor_y - offset_y + float(offset["y"])
    return (x, y, child_w, child_h)


def _anchor_point(
    x: float,
    y: float,
    w: float,
    h: float,
    anchor: str,
) -> Tuple[float, float]:
    mapping = {
        "topLeft": (x, y),
        "top": (x + w / 2, y),
        "topRight": (x + w, y),
        "left": (x, y + h / 2),
        "center": (x + w / 2, y + h / 2),
        "right": (x + w, y + h / 2),
        "bottomLeft": (x, y + h),
        "bottom": (x + w / 2, y + h),
        "bottomRight": (x + w, y + h),
    }
    return mapping[anchor]


def _anchor_offset(w: float, h: float, anchor: str) -> Tuple[float, float]:
    return _anchor_point(0, 0, w, h, anchor)


def _build_instance_transform(
    rect: Tuple[float, float, float, float],
    view_box: list[int],
) -> str:
    x, y, width, height = rect
    vb_x, vb_y, vb_w, vb_h = map(float, view_box)
    scale_x = width / vb_w
    scale_y = height / vb_h
    translate_x = x - vb_x * scale_x
    translate_y = y - vb_y * scale_y
    return f"translate({_fmt(translate_x)} {_fmt(translate_y)}) scale({_fmt(scale_x)} {_fmt(scale_y)})"


def _resolve_fill(token: str | None, registry: TokenRegistry) -> str:
    gradient = registry.get_linear_gradient(token)
    if gradient:
        return f"url(#{_token_id(token)})"
    color = registry.get_color(token)
    return color or "currentColor"


def _build_linear_gradient(token: str, definition: LinearGradientDef) -> ET.Element:
    gradient_id = _token_id(token)
    x1, y1, x2, y2 = _angle_to_bbox_coords(definition.angle)
    gradient = ET.Element(
        "linearGradient",
        {
            "id": gradient_id,
            "gradientUnits": "objectBoundingBox",
            "spreadMethod": definition.spread_method,
            "x1": f"{x1:.3f}",
            "y1": f"{y1:.3f}",
            "x2": f"{x2:.3f}",
            "y2": f"{y2:.3f}",
        },
    )
    for stop in definition.stops:
        ET.SubElement(
            gradient,
            "stop",
            {
                "offset": f"{stop.offset:.3f}",
                "stop-color": stop.color,
                "stop-opacity": f"{stop.opacity:.3f}",
            },
        )
    return gradient


def _build_glow_filter(token: str, definition: GlowDef, view_box: list[int]) -> ET.Element:
    vx, vy, vw, vh = view_box
    margin = definition.margin
    filter_el = ET.Element(
        "filter",
        {
            "id": _token_id(token),
            "filterUnits": "userSpaceOnUse",
            "x": _fmt(vx - margin),
            "y": _fmt(vy - margin),
            "width": _fmt(vw + margin * 2),
            "height": _fmt(vh + margin * 2),
        },
    )
    ET.SubElement(
        filter_el,
        "feGaussianBlur",
        {
            "in": "SourceGraphic",
            "stdDeviation": _fmt(definition.std_deviation),
            "result": "blurred",
        },
    )
    ET.SubElement(
        filter_el,
        "feFlood",
        {
            "flood-color": definition.color,
            "flood-opacity": f"{definition.opacity:.3f}",
            "result": "glowColor",
        },
    )
    ET.SubElement(
        filter_el,
        "feComposite",
        {
            "in": "glowColor",
            "in2": "blurred",
            "operator": "in",
            "result": "coloredGlow",
        },
    )
    merge = ET.SubElement(filter_el, "feMerge")
    ET.SubElement(merge, "feMergeNode", {"in": "coloredGlow"})
    ET.SubElement(merge, "feMergeNode", {"in": "SourceGraphic"})
    return filter_el


def _fmt(value: float | int) -> str:
    return f"{float(value):.2f}"


def _token_id(token: str) -> str:
    return token.replace('.', '-')


def _angle_to_bbox_coords(angle: float) -> tuple[float, float, float, float]:
    radians = math.radians(angle % 360)
    dx = math.cos(radians)
    dy = math.sin(radians)
    x1 = (1 - dx) * 0.5
    y1 = (1 - dy) * 0.5
    x2 = (1 + dx) * 0.5
    y2 = (1 + dy) * 0.5
    return x1, y1, x2, y2


__all__ = ["compile_svg"]
