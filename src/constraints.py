"""Normalize constraint fields for UI assets."""
from __future__ import annotations

from typing import Any, Dict, Iterable


def normalize_constraints_item(item: Dict[str, Any]) -> None:
    """Normalize legacy `constraints` into `constraint_flags`/`constraint_params` in-place."""
    if not isinstance(item, dict):
        return

    flags: list[str] = []
    params: Dict[str, Any] = {}

    existing_flags = item.get("constraint_flags")
    if isinstance(existing_flags, list):
        flags = [str(value) for value in existing_flags if str(value)]

    existing_params = item.get("constraint_params")
    if isinstance(existing_params, dict):
        params = dict(existing_params)

    legacy = item.get("constraints")
    if isinstance(legacy, list):
        for entry in legacy:
            if isinstance(entry, str) and entry not in flags:
                flags.append(entry)
    elif isinstance(legacy, dict):
        for key, value in legacy.items():
            if value is True or value is None:
                if key not in flags:
                    flags.append(key)
            else:
                params.setdefault(key, value)

    if flags:
        item["constraint_flags"] = flags
    if params:
        item["constraint_params"] = params


def normalize_asset_constraints(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize constraint fields across an asset in-place and return it."""
    if not isinstance(asset, dict):
        return asset

    normalize_constraints_item(asset)

    layers = asset.get("layers")
    if isinstance(layers, list):
        _normalize_layers(layers)

    components = asset.get("components")
    if isinstance(components, list):
        for component in components:
            if not isinstance(component, dict):
                continue
            normalize_constraints_item(component)
            _normalize_layers(component.get("layers") or [])

    instances = asset.get("instances")
    if isinstance(instances, list):
        for instance in instances:
            if isinstance(instance, dict):
                normalize_constraints_item(instance)

    slots = asset.get("slots")
    if isinstance(slots, list):
        for slot in slots:
            if isinstance(slot, dict):
                normalize_constraints_item(slot)

    return asset


def _normalize_layers(layers: Iterable[Any]) -> None:
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        normalize_constraints_item(layer)
        if layer.get("shape") in ("layoutRow", "layoutColumn", "layoutGrid"):
            items = layer.get("items")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        normalize_constraints_item(item)
