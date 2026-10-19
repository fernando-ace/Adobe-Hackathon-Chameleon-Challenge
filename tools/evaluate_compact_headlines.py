"""Compare compact-banner headline fitting with the pre-change planner.

The deterministic synthetic holdout varies copy length, target ratio, source
element count, grouped ornaments, rotation, transparency, and hero proportions.
All quality metrics are internal diagnostics, not Adobe's hidden evaluator.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

from engine.chameleon.analyzer import analyze_design
from engine.chameleon.scoring import score_design
import engine.resize as resize_module
from engine.resize import get_last_diagnostics, resize
from tests.test_engine import _official_tasks


ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "47f805b"
TARGETS = [(728, 90), (970, 90), (600, 90), (800, 90), (640, 80), (320, 50)]
COPY_LENGTHS = [48, 64, 80, 96, 112, 128, 144]
PHRASE = "Introducing a fresh botanical sparkling collection for warm summer evenings and golden hour gatherings. "


def _cases() -> list[tuple[str, dict[str, Any], dict[str, int]]]:
    base = next(t["source"] for t in _official_tasks() if t["difficulty"] == "level_3_advanced")
    cases = []
    for ti, (width, height) in enumerate(TARGETS):
        for li, length in enumerate(COPY_LENGTHS):
            source = copy.deepcopy(base)
            headline = next(e for e in source["elements"] if e["id"] == "headline")
            headline["content"] = (PHRASE * 3)[:length]
            # Exercise transparent asset proportions without replacing pixels.
            hero = next(e for e in source["elements"] if e["id"] == "product")
            hero["width"] *= (0.82, 1.0, 1.18)[(ti + li) % 3]
            # Vary existing group membership/ornaments while retaining the
            # single supporting line required by the compact wide-copy rule.
            if (ti + li) % 3 == 0:
                source["elements"] = [e for e in source["elements"] if e["id"] not in {"ribbon_bg", "ribbon_label"}]
            if (ti + li) % 4 == 0:
                source["elements"] = [e for e in source["elements"] if e["id"] not in {"badge3_bg", "badge3_label"}]
            source["elements"].append({
                "id": f"holdout_mark_{ti}_{li}", "type": "shape",
                "x": source["canvas"]["width"] * 0.48,
                "y": source["canvas"]["height"] * 0.52,
                "width": source["canvas"]["width"] * 0.025,
                "height": source["canvas"]["height"] * 0.08,
                "shape_type": "ellipse", "fill_color": "rgba(255,255,255,0.35)",
                "opacity": 0.4, "rotation": (ti + li) * 7 % 45, "z_index": 4,
            })
            cases.append((f"{width}x{height}_copy{length}", source,
                          {"width": width, "height": height}))
    return cases


def _baseline_generator() -> Callable[..., Any]:
    code = subprocess.check_output(
        ["git", "show", f"{BASELINE_COMMIT}:engine/chameleon/planner.py"],
        cwd=ROOT, text=True,
    )
    with tempfile.TemporaryDirectory(prefix="chameleon-planner-") as temp:
        path = Path(temp) / "planner_baseline.py"
        path.write_text(code, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("engine.chameleon.planner_baseline", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load baseline planner")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.generate_candidates


def _evaluate(generator: Callable[..., Any], cases: list[tuple[str, dict[str, Any], dict[str, int]]]) -> list[dict[str, Any]]:
    resize_module.generate_candidates = generator
    rows = []
    for name, source, target in cases:
        started = time.perf_counter()
        output = resize(source, target)
        elapsed = time.perf_counter() - started
        diagnostics = get_last_diagnostics()
        dna = analyze_design(source, target, ROOT / "brand_kit/assets")
        report = score_design(dna, output, diagnostics["layout_family"])
        headline = next(e for e in output["elements"] if e["id"] == "headline")
        rows.append({
            "case": name,
            "headline_font_px": headline["font_size"],
            "hard_valid": report.hard_valid,
            "clipped_text_count": report.clipped_text_count,
            "new_collision_count": report.accidental_collision_count,
            "image_ratio_failures": report.image_ratio_failures,
            "fallback_used": diagnostics["fallback_used"],
            "runtime_seconds": round(elapsed, 6),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/benchmark/compact-headline-holdout.json")
    args = parser.parse_args()
    cases = _cases()
    current_generator = resize_module.generate_candidates
    before = _evaluate(_baseline_generator(), cases)
    after = _evaluate(current_generator, cases)
    resize_module.generate_candidates = current_generator
    rows = [{"case": a["case"], "before": b, "after": a} for b, a in zip(before, after)]
    summary = {}
    for side, results in (("before", before), ("after", after)):
        sizes = [r["headline_font_px"] for r in results]
        summary[f"{side}_mean_headline_font_px"] = round(statistics.mean(sizes), 4)
        summary[f"{side}_minimum_headline_font_px"] = round(min(sizes), 4)
        runtimes = sorted(r["runtime_seconds"] for r in results)
        summary[f"{side}_median_runtime_seconds"] = round(statistics.median(runtimes), 6)
        summary[f"{side}_p95_runtime_seconds"] = round(runtimes[min(len(runtimes) - 1, int(len(runtimes) * 0.95))], 6)
        for metric in ("hard_valid", "clipped_text_count", "new_collision_count", "image_ratio_failures", "fallback_used"):
            label = "invalid_cases" if metric == "hard_valid" else metric
            summary[f"{side}_{label}"] = sum((not r[metric]) if metric == "hard_valid" else bool(r[metric]) for r in results)
    summary["headline_improved_cases"] = sum(a["headline_font_px"] > b["headline_font_px"] for b, a in zip(before, after))
    summary["case_count"] = len(cases)
    artifact = {
        "label": "synthetic robustness holdout; internal metrics, not Adobe hidden-set evidence",
        "baseline_commit": BASELINE_COMMIT,
        "target_sizes": [dict(width=w, height=h) for w, h in TARGETS],
        "copy_lengths_characters": COPY_LENGTHS,
        "summary": summary,
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.relative_to(ROOT)), "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
