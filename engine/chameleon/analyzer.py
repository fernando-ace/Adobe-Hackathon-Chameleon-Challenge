"""Extract Design DNA, image metadata, semantic roles, and source structure."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from .model import DesignDNA, ElementFacts
from .relationships import extract_relationships
from .semantics import infer_roles


def _transformation(source_ratio: float, target_ratio: float) -> str:
    change = abs(target_ratio / max(source_ratio, 1e-6) - 1)
    if change < 0.08:
        return "near_identical"
    if change < 0.22:
        return "minor_change"
    if change < 0.55:
        return "moderate_change"
    if target_ratio > 2.4:
        return "ultra_wide"
    if target_ratio < 0.42:
        return "ultra_tall"
    return "extreme_change"


def analyze_design(
    source: dict[str, Any], target_canvas: dict[str, Any],
    assets_dir: str | Path = "brand_kit/assets",
) -> DesignDNA:
    canvas = source["canvas"]
    sw, sh = float(canvas["width"]), float(canvas["height"])
    tw, th = float(target_canvas["width"]), float(target_canvas["height"])
    source_area = max(1.0, sw * sh)
    roles = infer_roles(source["elements"], canvas)
    groups: dict[str, list[str]] = {}
    backgrounds: set[str] = set()
    facts: list[ElementFacts] = []
    diagnostics: list[str] = []
    root = Path(assets_dir)
    for e in source["elements"]:
        x, y = float(e.get("x", 0)), float(e.get("y", 0))
        w, h = max(0.0, float(e.get("width", 0))), max(0.0, float(e.get("height", 0)))
        eid = str(e.get("id", ""))
        role, confidence, importance = roles.get(eid, ("unknown", 0.0, 0.4))
        gid = str(e["group_id"]) if e.get("group_id") is not None else None
        if gid:
            groups.setdefault(gid, []).append(eid)
        if role == "background":
            backgrounds.add(eid)
        asset_size = None
        alpha_bounds = None
        luminance = None
        if e.get("type") == "image":
            path = root / str(e.get("asset_id", ""))
            if path.is_file():
                try:
                    with Image.open(path) as im:
                        asset_size = im.size
                        rgba = im.convert("RGBA")
                        alpha_bounds = rgba.getchannel("A").getbbox()
                        rgb = rgba.convert("RGB")
                        rgb.thumbnail((64, 64), Image.Resampling.LANCZOS)
                        pixels = [rgb.getpixel((x, y)) for y in range(rgb.height) for x in range(rgb.width)]
                        if pixels:
                            def linear(c: int) -> float:
                                value = c / 255.0
                                return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
                            luminance = sum(0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)
                                            for r, g, b in pixels) / len(pixels)
                except (OSError, ValueError) as exc:
                    diagnostics.append(f"Could not inspect image asset for {eid}: {exc}")
            else:
                diagnostics.append(f"Image asset unavailable for {eid}; preserved reference without pixel analysis.")
        facts.append(ElementFacts(
            element=e, role=role, confidence=confidence, importance=importance,
            center=((x + w / 2) / max(1.0, sw), (y + h / 2) / max(1.0, sh)),
            normalized_box=(x / max(1.0, sw), y / max(1.0, sh), w / max(1.0, sw), h / max(1.0, sh)),
            area_fraction=(w * h) / source_area, aspect_ratio=w / max(h, 1e-6),
            group_id=gid, asset_size=asset_size, alpha_bounds=alpha_bounds, luminance=luminance,
        ))
    # Describe source layout at a coarse level, without assuming a specific template.
    images = [f for f in facts if f.role == "hero_image"]
    text = [f for f in facts if f.type == "text" and f.role in {"headline", "subheadline", "body_copy"}]
    if images and text and min(f.center[0] for f in images) > max(f.center[0] for f in text) + 0.12:
        composition = "copy_left_hero_right"
    elif images and text and max(f.center[0] for f in images) < min(f.center[0] for f in text) - 0.12:
        composition = "hero_left_copy_right"
    elif images and text:
        composition = "centered_stack"
    elif len(text) >= 2:
        composition = "typographic_stack"
    else:
        composition = "freeform"
    relationships = extract_relationships(source["elements"])
    reading_order = [f.id for f in sorted(
        (f for f in facts if f.role not in {"background", "decoration", "logo"}),
        key=lambda f: (f.center[1], f.center[0], int(f.element.get("z_index", 0))),
    )]
    alignments = []
    spacing_samples = []
    for i, a in enumerate(facts):
        ax, ay, aw, ah = a.normalized_box
        for b in facts[i + 1:]:
            bx, by, bw, bh = b.normalized_box
            for kind, delta in (("left", abs(ax - bx)), ("center_x", abs((ax + aw / 2) - (bx + bw / 2))),
                                ("right", abs((ax + aw) - (bx + bw))), ("top", abs(ay - by)),
                                ("center_y", abs((ay + ah / 2) - (by + bh / 2))), ("bottom", abs((ay + ah) - (by + bh)))):
                if delta <= 0.025:
                    alignments.append((a.id, b.id, kind, delta))
            distance = ((a.center[0] - b.center[0]) ** 2 + (a.center[1] - b.center[1]) ** 2) ** 0.5
            if distance < 0.35:
                spacing_samples.append((a.id, b.id, distance))
    intentional_overlaps = [(r.source_id, r.target_id) for r in relationships if r.kind == "overlaps" and r.intentional]
    anchors = [f.id for f in sorted((f for f in facts if f.role not in {"background", "decoration", "legal"}),
                                    key=lambda f: (f.importance, f.area_fraction, -int(f.element.get("z_index", 0))), reverse=True)[:3]]
    group_signatures: dict[tuple[str, int], list[str]] = {}
    for gid, ids in groups.items():
        shape_kinds = sorted(str(next((e.get("shape_type") for e in source["elements"] if str(e.get("id")) == eid), "")) for eid in ids)
        group_signatures.setdefault(("|".join(shape_kinds), len(ids)), []).append(gid)
    repeated_groups = [ids for ids in group_signatures.values() if len(ids) > 1]
    return DesignDNA(
        source=source, target_canvas={"width": int(tw), "height": int(th)}, facts=facts,
        relationships=relationships, groups=groups,
        background_ids=backgrounds, composition=composition,
        transformation=_transformation(sw / max(sh, 1.0), tw / max(th, 1.0)),
        source_aspect=sw / max(sh, 1.0), target_aspect=tw / max(th, 1.0),
        reading_order=reading_order, alignments=alignments, spacing_samples=spacing_samples,
        intentional_overlaps=intentional_overlaps, anchor_ids=anchors,
        repeated_groups=repeated_groups, diagnostics=diagnostics,
    )
