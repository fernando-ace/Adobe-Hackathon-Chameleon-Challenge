"""Render a hand-composed synthetic campaign across independent target formats."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from engine.chameleon.analyzer import analyze_design
from engine.chameleon.scoring import score_design
from engine.resize import get_last_diagnostics, resize
from renderer.converter.convert import render_design_to_png


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "curated"
ASSETS = ROOT / "brand_kit" / "assets"
FONTS = ROOT / "brand_kit" / "fonts"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=EVIDENCE / "source.json",
                        help="fixture JSON with source and targets")
    parser.add_argument("--output-dir", type=Path,
                        help="directory for source/output renders, JSON files, and report (defaults to the fixture directory)")
    args = parser.parse_args()
    fixture_path = args.fixture.resolve()
    output_dir = (args.output_dir.resolve() if args.output_dir else fixture_path.parent)
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture: dict[str, Any] = json.loads(fixture_path.read_text(encoding="utf-8"))
    source = fixture["source"]
    render_design_to_png(source, ASSETS, output_dir / "source.png", FONTS)
    results = []
    for target in fixture["targets"]:
        target_size = {"width": target["width"], "height": target["height"]}
        output = resize(source, target_size)
        diagnostics = get_last_diagnostics()
        repeated = resize(source, target_size)
        design_dna = analyze_design(source, target_size, ASSETS)
        quality = score_design(design_dna, output, diagnostics.get("layout_family", ""))
        source_elements = {element["id"]: element for element in source["elements"]}
        output_elements = {element["id"]: element for element in output["elements"]}
        ids_preserved = list(source_elements) == list(output_elements)
        text_preserved = all(
            element.get("content") == output_elements[element_id].get("content")
            for element_id, element in source_elements.items()
            if element.get("type") == "text"
        )
        font_families_preserved = all(
            element.get("font_family") == output_elements[element_id].get("font_family")
            for element_id, element in source_elements.items()
            if element.get("type") == "text"
        )
        image_assets_preserved = all(
            element.get("asset_id") == output_elements[element_id].get("asset_id")
            for element_id, element in source_elements.items()
            if element.get("type") == "image"
        )
        output_stem = f"{target['id']}_output"
        (output_dir / f"{output_stem}.json").write_text(
            json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        render_design_to_png(output, ASSETS, output_dir / f"{output_stem}.png", FONTS)
        results.append({
            "id": target["id"],
            "target_canvas": target_size,
            "element_count_preserved": len(output["elements"]) == len(source["elements"]),
            "ids_preserved": ids_preserved,
            "text_preserved": text_preserved,
            "font_families_preserved": font_families_preserved,
            "image_asset_ids_preserved": image_assets_preserved,
            "deterministic_json": json.dumps(output, sort_keys=True, separators=(",", ":")) == json.dumps(repeated, sort_keys=True, separators=(",", ":")),
            "layout_family": diagnostics.get("layout_family"),
            "candidate_count": diagnostics.get("candidate_count"),
            "repair_count": diagnostics.get("repair_count"),
            "proxy_score": quality.score,
            "hard_valid": quality.hard_valid,
            "off_canvas_count": quality.off_canvas_count,
            "clipped_text_count": quality.clipped_text_count,
            "image_ratio_failures": quality.image_ratio_failures,
            "accidental_collision_count": quality.accidental_collision_count,
            "issues": quality.issues,
            "output_json": f"{output_stem}.json",
            "output_png": f"{output_stem}.png",
        })
    report = {
        "fixture": fixture.get("name", fixture_path.stem),
        "synthetic": bool(fixture.get("synthetic", False)),
        "source_elements": len(source["elements"]),
        "outputs": results,
        "score_note": "Internal source-relative proxy only; inspect the rendered PNGs.",
    }
    (output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
