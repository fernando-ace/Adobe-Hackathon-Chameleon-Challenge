from __future__ import annotations

from copy import deepcopy
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
            before = original[element["id"]]
            current_edges = (max(0, -element["x"]), max(0, -element["y"]),
                             max(0, element["x"] + element["width"] - target["width"]),
                             max(0, element["y"] + element["height"] - target["height"]))
            if any(edge > 0.5 for edge in current_edges):
                note = str(before.get("_note", "")).casefold()
                self.assertTrue("intentional" in note or "bleed" in note, element["id"])
                source_canvas = source["canvas"]
                source_edges = (max(0, -before["x"]), max(0, -before["y"]),
                                max(0, before["x"] + before["width"] - source_canvas["width"]),
                                max(0, before["y"] + before["height"] - source_canvas["height"]))
                self.assertTrue(all(current / target_size <= prior / source_size + 0.01
                                    for current, prior, target_size, source_size in zip(
                                        current_edges, source_edges,
                                        (target["width"], target["height"], target["width"], target["height"]),
                                        (source_canvas["width"], source_canvas["height"], source_canvas["width"], source_canvas["height"]),
                                    )), element["id"])
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

    def test_action_language_identifies_cta_and_keeps_button_geometry(self):
        fixture = json.loads((ROOT / "evidence" / "curated" / "source.json").read_text(encoding="utf-8"))
        source = fixture["source"]
        target = {"width": 1920, "height": 1080}
        dna = analyze_design(source, target)
        self.assertEqual(dna.by_id["cta_background"].role, "cta_container")

        output = resize(source, target)
        original = {element["id"]: element for element in source["elements"]}
        current = {element["id"]: element for element in output["elements"]}
        source_group = [original["cta_background"], original["cta_label"]]
        output_group = [current["cta_background"], current["cta_label"]]

        def bounds(elements):
            x0 = min(element["x"] for element in elements)
            y0 = min(element["y"] for element in elements)
            x1 = max(element["x"] + element["width"] for element in elements)
            y1 = max(element["y"] + element["height"] for element in elements)
            return (x1 - x0) / (y1 - y0)

        self.assertAlmostEqual(bounds(source_group), bounds(output_group), delta=0.02)

    def test_lower_unbolded_supporting_line_is_not_a_cta(self):
        from engine.chameleon.semantics import infer_roles

        roles = infer_roles([
            {"id": "headline", "type": "text", "x": 0, "y": 0, "width": 900, "height": 100,
             "content": "A clear headline", "font_family": "Solstice Serif", "font_size": 48},
            {"id": "support", "type": "text", "x": 20, "y": 800, "width": 700, "height": 60,
             "content": "A short supporting message", "font_family": "Solstice Sans", "font_size": 16},
        ], {"width": 1000, "height": 1000})
        self.assertEqual(roles["support"][0], "subheadline")

    def test_portrait_story_reserves_more_width_for_primary_action(self):
        fixture = json.loads((ROOT / "evidence" / "curated" / "source.json").read_text(encoding="utf-8"))
        output = resize(fixture["source"], {"width": 300, "height": 600})
        label = next(element for element in output["elements"] if element["id"] == "cta_label")
        self.assertGreaterEqual(label["font_size"], 8.0)

    def test_extreme_tall_target_caps_button_and_badge_background_growth(self):
        fixture = json.loads((ROOT / "evidence" / "curated" / "sidecar" / "source.json").read_text(encoding="utf-8"))
        source = fixture["source"]
        output = resize(source, {"width": 1080, "height": 1920})
        original = {element["id"]: element for element in source["elements"]}
        current = {element["id"]: element for element in output["elements"]}

        for group_ids in (("cta_background", "cta_label"),
                          ("citrus_badge_background", "citrus_badge_label")):
            source_bounds = self._union_size([original[element_id] for element_id in group_ids])
            output_bounds = self._union_size([current[element_id] for element_id in group_ids])
            scale = output_bounds[0] / source_bounds[0]
            self.assertAlmostEqual(output_bounds[1] / source_bounds[1], scale, delta=0.01)
            self.assertLessEqual(scale, 1.25 + 1e-6)

    def test_tall_story_bands_close_hero_copy_and_action_gaps(self):
        fixture = json.loads((ROOT / "evidence" / "curated" / "sidecar" / "source.json").read_text(encoding="utf-8"))
        output = resize(fixture["source"], {"width": 1080, "height": 1920})
        by_id = {element["id"]: element for element in output["elements"]}
        hero = by_id["hero_product"]
        copy = by_id["supporting_copy"]
        self.assertLessEqual(float(hero["y"]) + float(hero["height"]), float(copy["y"]))
        self.assertLessEqual(float(copy["height"]), 1920 * 0.09)
        self.assertLess(float(by_id["cta_background"]["y"]), 1920 * 0.84)

        badge = self._union_bounds([by_id["citrus_badge_background"], by_id["plant_badge_background"]])
        cta = by_id["cta_background"]
        self.assertLessEqual(badge[3], float(cta["y"]))

    def test_bold_event_date_is_informational_copy_not_a_standalone_cta(self):
        fixture = json.loads((ROOT / "evidence" / "curated" / "market" / "source.json").read_text(encoding="utf-8"))
        dna = analyze_design(fixture["source"], {"width": 300, "height": 600})
        self.assertEqual(dna.by_id["event_eyebrow"].role, "event_metadata")

    def test_mobile_event_date_keeps_source_scale_before_product(self):
        fixture = json.loads((ROOT / "evidence" / "curated" / "market" / "source.json").read_text(encoding="utf-8"))
        output = resize(fixture["source"], {"width": 300, "height": 600})
        by_id = {element["id"]: element for element in output["elements"]}
        self.assertGreaterEqual(by_id["event_eyebrow"]["font_size"], 20.0)
        self.assertLessEqual(float(by_id["event_eyebrow"]["y"]) + float(by_id["event_eyebrow"]["height"]),
                             float(by_id["hero_product"]["y"]))
        self.assertFalse(any("new overlap" in issue for issue in get_last_diagnostics()["issues"]))

    def test_wide_source_recomposes_for_square_target(self):
        fixture = json.loads((ROOT / "evidence" / "curated" / "market" / "source.json").read_text(encoding="utf-8"))
        source = fixture["source"]
        target = {"width": 1080, "height": 1080}
        output = resize(source, target)
        diagnostics = get_last_diagnostics()
        self.assertNotEqual(diagnostics["layout_family"], "source_fit")
        self.assert_contract(source, target, output)

    def test_medium_rectangle_keeps_action_labels_above_legal_copy(self):
        fixture = json.loads((ROOT / "evidence" / "curated" / "market" / "source.json").read_text(encoding="utf-8"))
        output = resize(fixture["source"], {"width": 300, "height": 250})
        by_id = {element["id"]: element for element in output["elements"]}
        self.assertGreaterEqual(by_id["cta_label"]["font_size"] / by_id["legal_copy"]["font_size"], 0.82)
        self.assertGreaterEqual(by_id["time_badge_label"]["font_size"] / by_id["legal_copy"]["font_size"], 0.82)
        self.assertFalse(any("type hierarchy regressed" in issue for issue in get_last_diagnostics()["issues"]))

    @staticmethod
    def _union_size(elements):
        x0 = min(float(element["x"]) for element in elements)
        y0 = min(float(element["y"]) for element in elements)
        x1 = max(float(element["x"]) + float(element["width"]) for element in elements)
        y1 = max(float(element["y"]) + float(element["height"]) for element in elements)
        return x1 - x0, y1 - y0

    @staticmethod
    def _union_bounds(elements):
        x0 = min(float(element["x"]) for element in elements)
        y0 = min(float(element["y"]) for element in elements)
        x1 = max(float(element["x"]) + float(element["width"]) for element in elements)
        y1 = max(float(element["y"]) + float(element["height"]) for element in elements)
        return x0, y0, x1, y1

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

    def test_larger_canvas_preserves_primary_type_and_does_not_add_clipping(self):
        for task in _official_tasks():
            source, target = task["source"], task["target_canvas"]
            small = resize(source, target)
            small_family = get_last_diagnostics()["layout_family"]
            small_dna = analyze_design(source, target)
            small_report = score_design(small_dna, small, small_family)
            small_by_id = {element["id"]: element for element in small["elements"]}
            headlines = [fact for fact in small_dna.facts if fact.type == "text" and fact.role == "headline"]

            for scale in (1.03, 1.25):
                larger_target = {key: round(value * scale) for key, value in target.items()}
                larger = resize(source, larger_target)
                family = get_last_diagnostics()["layout_family"]
                self.assertFalse(get_last_diagnostics()["fallback_used"])
                report = score_design(analyze_design(source, larger_target), larger, family)
                self.assertLessEqual(report.clipped_text_count, small_report.clipped_text_count)
                larger_by_id = {element["id"]: element for element in larger["elements"]}
                for fact in headlines:
                    self.assertGreaterEqual(larger_by_id[fact.id]["font_size"], small_by_id[fact.id]["font_size"] * 0.9)

    def test_hierarchy_scoring_respects_source_and_catches_regressions(self):
        _name, source, _target = next(case for case in make_stress_corpus() if case[0] == "synthetic_049")
        dna = analyze_design(source, source["canvas"])
        facts = {fact.id: fact for fact in dna.facts}
        self.assertEqual(facts["copy_7"].role, "subheadline")
        self.assertEqual(facts["body"].role, "body_copy")

        preserved = score_design(dna, source, "source_fit")
        self.assertFalse(any("type hierarchy" in issue for issue in preserved.issues), preserved.issues)

        regressed = deepcopy(source)
        next(element for element in regressed["elements"] if element["id"] == "copy_7")["font_size"] = 10
        report = score_design(dna, regressed, "source_fit")
        self.assertTrue(any("copy_7/body: type hierarchy regressed" in issue for issue in report.issues), report.issues)

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
        self.assertGreaterEqual(elements["headline"]["font_size"], 13.0)
        self.assertGreaterEqual(elements["legal_text"]["font_size"], 7.5)
        self.assertGreaterEqual(elements["cta_label"]["font_size"], 8.0)
        for element_id in ("badge1_label", "badge2_label", "badge3_label"):
            self.assertGreaterEqual(elements[element_id]["font_size"], 8.0)
        product = elements["product"]
        target = task["target_canvas"]
        self.assertGreaterEqual(product["width"] * product["height"] / (target["width"] * target["height"]), 0.055)
        self.assertEqual(get_last_diagnostics()["issues"], [])

    def test_extreme_wide_banner_recomposes_without_new_collisions(self):
        task = next(task for task in _official_tasks() if task["difficulty"] == "level_3_advanced")
        target = {"width": 3000, "height": 600}
        output = resize(task["source"], target)
        diagnostics = get_last_diagnostics()
        self.assertIn(diagnostics["layout_family"], {"banner", "banner_mirror"})
        self.assertEqual(diagnostics["issues"], [])
        self.assertEqual(diagnostics["score_components"]["collision_avoidance"], 100.0)
        self.assert_contract(task["source"], target, output)
        by_id = {element["id"]: element for element in output["elements"]}
        self.assertLess(by_id["headline"]["x"], by_id["product"]["x"])
        self.assertGreater(by_id["product"]["height"], target["height"] * 0.60)

    def test_dense_wide_banner_keeps_brand_mark_out_of_copy_column(self):
        name, source, target = make_stress_corpus()[39]
        self.assertEqual(name, "synthetic_039")
        output = resize(source, target)
        diagnostics = get_last_diagnostics()
        self.assertIn(diagnostics["layout_family"], {"banner", "banner_mirror"})
        self.assertEqual(diagnostics["score_components"]["collision_avoidance"], 100.0)
        self.assertEqual(diagnostics["score_components"]["target_adaptation"], 100.0)
        self.assertGreaterEqual(diagnostics["proxy_score"], 98.0)
        self.assertFalse(any("headline/logo" in issue for issue in diagnostics["issues"]))
        self.assert_contract(source, target, output)

    def test_wide_campaign_keeps_secondary_art_out_of_narrative_column(self):
        wide_cases = [
            (name, source, target)
            for name, source, target in make_mutations(_official_tasks())
            if name.endswith("_wide") and sum(element.get("type") == "image" for element in source["elements"]) > 3
        ]
        self.assertTrue(wide_cases)
        for name, source, target in wide_cases:
            with self.subTest(name=name):
                output = resize(source, target)
                diagnostics = get_last_diagnostics()
                self.assertEqual(diagnostics["score_components"]["collision_avoidance"], 100.0)
                self.assertGreaterEqual(diagnostics["proxy_score"], 98.0)
                self.assertFalse(any("new overlap" in issue for issue in diagnostics["issues"]))
                self.assert_contract(source, target, output)

    def test_long_compact_headline_preserves_type_hierarchy(self):
        cases = [
            (name, source, target)
            for name, source, target in make_mutations(_official_tasks())
            if name.endswith("_headline_4x") and target["width"] <= 800 and target["height"] <= 150
        ]
        self.assertTrue(cases)
        for name, source, target in cases:
            with self.subTest(name=name):
                output = resize(source, target)
                diagnostics = get_last_diagnostics()
                headline = next(e for e in output["elements"] if e["id"] == "headline")
                self.assertGreaterEqual(headline["font_size"], 8.0)
                self.assertFalse(any("type hierarchy regressed" in issue for issue in diagnostics["issues"]))
                self.assertEqual(diagnostics["score_components"]["collision_avoidance"], 100.0)
                self.assert_contract(source, target, output)

    def test_sparse_portrait_stack_uses_lower_action_band(self):
        task = next(task for task in _official_tasks() if task["difficulty"] == "level_1_warmup")
        output = resize(task["source"], task["target_canvas"])
        cta = next(element for element in output["elements"] if element["id"] == "cta")
        center_y = (cta["y"] + cta["height"] / 2) / task["target_canvas"]["height"]
        self.assertGreaterEqual(center_y, 0.70)
        self.assertLess(center_y, 0.86)
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
        corpus = make_stress_corpus()
        self.assertEqual(len(corpus), 64)
        has_rotation = has_transparency = has_logo = has_missing_asset = has_40_plus = False
        for _name, source, target in corpus:
            ids = [element["id"] for element in source["elements"]]
            self.assertEqual(len(ids), len(set(ids)))
            group_counts = {}
            for element in source["elements"]:
                if element.get("group_id"):
                    group_counts[element["group_id"]] = group_counts.get(element["group_id"], 0) + 1
            self.assertTrue(all(count >= 2 for count in group_counts.values()))
            has_rotation |= any(float(element.get("rotation", 0)) != 0 for element in source["elements"])
            has_transparency |= any(float(element.get("opacity", 1)) < 1 for element in source["elements"])
            has_logo |= any(element.get("id") == "logo" for element in source["elements"])
            has_missing_asset |= any(element.get("asset_id") == "missing_stress_asset.png" for element in source["elements"])
            has_40_plus |= len(source["elements"]) >= 40
            output = resize(source, target)
            self.assert_contract(source, target, output)
            self.assertFalse(get_last_diagnostics()["fallback_used"], get_last_diagnostics())
            self.assertTrue(get_last_diagnostics()["hard_valid"], get_last_diagnostics())
            self.assertFalse(any("new overlap" in issue for issue in get_last_diagnostics()["issues"]), _name)
        self.assertTrue(all((has_rotation, has_transparency, has_logo, has_missing_asset, has_40_plus)))

    def test_mutations_preserve_contract_without_fallback(self):
        cases = make_mutations(_official_tasks())
        self.assertEqual(len(cases), 45)
        for name, source, target in cases:
            output = resize(source, target)
            self.assert_contract(source, target, output)
            self.assertFalse(get_last_diagnostics()["fallback_used"], get_last_diagnostics())
            self.assertFalse(any("new overlap" in issue for issue in get_last_diagnostics()["issues"]), name)
            self.assertFalse(any("type hierarchy regressed" in issue for issue in get_last_diagnostics()["issues"]), name)

    def test_stress_generator_handles_small_and_large_counts(self):
        for count in (2, 3, 5, 8, 15, 20, 30, 40):
            source, target = make_design(100 + count, count)
            self.assertEqual(len(source["elements"]), count)
            group_counts = {}
            for element in source["elements"]:
                if element.get("group_id"):
                    group_counts[element["group_id"]] = group_counts.get(element["group_id"], 0) + 1
            self.assertTrue(all(size >= 2 for size in group_counts.values()))
            output = resize(source, target)
            self.assert_contract(source, target, output)
            self.assertTrue(get_last_diagnostics()["hard_valid"], get_last_diagnostics())


if __name__ == "__main__":
    unittest.main()
