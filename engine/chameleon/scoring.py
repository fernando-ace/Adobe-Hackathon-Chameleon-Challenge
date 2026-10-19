"""Explicit internal proxy scoring with hard checks and inspectable penalties."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import cos, log, radians, sin
from typing import Any

from .model import DesignDNA
from .typography import measure_text
from .visual_analysis import background_for_design, minimum_local_contrast


@dataclass
class ScoreReport:
    score: float
    components: dict[str, float]
    issues: list[str]
    hard_valid: bool
    off_canvas_count: int
    image_ratio_failures: int
    clipped_text_count: int
    accidental_collision_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rotated_bounds(element: dict[str, Any]) -> tuple[float, float, float, float]:
    x, y = float(element.get("x", 0)), float(element.get("y", 0))
    w, h = float(element.get("width", 0)), float(element.get("height", 0))
    angle = radians(float(element.get("rotation", 0)))
    rw = abs(w * cos(angle)) + abs(h * sin(angle))
    rh = abs(w * sin(angle)) + abs(h * cos(angle))
    cx, cy = x + w / 2, y + h / 2
    return cx - rw / 2, cy - rh / 2, rw, rh


def _overlap_ratio(a: dict[str, Any], b: dict[str, Any]) -> float:
    ax, ay, aw, ah = _rotated_bounds(a)
    bx, by, bw, bh = _rotated_bounds(b)
    iw = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    return iw * ih / max(1.0, min(aw * ah, bw * bh))


def score_design(dna: DesignDNA, design: dict[str, Any], family: str = "") -> ScoreReport:
    cw, ch = float(dna.target_canvas["width"]), float(dna.target_canvas["height"])
    source_ids = [str(e.get("id", "")) for e in dna.source["elements"]]
    elements = design.get("elements", [])
    by_id = {str(e.get("id", "")): e for e in elements}
    issues: list[str] = []
    off_canvas = 0
    ratios = 0
    clipped = 0
    collisions = 0
    overflow_penalty = 0.0
    distortion_penalty = 0.0
    text_penalty = 0.0
    collision_penalty = 0.0
    group_penalty = 0.0
    adaptation_penalty = 0.0
    contrast_penalty = 0.0
    hierarchy_penalty = 0.0
    background = background_for_design(dna)
    if list(by_id) != source_ids or len(elements) != len(source_ids):
        issues.append("ID set or element count changed")
        overflow_penalty += 100.0

    # Hard checks and text measure use the same bundled font and wrapping helper as rendering.
    for fact in dna.facts:
        e = by_id.get(fact.id)
        if e is None:
            continue
        vals = [e.get(k) for k in ("x", "y", "width", "height")]
        if not all(isinstance(v, (int, float)) for v in vals):
            issues.append(f"{fact.id}: non-numeric geometry")
            overflow_penalty += 100
            continue
        x, y, w, h = map(float, vals)
        if w <= 0 or h <= 0:
            issues.append(f"{fact.id}: non-positive size")
            overflow_penalty += 70
        bx, by, bw, bh = _rotated_bounds(e)
        out = max(0.0, -bx) + max(0.0, -by) + max(0.0, bx + bw - cw) + max(0.0, by + bh - ch)
        sx, sy, sw, sh = _rotated_bounds(fact.element)
        source_canvas = dna.source["canvas"]
        source_out = (max(0.0, -sx) + max(0.0, -sy) +
                      max(0.0, sx + sw - float(source_canvas["width"])) +
                      max(0.0, sy + sh - float(source_canvas["height"])))
        note = str(fact.element.get("_note", "")).casefold()
        inherited_bleed = (
            source_out > 0.5 and ("intentional" in note or "bleed" in note) and
            out / max(cw, ch) <= source_out / max(float(source_canvas["width"]), float(source_canvas["height"])) + 0.01
        )
        if out > 0.5 and not inherited_bleed:
            off_canvas += 1
            overflow_penalty += min(30.0, 5.0 + out / max(cw, ch) * 40)
            issues.append(f"{fact.id}: rotated bounds exceed target canvas")
        if fact.type == "image" and fact.id not in dna.background_ids and e.get("fit") != "cover":
            source_ratio = max(1e-6, float(fact.element.get("width", 1)) / max(1e-6, float(fact.element.get("height", 1))))
            output_ratio = w / max(h, 1e-6)
            deviation = abs(output_ratio / source_ratio - 1)
            if deviation > 0.05:
                ratios += 1
                distortion_penalty += min(50, 24 + deviation * 40)
                issues.append(f"{fact.id}: image aspect ratio changed by {deviation:.1%}")
        if fact.type == "text":
            source = fact.element
            if e.get("content") != source.get("content") or e.get("font_family") != source.get("font_family"):
                text_penalty += 100
                issues.append(f"{fact.id}: Stage 1 copy/font changed")
            measure = measure_text(e, w, h, float(e.get("font_size", 1)))
            if not measure.fits:
                clipped += 1
                severity = max(0.0, measure.required_height - h) / max(1.0, h) + max(0.0, measure.widest_line - w) / max(1.0, w)
                penalty = (11 if fact.role in {"headline", "cta_text"} else 7 if fact.role in {"subheadline", "body_copy"} else 3) * (1 + min(2.0, severity))
                text_penalty += penalty
                issues.append(f"{fact.id}: text exceeds measured box ({measure.line_count} lines, needs {measure.required_height:.1f}px high)")
            size = float(e.get("font_size", 1))
            floor = {"headline": 10.0, "subheadline": 8.0, "body_copy": 7.0, "legal": 4.0,
                     "cta_text": 7.0, "badge_text": 5.0}.get(fact.role, 6.0)
            if size < floor:
                text_penalty += (floor - size) * (0.8 if fact.role == "legal" else 1.4)
                issues.append(f"{fact.id}: small type at {size:.1f}px")
            if background is not None:
                ratio = minimum_local_contrast(e, background)
                if ratio is not None:
                    threshold = 3.0 if size >= 24 or (str(e.get("font_weight", "")) == "bold" and size >= 18.5) else 4.5
                    if ratio < threshold:
                        contrast_penalty += min(8.0, (threshold - ratio) * (1.2 if fact.importance >= 0.45 else 0.5))
                        issues.append(f"{fact.id}: low sampled text/background contrast ({ratio:.2f}:1)")

    # A pair only escapes collision cost when the source indicates an intentional
    # overlap, they are grouped, one is the full-bleed background, or a low-z
    # decorative shape sits behind another element.
    intentional_pairs = set()
    source_overlap_ratio = {}
    for rel in dna.relationships:
        if rel.kind == "overlaps":
            pair = frozenset((rel.source_id, rel.target_id))
            if rel.intentional:
                intentional_pairs.add(pair)
            else:
                source_a, source_b = dna.by_id.get(rel.source_id), dna.by_id.get(rel.target_id)
                if source_a is not None and source_b is not None:
                    source_overlap_ratio[pair] = _overlap_ratio(source_a.element, source_b.element)
    for i, a in enumerate(elements):
        aid = str(a.get("id", ""))
        af = dna.by_id.get(aid)
        if aid in dna.background_ids:
            continue
        for b in elements[i + 1:]:
            bid = str(b.get("id", ""))
            bf = dna.by_id.get(bid)
            if bid in dna.background_ids or af is None or bf is None:
                continue
            if af.group_id and af.group_id == bf.group_id:
                continue
            if frozenset((aid, bid)) in intentional_pairs:
                continue
            if (af.role == "decoration" and int(a.get("z_index", 0)) < int(b.get("z_index", 0))) or (bf.role == "decoration" and int(b.get("z_index", 0)) < int(a.get("z_index", 0))):
                continue
            overlap = _overlap_ratio(a, b)
            prior_overlap = source_overlap_ratio.get(frozenset((aid, bid)), 0.0)
            if overlap > max(0.025, prior_overlap + 0.015):
                collisions += 1
                severity = min(1.0, overlap)
                collision_penalty += 12.0 * severity * max(0.45, af.importance, bf.importance)
                issues.append(f"{aid}/{bid}: new overlap ({overlap:.0%} of smaller element)")

    # Keep multi-element groups spatially coherent even when each child is legal.
    for gid, ids in dna.groups.items():
        present = [by_id[i] for i in ids if i in by_id]
        if len(present) < 2:
            continue
        centers = [(float(e["x"]) + float(e["width"]) / 2, float(e["y"]) + float(e["height"]) / 2) for e in present]
        spread = max(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5 for x1, y1 in centers for x2, y2 in centers)
        source_group = [dna.by_id[i].element for i in ids]
        src_spread = max(1.0, max(((float(a.get("x", 0)) - float(b.get("x", 0))) ** 2 + (float(a.get("y", 0)) - float(b.get("y", 0))) ** 2) ** 0.5 for a in source_group for b in source_group))
        if spread > max(cw, ch) * 0.6 and spread / max(cw, ch) > src_spread / max(float(dna.source["canvas"]["width"]), float(dna.source["canvas"]["height"])) * 1.7:
            group_penalty += 12
            issues.append(f"group {gid}: members are widely separated")

    text_facts = [fact for fact in dna.facts if fact.type == "text" and fact.id in by_id]
    hierarchy_rank = {"headline": 4, "subheadline": 3, "event_metadata": 3, "body_copy": 2, "cta_text": 2,
                      "badge_text": 1, "ribbon_text": 1, "legal": 0}
    for i, a in enumerate(text_facts):
        for b in text_facts[i + 1:]:
            ra, rb = hierarchy_rank.get(a.role, 1), hierarchy_rank.get(b.role, 1)
            if ra == rb:
                continue
            higher, lower = (a, b) if ra > rb else (b, a)
            high_size = float(by_id[higher.id].get("font_size", 1))
            low_size = float(by_id[lower.id].get("font_size", 1))
            source_high = float(higher.element.get("font_size", 1))
            source_low = float(lower.element.get("font_size", 1))
            source_ratio = source_high / max(1.0, source_low)
            output_ratio = high_size / max(1.0, low_size)
            # Preserve the source's own typographic relationship. Penalize a
            # candidate only when it degrades that relationship (or crosses
            # the default hierarchy floor), not when the source already does.
            minimum_ratio = max(0.0, min(0.82, source_ratio) - 0.01)
            if output_ratio < minimum_ratio:
                penalty = min(5.0, (minimum_ratio - output_ratio) * 12)
                hierarchy_penalty += penalty
                issues.append(f"{higher.id}/{lower.id}: type hierarchy regressed from source ({source_ratio:.2f} to {output_ratio:.2f})")

    # Adaptation must be appropriate to the target's shape. This stops a
    # mathematically tidy but visibly crushed square/poster arrangement from
    # winning in a wide-banner task.
    if dna.target_aspect >= 1.75:
        if family in {"source_fit", "stack"}:
            adaptation_penalty += 18.0
        elif family.startswith("split"):
            adaptation_penalty += 8.0
        for fact in dna.facts:
            if fact.role == "hero_image" and fact.id in by_id and fact.id not in dna.background_ids:
                e = by_id[fact.id]
                area_share = float(e.get("width", 0)) * float(e.get("height", 0)) / max(1.0, cw * ch)
                if area_share < 0.055:
                    adaptation_penalty += min(8.0, (0.055 - area_share) * 120)
    elif dna.target_aspect < 0.72 and family.startswith("banner"):
        adaptation_penalty += 14.0
    # Keep the source composition intact for near-identical and minor changes;
    # charge the source-fit family only when a real aspect-ratio reflow is due.
    if family == "source_fit" and dna.transformation not in {"near_identical", "minor_change"}:
        aspect_shift = abs(log(max(1e-6, dna.target_aspect) / max(1e-6, dna.source_aspect)))
        if aspect_shift > 0.12:
            adaptation_penalty += min(18.0, (aspect_shift - 0.12) * 24.0)
        if dna.transformation in {"extreme_change", "ultra_wide", "ultra_tall"}:
            adaptation_penalty += 8.0

    # Prefer a controlled, target-filling composition without rewarding edge crowding.
    non_background = [e for e in elements if str(e.get("id", "")) not in dna.background_ids]
    if non_background:
        important_ids = {f.id for f in dna.facts if f.importance >= 0.45 and f.role not in {"background", "decoration", "legal"}}
        primary = [e for e in non_background if str(e.get("id", "")) in important_ids] or non_background
        xs = [float(e.get("x", 0)) for e in primary]
        ys = [float(e.get("y", 0)) for e in primary]
        x2 = [float(e.get("x", 0)) + float(e.get("width", 0)) for e in primary]
        y2 = [float(e.get("y", 0)) + float(e.get("height", 0)) for e in primary]
        coverage = max(0, max(x2) - min(xs)) * max(0, max(y2) - min(ys)) / max(1.0, cw * ch)
        underuse_penalty = max(0.0, 0.15 - coverage) * 20.0
        vertical_fill, horizontal_fill = (max(y2) - min(ys)) / max(1.0, ch), (max(x2) - min(xs)) / max(1.0, cw)
        if dna.target_aspect < 0.9 and dna.target_canvas["height"] > dna.source["canvas"]["height"]:
            underuse_penalty += max(0.0, 0.56 - vertical_fill) * 24.0
        if dna.target_aspect > 1.75:
            underuse_penalty += max(0.0, 0.62 - horizontal_fill) * 12.0
    else:
        underuse_penalty = 20.0
    score = max(0.0, 100.0 - overflow_penalty - distortion_penalty - text_penalty - collision_penalty - group_penalty - underuse_penalty - adaptation_penalty - contrast_penalty - hierarchy_penalty)
    components = {
        "canvas_legality": round(max(0.0, 100.0 - overflow_penalty), 2),
        "image_fidelity": round(max(0.0, 100.0 - distortion_penalty), 2),
        "typography": round(max(0.0, 100.0 - text_penalty), 2),
        "collision_avoidance": round(max(0.0, 100.0 - collision_penalty), 2),
        "group_coherence": round(max(0.0, 100.0 - group_penalty), 2),
        "canvas_use": round(max(0.0, 100.0 - underuse_penalty), 2),
        "target_adaptation": round(max(0.0, 100.0 - adaptation_penalty), 2),
        "sampled_contrast": round(max(0.0, 100.0 - contrast_penalty), 2),
        "visual_hierarchy": round(max(0.0, 100.0 - hierarchy_penalty), 2),
    }
    hard_valid = not off_canvas and not ratios and not clipped and len(by_id) == len(source_ids) and not any("Stage 1 copy/font changed" in i for i in issues)
    return ScoreReport(round(score, 2), components, issues, hard_valid, off_canvas, ratios, clipped, collisions)
