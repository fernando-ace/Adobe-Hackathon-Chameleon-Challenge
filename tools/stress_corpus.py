"""Deterministic, schema-shaped stress and mutation inputs for local evaluation."""

from __future__ import annotations

from copy import deepcopy
import random
from typing import Any


TARGETS = [
    (1080, 1350), (1600, 400), (728, 90), (1080, 1920),
    (1200, 628), (480, 800), (1000, 1000), (2160, 3840), (300, 600),
]
ASSETS = ["solstice_bottle.png", "solstice_logo_lockup.png", "missing_stress_asset.png"]


def make_design(seed: int, count: int | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    rng = random.Random(seed)
    count = count if count is not None else rng.choice([2, 3, 5, 8, 10, 15, 20, 30, 40, 45])
    width, height = rng.choice([(1080, 1080), (1080, 1350), (1200, 628), (800, 1200)])
    elements: list[dict[str, Any]] = [{
        "id": "bg", "type": "image", "x": 0, "y": 0, "width": width, "height": height,
        "asset_id": "solstice_bg_gradient.png", "fit": "cover", "z_index": 0,
    }]
    if count > 1:
        elements.append({
            "id": "headline", "type": "text", "x": width * 0.08, "y": height * 0.12,
            "width": width * 0.84, "height": height * 0.14, "content": rng.choice([
                "Make Every Moment Shine", "A Longer Synthetic Headline for Stress Coverage",
                "Limited Seasonal Release", "A very long headline " * (2 if seed % 3 == 0 else 1),
            ]), "font_family": "Solstice Serif", "font_size": rng.choice([28, 38, 54]),
            "font_weight": "bold", "color": "rgba(255,255,255,1)", "text_align": "center", "z_index": 3,
        })
    if count >= 3:
        elements.append({
            "id": "hero", "type": "image", "x": width * 0.35, "y": height * 0.31,
            "width": width * 0.30, "height": height * 0.30, "asset_id": rng.choice(ASSETS),
            "fit": "contain", "z_index": 2,
        })
    if count >= 4:
        elements.append({
            "id": "body", "type": "text", "x": width * 0.12, "y": height * 0.66,
            "width": width * 0.76, "height": height * 0.08,
            "content": "A botanical blend prepared for a warm evening under open skies.",
            "font_family": "Solstice Sans", "font_size": 20, "color": "rgba(255,255,255,0.9)",
            "text_align": "center", "z_index": 3,
        })
    if count >= 5:
        elements.extend([
            {"id": "cta_bg", "type": "shape", "x": width * 0.34, "y": height * 0.82,
             "width": width * 0.32, "height": height * 0.08, "shape_type": "rectangle",
             "fill_color": "rgba(232,106,58,1)", "corner_radius": 32, "group_id": "cta", "z_index": 2},
            {"id": "cta_label", "type": "text", "x": width * 0.35, "y": height * 0.84,
             "width": width * 0.30, "height": height * 0.04, "content": "Explore the collection",
             "font_family": "Solstice Sans", "font_size": 18, "font_weight": "bold",
             "color": "rgba(255,255,255,1)", "text_align": "center", "group_id": "cta", "z_index": 3},
        ])
    while len(elements) < count:
        i = len(elements)
        if i % 3 == 0:
            badge_w, badge_h = rng.randint(100, 190), rng.randint(38, 58)
            badge_x, badge_y = rng.randint(12, max(12, width - badge_w - 12)), rng.randint(int(height * .58), max(int(height * .58), height - badge_h - 24))
            elements.append({"id": f"badge_{i}_shape", "type": "shape", "x": badge_x,
                             "y": badge_y, "width": badge_w, "height": badge_h,
                             "shape_type": "rectangle", "fill_color": "rgba(232,106,58,0.88)",
                             "group_id": f"badge_{i}", "z_index": 2})
            elements.append({"id": f"badge_{i}_text", "type": "text", "x": badge_x + 5,
                             "y": badge_y + max(2, (badge_h - 30) / 2), "width": badge_w - 10, "height": min(30, badge_h - 4),
                             "content": f"FEATURE {i}", "font_family": "Solstice Sans", "font_size": 14,
                             "font_weight": "bold", "color": "rgba(255,255,255,1)", "text_align": "center",
                             "group_id": f"badge_{i}", "z_index": 3})
        elif i % 3 == 1:
            elements.append({"id": f"copy_{i}", "type": "text", "x": rng.randint(0, int(width * .7)),
                             "y": rng.randint(0, int(height * .8)), "width": width * .25, "height": height * .07,
                             "content": "A short supporting message.", "font_family": "Solstice Sans", "font_size": 16,
                             "color": "rgba(255,255,255,0.9)", "text_align": rng.choice(["left", "center", "right"]), "z_index": 3})
        else:
            elements.append({"id": f"decoration_{i}", "type": "shape", "x": rng.randint(-60, width - 40),
                             "y": rng.randint(-60, height - 40), "width": rng.randint(40, 180), "height": rng.randint(40, 180),
                             "shape_type": rng.choice(["ellipse", "rectangle"]), "fill_color": "rgba(255,255,255,0.16)",
                             "z_index": 1})
    # Count is a requested stress scale; preserve complete group pairs where possible.
    if len(elements) > count:
        elements = elements[:count]
    design = {"canvas": {"width": width, "height": height}, "elements": elements}
    return design, {"width": TARGETS[seed % len(TARGETS)][0], "height": TARGETS[seed % len(TARGETS)][1]}


def make_stress_corpus(size: int = 24, seed: int = 20261014) -> list[tuple[str, dict[str, Any], dict[str, int]]]:
    cases = []
    for index in range(size):
        source, target = make_design(seed + index)
        cases.append((f"synthetic_{index:03d}", source, target))
    return cases


def make_mutations(samples: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any], dict[str, int]]]:
    cases = []
    for sample in samples:
        source, target = sample["source"], sample["target_canvas"]
        for multiplier in (2, 4):
            changed = deepcopy(source)
            for element in changed["elements"]:
                if element.get("type") == "text" and element.get("id") == "headline":
                    element["content"] = str(element["content"]) * multiplier
            cases.append((f"{sample.get('task_id','case')}_headline_{multiplier}x", changed, target))
        for target2 in ((728, 90), (480, 1200), (1920, 1080)):
            cases.append((f"{sample.get('task_id','case')}_{target2[0]}x{target2[1]}", deepcopy(source),
                          {"width": target2[0], "height": target2[1]}))
    return cases
