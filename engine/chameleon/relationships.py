"""Pairwise source-structure cues used to preserve composition intent."""

from __future__ import annotations

from typing import Any

from .model import Relationship


def extract_relationships(elements: list[dict[str, Any]]) -> list[Relationship]:
    rels: list[Relationship] = []
    for i, a in enumerate(elements):
        ax, ay = float(a.get("x", 0)), float(a.get("y", 0))
        aw, ah = float(a.get("width", 0)), float(a.get("height", 0))
        for b in elements[i + 1:]:
            bx, by = float(b.get("x", 0)), float(b.get("y", 0))
            bw, bh = float(b.get("width", 0)), float(b.get("height", 0))
            dx, dy = (bx + bw / 2) - (ax + aw / 2), (by + bh / 2) - (ay + ah / 2)
            distance = (dx * dx + dy * dy) ** 0.5
            scale = max(1.0, (aw * ah) ** 0.5 + (bw * bh) ** 0.5)
            overlap_x = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
            overlap_y = max(0.0, min(ay + ah, by + bh) - max(ay, by))
            overlap = overlap_x * overlap_y > 0
            same_group = a.get("group_id") is not None and a.get("group_id") == b.get("group_id")
            if same_group:
                rels.append(Relationship(str(a.get("id")), str(b.get("id")), "same_group", 1.0, True))
            if overlap:
                za, zb = int(a.get("z_index", 0)), int(b.get("z_index", 0))
                intent = same_group or za != zb or a.get("type") == "shape" or b.get("type") == "shape"
                rels.append(Relationship(str(a.get("id")), str(b.get("id")), "overlaps", min(1.0, overlap_x * overlap_y / max(1.0, min(aw * ah, bw * bh))), intent))
            if distance <= scale * 0.55:
                rels.append(Relationship(str(a.get("id")), str(b.get("id")), "near", max(0.1, 1.0 - distance / (scale * 0.55)), same_group))
            if abs(dy) <= max(12.0, min(ah, bh) * 0.22):
                rels.append(Relationship(str(a.get("id")), str(b.get("id")), "same_row", 0.55, False))
            if abs(dx) <= max(12.0, min(aw, bw) * 0.22):
                rels.append(Relationship(str(a.get("id")), str(b.get("id")), "same_column", 0.55, False))
            if ax <= bx and ay <= by and ax + aw >= bx + bw and ay + ah >= by + bh:
                rels.append(Relationship(str(b.get("id")), str(a.get("id")), "contained_by", 0.9, True))
            if bx <= ax and by <= ay and bx + bw >= ax + aw and by + bh >= ay + ah:
                rels.append(Relationship(str(a.get("id")), str(b.get("id")), "contained_by", 0.9, True))
            if not overlap and not same_group and abs(dy) > abs(dx):
                rels.append(Relationship(str(a.get("id")), str(b.get("id")), "above" if dy > 0 else "below", 0.3, False))
            elif not overlap and not same_group:
                rels.append(Relationship(str(a.get("id")), str(b.get("id")), "left_of" if dx > 0 else "right_of", 0.3, False))
    return rels
