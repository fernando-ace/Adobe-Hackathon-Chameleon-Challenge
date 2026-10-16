"""Export representative deterministic synthetic cases as inspectable evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.chameleon.analyzer import analyze_design
from engine.chameleon.scoring import score_design
from engine.resize import get_last_diagnostics, resize
from renderer.converter.convert import render_design_to_png
from tools.stress_corpus import make_stress_corpus


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "stress"
ASSETS = ROOT / "brand_kit" / "assets"
FONTS = ROOT / "brand_kit" / "fonts"


def canonical(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def main() -> int:
    report = json.loads((ROOT / "evidence" / "benchmark" / "report.json").read_text(encoding="utf-8"))
    rows = {row["name"]: row for row in report["stress"]}
    corpus = make_stress_corpus()
    cases_by_name = {name: (source, target) for name, source, target in corpus}

    slowest = max(report["stress"], key=lambda row: row["runtime_seconds"])["name"]
    densest = max(corpus, key=lambda case: len(case[1]["elements"]))[0]
    narrowest = min(corpus, key=lambda case: case[2]["width"] / case[2]["height"])[0]
    selected = list(dict.fromkeys((slowest, densest, narrowest)))
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "title": "Representative synthetic stress cases",
        "source": "tools/stress_corpus.py, deterministic seed 20261014",
        "selection": {
            "slowest": slowest,
            "densest": densest,
            "narrowest_target_aspect": narrowest,
        },
        "cases": [],
    }

    for name in selected:
        source, target = cases_by_name[name]
        seed = 20261014 + int(name.rsplit("_", 1)[1])
        source_path = OUT / f"{name}_source.json"
        output_path = OUT / f"{name}_output.json"
        source_png = OUT / f"{name}_source.png"
        output_png = OUT / f"{name}_output.png"
        source_path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        render_design_to_png(source, ASSETS, source_png, FONTS)
        output = resize(source, target)
        diagnostics = get_last_diagnostics()
        repeat = resize(source, target)
        dna = analyze_design(source, target, ASSETS)
        score = score_design(dna, output, diagnostics.get("layout_family", ""))
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        render_design_to_png(output, ASSETS, output_png, FONTS)
        prior = rows[name]
        manifest["cases"].append({
            "name": name,
            "seed": seed,
            "synthetic": True,
            "source_elements": len(source["elements"]),
            "source_canvas": source["canvas"],
            "target_canvas": target,
            "layout_family": diagnostics.get("layout_family"),
            "candidate_count": diagnostics.get("candidate_count"),
            "hard_valid": score.hard_valid,
            "off_canvas_count": score.off_canvas_count,
            "image_ratio_failures": score.image_ratio_failures,
            "clipped_text_count": score.clipped_text_count,
            "accidental_collision_count": score.accidental_collision_count,
            "deterministic_json": canonical(output) == canonical(repeat),
            "benchmark_runtime_seconds": prior["runtime_seconds"],
            "benchmark_runtime_note": "Observed in the full benchmark run; timing varies by host.",
            "artifacts": {
                "source_json": source_path.name,
                "source_png": source_png.name,
                "output_json": output_path.name,
                "output_png": output_png.name,
            },
        })

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
