"""Stage 1 entry point: analyze design intent, score candidates, and recompose."""

from __future__ import annotations

from copy import deepcopy
from math import cos, radians, sin
from typing import Any

from engine.chameleon.analyzer import analyze_design
from engine.chameleon.planner import generate_candidates
from engine.chameleon.repair import repair_candidate
from engine.chameleon.scoring import score_design
from engine.chameleon.validator import validate_output


_LAST_DIAGNOSTICS: dict[str, Any] = {}


def get_last_diagnostics() -> dict[str, Any]:
    """Return a copy of the last local run's selection and score diagnostics."""
    return deepcopy(_LAST_DIAGNOSTICS)


def _placement_reason(family: str, role: str) -> str:
    if family in {"identity", "source_fit"}:
        return "preserve the source composition and fit it to the target"
    if role == "background":
        return "cover the full target as the visual backdrop"
    if family in {"banner", "banner_mirror"}:
        side = "left" if family == "banner_mirror" else "right"
        if role == "logo":
            return f"anchor the brand above the {side}-side hero area"
        if role == "hero_image":
            return f"balance the narrative copy on the {side} side"
        if role in {"headline", "subheadline", "body_copy"}:
            return "form the primary narrative column"
        if role in {"cta_text", "badge_text", "ribbon_text"}:
            return "keep the action or campaign marker grouped near the narrative"
        return "occupy a supporting position in the banner composition"
    if family in {"split", "split_mirror"}:
        if role == "hero_image":
            return "occupy the visual column opposite the narrative"
        if role in {"headline", "subheadline", "body_copy", "cta_text"}:
            return "form the narrative and action column"
        if role == "logo":
            return "anchor the brand at the edge of the narrative column"
        return "support the primary two-column composition"
    if role == "logo":
        return "anchor the brand at the top of the vertical composition"
    if role == "headline":
        return "lead the vertical narrative stack"
    if role in {"cta_text", "badge_text", "ribbon_text"}:
        return "group the action or campaign marker in the lower support area"
    return "follow the vertical narrative and supporting-content flow"


def _placement_trace(dna: Any, design: dict[str, Any], family: str) -> list[dict[str, Any]]:
    output = {str(element.get("id", "")): element for element in design.get("elements", [])}
    cw, ch = max(1.0, float(dna.target_canvas["width"])), max(1.0, float(dna.target_canvas["height"]))
    trace = []
    for fact in dna.facts:
        element = output.get(fact.id)
        if element is None:
            continue
        trace.append({
            "id": fact.id,
            "role": fact.role,
            "confidence": round(float(fact.confidence), 3),
            "group_id": fact.group_id,
            "source_rect_normalized": [
                round(float(fact.element.get("x", 0)) / max(1.0, float(dna.source["canvas"]["width"])), 4),
                round(float(fact.element.get("y", 0)) / max(1.0, float(dna.source["canvas"]["height"])), 4),
                round(float(fact.element.get("width", 0)) / max(1.0, float(dna.source["canvas"]["width"])), 4),
                round(float(fact.element.get("height", 0)) / max(1.0, float(dna.source["canvas"]["height"])), 4),
            ],
            "output_rect_normalized": [
                round(float(element.get("x", 0)) / cw, 4), round(float(element.get("y", 0)) / ch, 4),
                round(float(element.get("width", 0)) / cw, 4), round(float(element.get("height", 0)) / ch, 4),
            ],
            "reason": _placement_reason(family, fact.role),
        })
    return trace


def _safe_fallback(source: dict[str, Any], target_canvas: dict[str, Any]) -> dict[str, Any]:
    sw, sh = max(1.0, float(source["canvas"]["width"])), max(1.0, float(source["canvas"]["height"]))
    tw, th = float(target_canvas["width"]), float(target_canvas["height"])
    scale = min(tw / sw, th / sh)
    dx, dy = (tw - sw * scale) / 2, (th - sh * scale) / 2
    output = deepcopy(source)
    output["canvas"] = {"width": int(tw), "height": int(th)}
    lowest_z = min((int(e.get("z_index", 0)) for e in source.get("elements", [])), default=0)
    source_area = max(1.0, sw * sh)
    original_by_id = {str(e.get("id", "")): e for e in source.get("elements", [])}
    for element in output["elements"]:
        original = original_by_id.get(str(element.get("id", "")), {})
        if (original.get("type") == "image" and
                float(original.get("width", 0)) * float(original.get("height", 0)) / source_area >= 0.58 and
                int(original.get("z_index", 0)) <= lowest_z + 1):
            element.update(x=0.0, y=0.0, width=tw, height=th)
            continue
        x, y = dx + float(element.get("x", 0)) * scale, dy + float(element.get("y", 0)) * scale
        w, h = max(1.0, float(element.get("width", 1)) * scale), max(1.0, float(element.get("height", 1)) * scale)
        if element.get("type") == "image" and element.get("fit") != "cover":
            ratio = max(1e-6, float(element.get("width", 1)) / max(1e-6, float(element.get("height", 1))))
            if w / h > ratio:
                w = h * ratio
            else:
                h = w / ratio
        if element.get("type") == "text":
            element["font_size"] = max(1.0, float(element.get("font_size", 1)) * scale)
        angle = radians(float(element.get("rotation", 0)))
        rw, rh = abs(w * cos(angle)) + abs(h * sin(angle)), abs(w * sin(angle)) + abs(h * cos(angle))
        x = min(max(0.0, x), max(0.0, tw - w))
        y = min(max(0.0, y), max(0.0, th - h))
        # Rotation-aware center clamp keeps the complete visual bound on-canvas.
        cx, cy = x + w / 2, y + h / 2
        cx = min(max(rw / 2, cx), tw - rw / 2) if rw <= tw else tw / 2
        cy = min(max(rh / 2, cy), th - rh / 2) if rh <= th else th / 2
        element.update(x=cx - w / 2, y=cy - h / 2, width=w, height=h)
    return output


def resize(source: dict[str, Any], target_canvas: dict[str, Any]) -> dict[str, Any]:
    """Return the same design reflowed for ``target_canvas``.

    Stage 1 constraints are maintained: all source IDs, count, text, fonts,
    image references, and non-geometric properties are copied unchanged.
    Geometry and text font size are the only element fields this engine edits.
    """
    global _LAST_DIAGNOSTICS
    source_canvas = source.get("canvas", {})
    if (source_canvas.get("width") == target_canvas.get("width") and
            source_canvas.get("height") == target_canvas.get("height")):
        identity = {
            "canvas": deepcopy(target_canvas),
            "elements": deepcopy(source.get("elements", [])),
        }
        issues = validate_output(source, target_canvas, identity)
        documented_bleed_ids = {
            str(element.get("id", ""))
            for element in source.get("elements", [])
            if "intentional" in str(element.get("_note", "")).casefold()
            or "bleed" in str(element.get("_note", "")).casefold()
        }
        only_documented_bleed = all(
            issue.split(":", 1)[0] in documented_bleed_ids and "off-canvas geometry" in issue
            for issue in issues
        )
        if not issues or only_documented_bleed:
            _LAST_DIAGNOSTICS = {
                "layout_family": "identity",
                "candidate_count": 1,
                "repair_count": 0,
                "issues": issues,
                "hard_valid": not issues,
                "fallback_used": False,
            }
            return identity
    try:
        dna = analyze_design(source, target_canvas)
        candidates = generate_candidates(dna)
        reports = [(score_design(dna, item["design"], item["family"]), item, index)
                   for index, item in enumerate(candidates)]
        shortlist = sorted(reports, key=lambda row: (row[0].score, row[0].hard_valid, -row[2]), reverse=True)[:2]
        refined = []
        for initial_report, item, index in shortlist:
            design, repaired_report, repairs = repair_candidate(dna, item["design"], item["family"])
            refined.append((repaired_report, {**item, "design": design, "repairs": repairs}, index))
        # Stable order breaks ties; candidate generation is deterministic.
        report, selected, _ = max(refined, key=lambda row: (row[0].score, row[0].hard_valid, -row[2]))
        contract_issues = validate_output(source, target_canvas, selected["design"])
        if contract_issues:
            fallback = _safe_fallback(source, target_canvas)
            _LAST_DIAGNOSTICS = {
                "fallback_used": True,
                "fallback_reason": "final contract validation failed",
                "validation_issues": contract_issues,
            }
            return fallback
        _LAST_DIAGNOSTICS = {
            "layout_family": selected["family"],
            "candidate_count": len(candidates),
            "repair_count": selected.get("repairs", 0),
            "proxy_score": report.score,
            "score_components": report.components,
            "candidate_rankings": [
                {
                    "family": item["family"],
                    "variant": item["variant"],
                    "score": ranked.score,
                    "hard_valid": ranked.hard_valid,
                    "issues": ranked.issues,
                }
                for ranked, item, _ in sorted(reports, key=lambda row: (row[0].score, row[0].hard_valid), reverse=True)
            ],
            "issues": report.issues,
            "hard_valid": report.hard_valid,
            "fallback_used": False,
            "placements": _placement_trace(dna, selected["design"], selected["family"]),
            "analysis": {
                "composition": dna.composition,
                "transformation": dna.transformation,
                "groups": len(dna.groups),
                "relationships": len(dna.relationships),
                "reading_order": dna.reading_order,
                "alignment_relations": len(dna.alignments),
                "spacing_samples": len(dna.spacing_samples),
                "intentional_overlaps": dna.intentional_overlaps,
                "anchors": dna.anchor_ids,
                "repeated_groups": dna.repeated_groups,
                "role_counts": {role: sum(1 for f in dna.facts if f.role == role) for role in sorted({f.role for f in dna.facts})},
                "warnings": dna.diagnostics,
            },
        }
        return selected["design"]
    except Exception as exc:  # the contract requires a valid best-effort result, not a crash
        _LAST_DIAGNOSTICS = {"fallback_used": True, "fallback_reason": f"{type(exc).__name__}: {exc}"}
        return _safe_fallback(source, target_canvas)
