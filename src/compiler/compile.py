"""JSON → SVG compiler for UI assets."""
from __future__ import annotations

import math
from xml.etree import ElementTree as ET
from typing import Any, Dict, Iterable, List, Optional, Tuple

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

    clip_ids: set[str] = set()
    _append_layers(svg, asset["layers"], registry, defs, clip_ids, id_prefix="", components=None)
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
    clip_ids: set[str] = set()

    for instance in instance_order:
        instance_id = instance["id"]
        component = components[instance["componentId"]]
        rect = resolved[instance_id]
        transform = _build_instance_transform(rect, component["viewBox"])
        group = ET.SubElement(svg, "g", {"id": instance_id, "transform": transform})
    _append_layers(
        group,
        component["layers"],
        registry,
        defs,
        clip_ids,
        id_prefix=f"{instance_id}--",
        components=components,
    )

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
    defs: ET.Element,
    clip_ids: set[str],
    id_prefix: str,
    components: Optional[Dict[str, Dict[str, Any]]],
) -> None:
    for layer in layers:
        group = ET.SubElement(parent, "g", {"id": f"{id_prefix}{layer['id']}"})
        shape = layer.get("shape")
        if shape == "roundedRect":
            rect_attrs = _build_rect_attrs(layer, registry)
            ET.SubElement(group, "rect", rect_attrs)
        elif shape == "text":
            text_element = _build_text_element(layer, registry, defs, clip_ids, id_prefix)
            group.append(text_element)
        elif shape in ("layoutRow", "layoutColumn", "layoutGrid"):
            if components is None:
                raise ValueError("Layout layers require component definitions.")
            _append_layout_items(group, layer, registry, defs, clip_ids, id_prefix, components)
        else:
            raise ValueError(f"Unsupported shape: {shape}")


def _build_text_element(
    layer: Dict[str, Any],
    registry: TokenRegistry,
    defs: ET.Element,
    clip_ids: set[str],
    id_prefix: str,
) -> ET.Element:
    rect = layer["rect"]
    text_config = layer["text"]
    style = layer.get("style", {})

    font_size = float(text_config["size"])
    align = text_config.get("align", "left")
    anchor = _text_anchor(align)
    x, y = _text_position(rect, align)

    attrs = {
        "x": _fmt(x),
        "y": _fmt(y),
        "fill": _resolve_fill(style.get("fill"), registry),
        "font-family": registry.get_font(text_config["font"]) or "sans-serif",
        "font-size": _fmt(font_size),
        "text-anchor": anchor,
        "dominant-baseline": "hanging",
    }

    overflow = text_config["overflow"]
    if overflow in ("clip", "ellipsis"):
        clip_id = f"clip-{id_prefix}{layer['id']}"
        if clip_id not in clip_ids:
            clip_ids.add(clip_id)
            clip_path = ET.SubElement(defs, "clipPath", {"id": clip_id})
            ET.SubElement(
                clip_path,
                "rect",
                {
                    "x": _fmt(rect["x"]),
                    "y": _fmt(rect["y"]),
                    "width": _fmt(rect["width"]),
                    "height": _fmt(rect["height"]),
                },
            )
        attrs["clip-path"] = f"url(#{clip_id})"

    text_el = ET.Element("text", attrs)
    lines = _layout_text_lines(
        text_config["value"],
        int(text_config["maxLines"]),
        float(rect["width"]),
        font_size,
        overflow,
    )
    line_height = font_size * 1.2
    fit = text_config["fit"]
    for index, line in enumerate(lines):
        tspan_attrs = {"x": _fmt(x)}
        if index == 0:
            tspan_attrs["y"] = _fmt(y)
        else:
            tspan_attrs["dy"] = _fmt(line_height)
        if fit == "shrink":
            tspan_attrs["textLength"] = _fmt(rect["width"])
            tspan_attrs["lengthAdjust"] = "spacingAndGlyphs"
        tspan = ET.SubElement(text_el, "tspan", tspan_attrs)
        tspan.text = line

    return text_el


def _append_layout_items(
    parent: ET.Element,
    layer: Dict[str, Any],
    registry: TokenRegistry,
    defs: ET.Element,
    clip_ids: set[str],
    id_prefix: str,
    components: Dict[str, Dict[str, Any]],
) -> None:
    layout_type = layer["shape"]
    rect = layer["rect"]
    layout = layer.get("layout", {})
    items = layer.get("items", [])

    positions = _layout_positions(layout_type, rect, layout, items)
    for item, item_rect in positions:
        component_id = item["componentId"]
        if component_id not in components:
            raise ValueError(f"Component '{component_id}' is not defined.")
        component = components[component_id]

        item_group_id = f"{id_prefix}{layer['id']}--{item['id']}"
        transform = _build_instance_transform(item_rect, component["viewBox"])
        group = ET.SubElement(parent, "g", {"id": item_group_id, "transform": transform})
        _append_layers(
            group,
            component["layers"],
            registry,
            defs,
            clip_ids,
            id_prefix=f"{item_group_id}--",
            components=components,
        )


def _layout_positions(
    layout_type: str,
    rect: Dict[str, Any],
    layout: Dict[str, Any],
    items: List[Dict[str, Any]],
) -> List[Tuple[Dict[str, Any], Tuple[float, float, float, float]]]:
    padding = _normalize_padding(layout.get("padding", {}))
    gap = float(layout.get("gap", 0) or 0)
    align = layout.get("align", "start")

    origin_x = float(rect["x"]) + padding["left"]
    origin_y = float(rect["y"]) + padding["top"]
    content_w = float(rect["width"]) - padding["left"] - padding["right"]
    content_h = float(rect["height"]) - padding["top"] - padding["bottom"]

    if layout_type == "layoutRow":
        return _layout_row(items, origin_x, origin_y, content_w, content_h, gap, align)
    if layout_type == "layoutColumn":
        return _layout_column(items, origin_x, origin_y, content_w, content_h, gap, align)
    if layout_type == "layoutGrid":
        columns = int(layout["columns"])
        row_gap = float(layout.get("rowGap", 0) or 0)
        col_gap = float(layout.get("colGap", 0) or 0)
        return _layout_grid(items, origin_x, origin_y, content_w, content_h, columns, row_gap, col_gap, align)

    raise ValueError(f"Unsupported layout type: {layout_type}")


def _layout_row(
    items: List[Dict[str, Any]],
    origin_x: float,
    origin_y: float,
    content_w: float,
    content_h: float,
    gap: float,
    align: str,
) -> List[Tuple[Dict[str, Any], Tuple[float, float, float, float]]]:
    positions: List[Tuple[Dict[str, Any], Tuple[float, float, float, float]]] = []
    cursor_x = origin_x
    for item in items:
        item_w = float(item["size"]["width"])
        item_h = float(item["size"]["height"])
        if align == "stretch":
            item_h = max(content_h, 0)
        y = origin_y + _align_offset(align, content_h, item_h)
        positions.append((item, (cursor_x, y, item_w, item_h)))
        cursor_x += item_w + gap
    return positions


def _layout_column(
    items: List[Dict[str, Any]],
    origin_x: float,
    origin_y: float,
    content_w: float,
    content_h: float,
    gap: float,
    align: str,
) -> List[Tuple[Dict[str, Any], Tuple[float, float, float, float]]]:
    positions: List[Tuple[Dict[str, Any], Tuple[float, float, float, float]]] = []
    cursor_y = origin_y
    for item in items:
        item_w = float(item["size"]["width"])
        item_h = float(item["size"]["height"])
        if align == "stretch":
            item_w = max(content_w, 0)
        x = origin_x + _align_offset(align, content_w, item_w)
        positions.append((item, (x, cursor_y, item_w, item_h)))
        cursor_y += item_h + gap
    return positions


def _layout_grid(
    items: List[Dict[str, Any]],
    origin_x: float,
    origin_y: float,
    content_w: float,
    content_h: float,
    columns: int,
    row_gap: float,
    col_gap: float,
    align: str,
) -> List[Tuple[Dict[str, Any], Tuple[float, float, float, float]]]:
    positions: List[Tuple[Dict[str, Any], Tuple[float, float, float, float]]] = []
    if columns <= 0:
        return positions

    rows = max(1, (len(items) + columns - 1) // columns)
    cell_w = (content_w - col_gap * (columns - 1)) / columns if columns > 0 else 0
    cell_h = (content_h - row_gap * (rows - 1)) / rows if rows > 0 else 0

    for index, item in enumerate(items):
        row = index // columns
        col = index % columns
        cell_x = origin_x + col * (cell_w + col_gap)
        cell_y = origin_y + row * (cell_h + row_gap)

        item_w = float(item["size"]["width"])
        item_h = float(item["size"]["height"])
        if align == "stretch":
            item_w = max(cell_w, 0)
            item_h = max(cell_h, 0)
            offset_x = 0
            offset_y = 0
        else:
            offset_x = _align_offset(align, cell_w, item_w)
            offset_y = _align_offset(align, cell_h, item_h)
        positions.append((item, (cell_x + offset_x, cell_y + offset_y, item_w, item_h)))
    return positions


def _normalize_padding(padding: Dict[str, Any]) -> Dict[str, float]:
    return {
        "top": float(padding.get("top", 0) or 0),
        "right": float(padding.get("right", 0) or 0),
        "bottom": float(padding.get("bottom", 0) or 0),
        "left": float(padding.get("left", 0) or 0),
    }


def _align_offset(align: str, container_size: float, item_size: float) -> float:
    if align == "center":
        return (container_size - item_size) / 2
    if align == "end":
        return container_size - item_size
    return 0.0


def _layout_text_lines(
    value: str,
    max_lines: int,
    max_width: float,
    font_size: float,
    overflow: str,
) -> List[str]:
    text = " ".join(value.split())
    if not text:
        return [""]

    max_chars = max(1, int(max_width / max(font_size * 0.6, 1)))
    words = text.split(" ")
    lines: List[str] = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        while len(word) > max_chars:
            lines.append(word[:max_chars])
            word = word[max_chars:]
        current = word

    if current:
        lines.append(current)

    if len(lines) <= max_lines:
        return lines

    truncated = lines[:max_lines]
    if overflow == "ellipsis" and truncated:
        last = truncated[-1]
        if len(last) >= max_chars:
            last = last[: max(1, max_chars - 1)]
        truncated[-1] = f"{last}..."
    return truncated


def _text_anchor(align: str) -> str:
    return {"left": "start", "center": "middle", "right": "end"}[align]


def _text_position(rect: Dict[str, Any], align: str) -> Tuple[float, float]:
    x = float(rect["x"])
    y = float(rect["y"])
    width = float(rect["width"])
    if align == "center":
        x += width / 2
    elif align == "right":
        x += width
    return x, y


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
