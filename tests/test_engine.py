from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from engine.chameleon.analyzer import analyze_design
from engine.chameleon.scoring import score_design
from engine.chameleon.repair import repair_candidate
from engine.resize import get_last_diagnostics, resize
from renderer.converter.convert import render_design_to_png
from tools.stress_corpus import make_design, make_mutations, make_stress_corpus


ROOT = Path(__file__).resolve().parents[1]


def _official_tasks():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "input").glob("*.json"))]


class EngineContractTests(unittest.TestCase):
    def assert_contract(self, source, target, output):
        self.assertEqual(output["canvas"], target)
        source_ids = [e["id"] for e in source["elements"]]
        output_ids = [e["id"] for e in output["elements"]]
        self.assertEqual(len(output_ids), len(source_ids))
        self.assertEqual(set(output_ids), set(source_ids))
        self.assertEqual(len(set(output_ids)), len(output_ids))
        original = {e["id"]: e for e in source["elements"]}
        for element in output["elements"]:
            self.assertTrue(all(isinstance(element.get(k), (int, float)) for k in ("x", "y", "width", "height")))
            self.assertGreater(element["width"], 0)
            self.assertGreater(element["height"], 0)
            self.assertGreaterEqual(element["x"], -0.5)
            self.assertGreaterEqual(element["y"], -0.5)
            self.assertLessEqual(element["x"] + element["width"], target["width"] + 0.5)
            self.assertLessEqual(element["y"] + element["height"], target["height"] + 0.5)
            before = original[element["id"]]
            if before["type"] == "text":
                self.assertEqual(element["content"], before["content"])
                self.assertEqual(element["font_family"], before["font_family"])
            if before["type"] == "image" and before.get("fit") != "cover":
                self.assertAlmostEqual(element["width"] / element["height"], before["width"] / before["height"], delta=0.05 * before["width"] / before["height"])

    def test_official_samples_contract_determinism_and_score(self):
        self.assertEqual(len(_official_tasks()), 3)
        for task in _official_tasks():
            source = task["source"]
            before = json.dumps(source, sort_keys=True)
            output = resize(source, task["target_canvas"])
            diagnostics = get_last_diagnostics()
            self.assertFalse(diagnostics["fallback_used"], diagnostics)
            self.assertGreaterEqual(diagnostics["candidate_count"], 12)
            self.assertTrue(diagnostics["hard_valid"], diagnostics)
            self.assertEqual(len(diagnostics["placements"]), len(source["elements"]))
            self.assertTrue(all("reason" in placement and len(placement["output_rect_normalized"]) == 4 for placement in diagnostics["placements"]))
            self.assertGreaterEqual(len(diagnostics["candidate_rankings"]), 12)
            self.assertEqual(json.dumps(source, sort_keys=True), before, "resize mutated source data")
            self.assert_contract(source, task["target_canvas"], output)
            second = resize(source, task["target_canvas"])
            self.assertEqual(json.dumps(output, sort_keys=True), json.dumps(second, sort_keys=True))
            dna = analyze_design(source, task["target_canvas"])
            report = score_design(dna, output, diagnostics["layout_family"])
            self.assertTrue(report.hard_valid, report.issues)

    def test_metamorphic_identity_and_small_aspect_change(self):
        for task in _official_tasks():
            source = task["source"]
            width, height = source["canvas"]["width"], source["canvas"]["height"]
            identity = resize(source, {"width": width, "height": height})
            self.assertEqual(identity["elements"], source["elements"])
            self.assertEqual(get_last_diagnostics()["layout_family"], "identity")

            nearby = resize(source, {"width": round(width * 1.03), "height": height})
            self.assertFalse(get_last_diagnostics()["fallback_used"])
            original = {element["id"]: element for element in source["elements"]}
            normalized_delta = []
            for element in nearby["elements"]:
                before = original[element["id"]]
                for field, canvas_size in (("x", width), ("width", width), ("y", height), ("height", height)):
                    normalized_delta.append(abs(element[field] - before[field]) / canvas_size)
            self.assertLess(sum(normalized_delta) / max(1, len(normalized_delta)), 0.04)

    def test_official_outputs_render(self):
        for task in _official_tasks():
            output = resize(task["source"], task["target_canvas"])
            with tempfile.TemporaryDirectory() as temp:
                png = Path(temp) / "preview.png"
                warnings = render_design_to_png(output, ROOT / "brand_kit/assets", png, ROOT / "brand_kit/fonts")
                self.assertTrue(png.is_file())
                self.assertGreater(png.stat().st_size, 1000)
                if task["difficulty"] == "level_3_advanced":
                    self.assertTrue(any("solstice_holiday_badge_2025.png" in w for w in warnings))
                else:
                    self.assertEqual(warnings, [])

    def test_compact_banner_reserves_readable_action_row(self):
        task = next(task for task in _official_tasks() if task["difficulty"] == "level_3_advanced")
        output = resize(task["source"], task["target_canvas"])
        elements = {element["id"]: element for element in output["elements"]}
        self.assertGreaterEqual(elements["cta_label"]["font_size"], 8.0)
        for element_id in ("badge1_label", "badge2_label", "badge3_label"):
            self.assertGreaterEqual(elements[element_id]["font_size"], 8.0)
        self.assertEqual(get_last_diagnostics()["issues"], [])

    def test_semantics_detect_background_and_group_pair(self):
        source = _official_tasks()[1]["source"]
        dna = analyze_design(source, {"width": 1600, "height": 400})
        self.assertIn("bg", dna.background_ids)
        self.assertIn("cta", dna.groups)
        self.assertTrue(any(r.kind == "same_group" and r.intentional for r in dna.relationships))
        self.assertEqual(dna.transformation, "ultra_wide")

    def test_repair_moves_a_lower_priority_colliding_element(self):
        task = _official_tasks()[1]
        dna = analyze_design(task["source"], task["target_canvas"])
        output = resize(task["source"], task["target_canvas"])
        logo = next(e for e in output["elements"] if e["id"] == "logo")
        product = next(e for e in output["elements"] if e["id"] == "product")
        product["x"], product["y"] = logo["x"], logo["y"]
        repaired, report, repairs = repair_candidate(dna, output, "banner")
        self.assertGreater(repairs, 0)
        self.assertLess(report.accidental_collision_count, score_design(dna, output, "banner").accidental_collision_count)
        self.assertTrue(report.hard_valid)
        self.assertNotEqual(next(e for e in repaired["elements"] if e["id"] == "product")["y"], logo["y"])

    def test_safe_fallback_preserves_ids_when_analysis_fails(self):
        task = _official_tasks()[0]
        with patch("engine.resize.analyze_design", side_effect=RuntimeError("synthetic analyzer failure")):
            output = resize(task["source"], {"width": 500, "height": 300})
        self.assertTrue(get_last_diagnostics()["fallback_used"])
        self.assertEqual({e["id"] for e in output["elements"]}, {e["id"] for e in task["source"]["elements"]})
        self.assertEqual(output["canvas"], {"width": 500, "height": 300})

    def test_stress_corpus_is_schema_shaped_and_survives(self):
        corpus = make_stress_corpus(24)
        self.assertEqual(len(corpus), 24)
        for _name, source, target in corpus:
            output = resize(source, target)
            self.assert_contract(source, target, output)
            self.assertFalse(get_last_diagnostics()["fallback_used"], get_last_diagnostics())
            self.assertTrue(get_last_diagnostics()["hard_valid"], get_last_diagnostics())

    def test_mutations_preserve_contract_without_fallback(self):
        cases = make_mutations(_official_tasks())
        self.assertEqual(len(cases), 15)
        for _name, source, target in cases:
            output = resize(source, target)
            self.assert_contract(source, target, output)
            self.assertFalse(get_last_diagnostics()["fallback_used"], get_last_diagnostics())

    def test_stress_generator_handles_small_and_large_counts(self):
        for count in (2, 3, 5, 8, 15, 20, 30, 40):
            source, target = make_design(100 + count, count)
            self.assertEqual(len(source["elements"]), count)
            output = resize(source, target)
            self.assert_contract(source, target, output)
            self.assertTrue(get_last_diagnostics()["hard_valid"], get_last_diagnostics())


if __name__ == "__main__":
    unittest.main()
