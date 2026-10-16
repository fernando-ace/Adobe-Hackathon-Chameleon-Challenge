"""Run the official, stress, mutation, rendering, and determinism benchmark."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
import statistics
import time
from typing import Any

from engine.chameleon.analyzer import analyze_design
from engine.chameleon.scoring import score_design
from engine.resize import get_last_diagnostics, resize
from renderer.converter.convert import render_design_to_png
from tools.stress_corpus import STRESS_CASES, make_mutations, make_stress_corpus


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
OFFICIAL = EVIDENCE / "official"
FINAL = EVIDENCE / "final"
BENCH = EVIDENCE / "benchmark"
GALLERY = EVIDENCE / "gallery"


def _load_tasks() -> list[dict[str, Any]]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "input").glob("*.json"))]


def _canonical(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _record_case(name: str, source: dict[str, Any], target: dict[str, int], output: dict[str, Any], family: str, elapsed: float) -> dict[str, Any]:
    dna = analyze_design(source, target, ROOT / "brand_kit/assets")
    report = score_design(dna, output, family)
    return {
        "name": name,
        "layout_family": family,
        "proxy_score": report.score,
        "hard_valid": report.hard_valid,
        "off_canvas_count": report.off_canvas_count,
        "image_ratio_failures": report.image_ratio_failures,
        "clipped_text_count": report.clipped_text_count,
        "accidental_collision_count": report.accidental_collision_count,
        "runtime_seconds": round(elapsed, 5),
        "issues": report.issues,
    }


def main() -> int:
    for folder in (OFFICIAL, FINAL, BENCH, GALLERY):
        folder.mkdir(parents=True, exist_ok=True)
    tasks = _load_tasks()
    official_rows = []
    gallery_rows = []
    for task in tasks:
        stem = Path(task["task_id"]).stem
        source, target = task["source"], task["target_canvas"]
        source_png = OFFICIAL / f"{stem}_source.png"
        warnings = render_design_to_png(source, ROOT / "brand_kit/assets", source_png, ROOT / "brand_kit/fonts")
        # Filenames derive from the actual input stem and remain sample-ID agnostic.
        input_stem = next(p.stem for p in (ROOT / "input").glob("*.json") if json.loads(p.read_text(encoding="utf-8"))["task_id"] == task["task_id"])
        baseline_path = EVIDENCE / "baseline" / f"{input_stem}_output.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        dna = analyze_design(source, target, ROOT / "brand_kit/assets")
        baseline_report = score_design(dna, baseline, "source_fit")
        started = time.perf_counter()
        output = resize(source, target)
        elapsed = time.perf_counter() - started
        diag = get_last_diagnostics()
        current_json = FINAL / f"{input_stem}_output.json"
        current_png = FINAL / f"{input_stem}_output.png"
        current_json.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        warnings_current = render_design_to_png(output, ROOT / "brand_kit/assets", current_png, ROOT / "brand_kit/fonts")
        current_report = score_design(dna, output, diag.get("layout_family", ""))
        official_rows.append({
            "input": input_stem,
            "difficulty": task.get("difficulty"),
            "source_canvas": source["canvas"],
            "target_canvas": target,
            "element_count": len(source["elements"]),
            "baseline": baseline_report.to_dict(),
            "current": current_report.to_dict(),
            "layout_family": diag.get("layout_family"),
            "candidate_count": diag.get("candidate_count"),
            "repair_count": diag.get("repair_count"),
            "runtime_seconds": round(elapsed, 5),
            "renderer_warnings": warnings_current,
            "source_renderer_warnings": warnings,
        })
        gallery_rows.append((input_stem, task.get("difficulty", ""), target, source_png, EVIDENCE / "baseline" / f"{input_stem}_output.png", current_png))

    stress_rows = []
    stress_deterministic = 0
    for name, source, target in make_stress_corpus():
        started = time.perf_counter()
        output = resize(source, target)
        elapsed = time.perf_counter() - started
        diag = get_last_diagnostics()
        row = _record_case(name, source, target, output, diag.get("layout_family", ""), elapsed)
        stress_rows.append(row)
        repeat = resize(source, target)
        stress_deterministic += int(_canonical(output) == _canonical(repeat))

    mutations = []
    mutation_deterministic = 0
    for name, source, target in make_mutations(tasks):
        started = time.perf_counter()
        output = resize(source, target)
        elapsed = time.perf_counter() - started
        diag = get_last_diagnostics()
        mutations.append(_record_case(name, source, target, output, diag.get("layout_family", ""), elapsed))
        repeat = resize(source, target)
        mutation_deterministic += int(_canonical(output) == _canonical(repeat))

    runtimes = [r["runtime_seconds"] for r in stress_rows]
    sorted_times = sorted(runtimes)
    summary = {
        "label": "internal proxy; not Adobe's hidden score",
        "official_count": len(official_rows),
        "stress_count": len(stress_rows),
        "mutation_count": len(mutations),
        "stress_structural_validity_rate": sum(r["hard_valid"] for r in stress_rows) / max(1, len(stress_rows)),
        "stress_off_canvas_cases": sum(r["off_canvas_count"] > 0 for r in stress_rows),
        "stress_image_ratio_failures": sum(r["image_ratio_failures"] for r in stress_rows),
        "stress_text_clipping_cases": sum(r["clipped_text_count"] > 0 for r in stress_rows),
        "stress_hierarchy_regressions": sum(sum("type hierarchy regressed" in issue for issue in r["issues"]) for r in stress_rows),
        "stress_hierarchy_regression_cases": sum(any("type hierarchy regressed" in issue for issue in r["issues"]) for r in stress_rows),
        "stress_collision_free_rate": sum(r["accidental_collision_count"] == 0 for r in stress_rows) / max(1, len(stress_rows)),
        "stress_median_runtime_seconds": statistics.median(runtimes) if runtimes else 0,
        "stress_p95_runtime_seconds": sorted_times[min(len(sorted_times) - 1, int(len(sorted_times) * 0.95))] if sorted_times else 0,
        "stress_determinism_rate": stress_deterministic / max(1, len(stress_rows)),
        "collision_metric_definition": (
            "Counts only new or worsened intersections relative to the source; pre-existing overlap is not counted as a regression."
        ),
        "mutation_structural_validity_rate": sum(r["hard_valid"] for r in mutations) / max(1, len(mutations)),
        "mutation_off_canvas_cases": sum(r["off_canvas_count"] > 0 for r in mutations),
        "mutation_image_ratio_failures": sum(r["image_ratio_failures"] for r in mutations),
        "mutation_text_clipping_cases": sum(r["clipped_text_count"] > 0 for r in mutations),
        "mutation_hierarchy_regressions": sum(sum("type hierarchy regressed" in issue for issue in r["issues"]) for r in mutations),
        "mutation_hierarchy_regression_cases": sum(any("type hierarchy regressed" in issue for issue in r["issues"]) for r in mutations),
        "mutation_collision_free_rate": sum(r["accidental_collision_count"] == 0 for r in mutations) / max(1, len(mutations)),
        "mutation_determinism_rate": mutation_deterministic / max(1, len(mutations)),
        "official": official_rows,
        "stress": stress_rows,
        "mutations": mutations,
    }
    (BENCH / "report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = ["# Internal benchmark report", "", "This score is an internal proxy, not Adobe's hidden evaluator.", "",
             f"- Official samples: {len(official_rows)}", f"- Synthetic stress cases: {len(stress_rows)} (default {STRESS_CASES})",
             f"- Mutations: {len(mutations)}", f"- Stress structural validity: {summary['stress_structural_validity_rate']:.1%}",
             f"- Stress off-canvas cases: {summary['stress_off_canvas_cases']}", f"- Image-ratio failures: {summary['stress_image_ratio_failures']}",
             f"- Text-clipping cases: {summary['stress_text_clipping_cases']}",
             f"- Stress hierarchy regressions: {summary['stress_hierarchy_regressions']} across {summary['stress_hierarchy_regression_cases']} cases",
             f"- No-new-collision rate (source-relative): {summary['stress_collision_free_rate']:.1%}",
             f"- Determinism rate: {summary['stress_determinism_rate']:.1%}",
             f"- Stress runtime median / p95: {summary['stress_median_runtime_seconds']:.4f}s / {summary['stress_p95_runtime_seconds']:.4f}s", "",
             f"- Mutation structural validity: {summary['mutation_structural_validity_rate']:.1%}",
             f"- Mutation off-canvas cases: {summary['mutation_off_canvas_cases']}",
             f"- Mutation image-ratio failures: {summary['mutation_image_ratio_failures']}",
             f"- Mutation text-clipping cases: {summary['mutation_text_clipping_cases']}",
             f"- Mutation hierarchy regressions: {summary['mutation_hierarchy_regressions']} across {summary['mutation_hierarchy_regression_cases']} cases",
             f"- Mutation no-new-collision rate (source-relative): {summary['mutation_collision_free_rate']:.1%}",
             f"- Mutation determinism rate: {summary['mutation_determinism_rate']:.1%}", "",
              f"- Collision metric: {summary['collision_metric_definition']}", "",
             "| Official sample | Baseline proxy | Current proxy | Layout | Candidates | Repairs |", "|---|---:|---:|---|---:|---:|"]
    for row in official_rows:
        lines.append(f"| {row['input']} | {row['baseline']['score']:.2f} | {row['current']['score']:.2f} | {row['layout_family']} | {row['candidate_count']} | {row['repair_count']} |")
    lines.extend(["", "See `report.json` for per-case diagnostics. Rendered source/baseline/current comparisons are in `../gallery/index.html`."])
    (BENCH / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    cards = []
    for name, difficulty, target, source_png, baseline_png, current_png in gallery_rows:
        images = "".join(f'<td><img src="../{escape(p.relative_to(EVIDENCE).as_posix())}" alt="{label}" style="max-width:100%;height:auto"></td>'
                         for p, label in ((source_png, "Source"), (baseline_png, "Baseline"), (current_png, "Current")))
        cards.append(f"<h2>{escape(name)} — {escape(str(difficulty))} — {target['width']}×{target['height']}</h2><table><thead><tr><th>Source</th><th>Starter baseline</th><th>Chameleon</th></tr></thead><tbody><tr>{images}</tr></tbody></table>")
    html = "<!doctype html><meta charset='utf-8'><title>Chameleon visual comparisons</title><style>body{font:16px system-ui;max-width:1400px;margin:2rem auto;padding:0 1rem}table{width:100%;table-layout:fixed;margin-bottom:3rem}th,td{vertical-align:top;padding:.5rem;background:#f4f1ed}img{width:100%}</style><h1>Chameleon visual evidence</h1><p>Source, untouched starter baseline, and current output rendered with the supplied renderer.</p>" + "\n".join(cards)
    (GALLERY / "index.html").write_text(html, encoding="utf-8")
    print(f"Wrote {BENCH / 'report.md'} and {GALLERY / 'index.html'}")
    print(json.dumps({k: v for k, v in summary.items() if not isinstance(v, list)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
