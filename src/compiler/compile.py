"""JSON → SVG compiler for the MVP button asset."""
from __future__ import annotations

import math
from xml.etree import ElementTree as ET
from typing import Any, Dict

from .tokens import GlowDef, LinearGradientDef, TokenRegistry


def compile_svg(asset: Dict[str, Any]) -> str:
    """Convert a validated JSON asset into SVG markup."""
    registry = TokenRegistry()
    view_box = asset["viewBox"]
    width = str(view_box[2])
    height = str(view_box[3])

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "version": "1.1",
            "viewBox": " ".join(str(value) for value in view_box),
            "width": width,
            "height": height,
        },
    )

    defs = ET.SubElement(svg, "defs")
    gradient_ids: set[str] = set()
    glow_ids: set[str] = set()

    for layer in asset["layers"]:
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

    if len(defs) == 0:
        svg.remove(defs)

    for layer in asset["layers"]:
        group = ET.SubElement(svg, "g", {"id": layer["id"]})
        rect_attrs = _build_rect_attrs(layer, registry)
        ET.SubElement(group, "rect", rect_attrs)

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
