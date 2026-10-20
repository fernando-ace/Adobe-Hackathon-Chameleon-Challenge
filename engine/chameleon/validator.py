"""Final contract validation independent from the candidate ranking score."""

from __future__ import annotations

import math
from typing import Any


_REQUIRED = {
    "text": ("content", "font_family", "font_size", "color"),
    "image": ("asset_id",),
    "shape": ("shape_type", "fill_color"),
}


def validate_output(source: dict[str, Any], target: dict[str, Any], output: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    canvas = output.get("canvas")
    elements = output.get("elements")
    if not isinstance(canvas, dict) or not isinstance(elements, list):
        return ["output must contain canvas object and elements array"]
    if canvas != target:
        issues.append("output canvas differs from requested target")
    ids = [str(e.get("id", "")) for e in elements if isinstance(e, dict)]
    source_ids = [str(e.get("id", "")) for e in source.get("elements", [])]
    if len(elements) != len(source_ids) or len(ids) != len(set(ids)) or set(ids) != set(source_ids):
        issues.append("output element IDs/count differ from source")
    src_by_id = {str(e.get("id", "")): e for e in source.get("elements", [])}
    width, height = canvas.get("width", 0), canvas.get("height", 0)
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        issues.append("output canvas dimensions must be positive integers")
        return issues
    for element in elements:
        if not isinstance(element, dict):
            issues.append("elements array contains a non-object")
            continue
        eid = str(element.get("id", ""))
        for key in ("id", "type", "x", "y", "width", "height"):
            if key not in element:
                issues.append(f"{eid}: missing required field {key}")
        for key in ("x", "y", "width", "height"):
            value = element.get(key)
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                issues.append(f"{eid}: {key} must be a finite number")
        if not all(isinstance(element.get(k), (int, float)) and math.isfinite(float(element[k])) for k in ("x", "y", "width", "height")):
            continue
        x, y, w, h = (float(element[k]) for k in ("x", "y", "width", "height"))
        if w <= 0 or h <= 0 or x < -0.5 or y < -0.5 or x + w > width + 0.5 or y + h > height + 0.5:
            original = src_by_id.get(eid)
            source_canvas = source.get("canvas", {})
            inherited_bleed = False
            note = str(original.get("_note", "")).casefold() if original is not None else ""
            if original is not None and ("intentional" in note or "bleed" in note):
                ox, oy = float(original.get("x", 0)), float(original.get("y", 0))
                ow, oh = float(original.get("width", 0)), float(original.get("height", 0))
                source_width = max(1.0, float(source_canvas.get("width", width)))
                source_height = max(1.0, float(source_canvas.get("height", height)))
                current_edges = (max(0.0, -x), max(0.0, -y), max(0.0, x + w - width), max(0.0, y + h - height))
                source_edges = (max(0.0, -ox), max(0.0, -oy), max(0.0, ox + ow - source_width), max(0.0, oy + oh - source_height))
                inherited_bleed = any(edge > 0 for edge in source_edges) and all(
                    current / target_size <= prior / source_size + 0.01
                    for current, prior, target_size, source_size in zip(
                        current_edges, source_edges, (width, height, width, height), (source_width, source_height, source_width, source_height)
                    )
                )
            if not inherited_bleed:
                issues.append(f"{eid}: invalid or off-canvas geometry")
        for key in _REQUIRED.get(str(element.get("type")), ()):
            if key not in element:
                issues.append(f"{eid}: missing type-specific field {key}")
        original = src_by_id.get(eid)
        if original is None:
            continue
        editable = {"x", "y", "width", "height"}
        if original.get("type") == "text":
            editable.add("font_size")
        for key, value in original.items():
            if key not in editable and element.get(key) != value:
                issues.append(f"{eid}: non-layout property changed: {key}")
        if element.get("type") != original.get("type"):
            issues.append(f"{eid}: element type changed")
        if original.get("type") == "text":
            if element.get("content") != original.get("content"):
                issues.append(f"{eid}: text content changed")
            if element.get("font_family") != original.get("font_family"):
                issues.append(f"{eid}: font family changed")
            size = element.get("font_size")
            if not isinstance(size, (int, float)) or not math.isfinite(float(size)) or float(size) < 1:
                issues.append(f"{eid}: font size must be finite and at least 1")
        if original.get("type") == "image" and element.get("asset_id") != original.get("asset_id"):
            issues.append(f"{eid}: image asset reference changed")
    return issues
