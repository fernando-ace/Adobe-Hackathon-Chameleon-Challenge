"""Small deterministic repair loop driven by diagnosed geometry violations."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from .model import DesignDNA
from .scoring import ScoreReport, score_design


_PAIR = re.compile(r"^([^/ :]+)/([^:]+): new overlap")
_SINGLE = re.compile(r"^([^:]+): rotated bounds exceed target canvas")


def _shift_unit(dna: DesignDNA, design: dict[str, Any], element_id: str, dx: float, dy: float) -> None:
    fact = dna.by_id.get(element_id)
    if fact is None:
        return
    ids = dna.groups.get(fact.group_id, [element_id]) if fact.group_id else [element_id]
    for eid in ids:
        element = next((e for e in design["elements"] if str(e.get("id", "")) == eid), None)
        if element is None:
            continue
        w, h = float(element.get("width", 0)), float(element.get("height", 0))
        element["x"] = min(max(0.0, float(element.get("x", 0)) + dx), max(0.0, float(dna.target_canvas["width"]) - w))
        element["y"] = min(max(0.0, float(element.get("y", 0)) + dy), max(0.0, float(dna.target_canvas["height"]) - h))


def _candidate_moves(dna: DesignDNA, design: dict[str, Any], element_id: str) -> list[dict[str, Any]]:
    w, h = float(dna.target_canvas["width"]), float(dna.target_canvas["height"])
    gap = max(2.0, min(w, h) * 0.04)
    trials = []
    for distance in (gap, gap * 2, gap * 4):
        for dx, dy in ((distance, 0), (-distance, 0), (0, distance), (0, -distance)):
            trial = deepcopy(design)
            _shift_unit(dna, trial, element_id, dx, dy)
            trials.append(trial)
    return trials


def repair_candidate(
    dna: DesignDNA, design: dict[str, Any], family: str, max_repairs: int | None = None,
) -> tuple[dict[str, Any], ScoreReport, int]:
    """Move lower-priority units away from diagnosed violations, keeping only gains."""
    current = deepcopy(design)
    report = score_design(dna, current, family)
    repairs = 0
    if max_repairs is None:
        max_repairs = min(32, max(6, len(dna.facts) // 2))

    def rank(candidate_report: ScoreReport) -> tuple[Any, ...]:
        return (
            candidate_report.hard_valid,
            candidate_report.clipped_text_count == 0,
            -candidate_report.image_ratio_failures,
            -candidate_report.off_canvas_count,
            -candidate_report.clipped_text_count,
            -candidate_report.accidental_collision_count,
            candidate_report.components.get("typography", 0.0),
            candidate_report.score,
        )

    for _ in range(max_repairs):
        pair_ids = None
        single_id = None
        for issue in report.issues:
            match = _PAIR.match(issue)
            if match:
                pair_ids = (match.group(1), match.group(2))
                break
            match = _SINGLE.match(issue)
            if match:
                single_id = match.group(1)
                break
        if pair_ids:
            a, b = pair_ids
            fa, fb = dna.by_id.get(a), dna.by_id.get(b)
            if fa is None or fb is None:
                break
            mover = a if fa.importance < fb.importance else b
        elif single_id:
            mover = single_id
        else:
            break
        best_design, best_report = current, report
        for trial in _candidate_moves(dna, current, mover):
            candidate_report = score_design(dna, trial, family)
            if rank(candidate_report) > rank(best_report):
                best_design, best_report = trial, candidate_report
        if best_design is current:
            break
        current, report = best_design, best_report
        repairs += 1
    return current, report, repairs
