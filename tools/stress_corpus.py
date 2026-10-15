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
STRESS_CASES = 64


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
    if count == 5:
        elements.append({
            "id": "cta_label", "type": "text", "x": width * 0.35, "y": height * 0.84,
            "width": width * 0.30, "height": height * 0.05, "content": "Explore the collection",
            "font_family": "Solstice Sans", "font_size": 18, "font_weight": "bold",
            "color": "rgba(255,255,255,1)", "text_align": "center", "z_index": 3,
        })
    elif count >= 6:
        elements.extend([
            {"id": "cta_bg", "type": "shape", "x": width * 0.34, "y": height * 0.82,
             "width": width * 0.32, "height": height * 0.08, "shape_type": "rectangle",
             "fill_color": "rgba(232,106,58,1)", "corner_radius": 32, "group_id": "cta", "z_index": 2},
            {"id": "cta_label", "type": "text", "x": width * 0.35, "y": height * 0.84,
             "width": width * 0.30, "height": height * 0.04, "content": "Explore the collection",
             "font_family": "Solstice Sans", "font_size": 18, "font_weight": "bold",
             "color": "rgba(255,255,255,1)", "text_align": "center", "group_id": "cta", "z_index": 3},
        ])
    if count >= 8:
        elements.append({
            "id": "logo", "type": "image", "x": width * 0.78, "y": height * 0.035,
            "width": width * 0.16, "height": height * 0.055, "asset_id": "solstice_logo_lockup.png",
            "fit": "contain", "z_index": 4,
        })
    while len(elements) < count:
        i = len(elements)
        remaining = count - len(elements)
        paired_badges = sum(1 for element in elements if str(element.get("group_id", "")).startswith("badge_")) // 2
        if i % 3 == 0 and remaining >= 2 and paired_badges < 4:
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
                             "opacity": rng.choice([0.25, 0.55, 0.85]),
                             "rotation": rng.choice([-30, 0, 20, 45]) if i % 2 == 0 else 0,
                             "z_index": 1})
    if len(elements) != count:
        raise ValueError(f"generator made {len(elements)} elements for requested count {count}")
    design = {"canvas": {"width": width, "height": height}, "elements": elements}
    if count >= 30:
        # Keep high-density cases on canvases that could plausibly carry them;
        # narrow banners are covered by lower-count source designs instead.
        target = rng.choice([size for size in TARGETS if size[0] * size[1] >= 600_000 and size[0] / size[1] < 2.5])
    else:
        target = TARGETS[seed % len(TARGETS)]
    return design, {"width": target[0], "height": target[1]}


def make_stress_corpus(size: int = STRESS_CASES, seed: int = 20261014) -> list[tuple[str, dict[str, Any], dict[str, int]]]:
    cases = []
    for index in range(size):
        source, target = make_design(seed + index)
        cases.append((f"synthetic_{index:03d}", source, target))
    return cases


def _ensure_shape(design: dict[str, Any]) -> dict[str, Any]:
    shape = next((element for element in design["elements"] if element.get("type") == "shape"), None)
    if shape is not None:
        return shape
    width, height = design["canvas"]["width"], design["canvas"]["height"]
    shape = {"id": "mutation_decoration", "type": "shape", "x": width * 0.72, "y": height * 0.52,
             "width": width * 0.12, "height": height * 0.12, "shape_type": "ellipse",
             "fill_color": "rgba(255,255,255,0.3)", "z_index": 1}
    design["elements"].append(shape)
    return shape


def _ensure_group(design: dict[str, Any]) -> str:
    existing = next((element.get("group_id") for element in design["elements"] if element.get("group_id")), None)
    if existing:
        return str(existing)
    width, height = design["canvas"]["width"], design["canvas"]["height"]
    group_id, x, y, w, h = "mutation_move_group", width * 0.08, height * 0.78, width * 0.28, height * 0.07
    design["elements"].extend([
        {"id": "mutation_move_bg", "type": "shape", "x": x, "y": y, "width": w, "height": h,
         "shape_type": "rectangle", "fill_color": "rgba(232,106,58,1)", "group_id": group_id, "z_index": 2},
        {"id": "mutation_move_label", "type": "text", "x": x + 4, "y": y + h * 0.2, "width": w - 8, "height": h * 0.6,
         "content": "MOVE TOGETHER", "font_family": "Solstice Sans", "font_size": h * 0.32,
         "color": "rgba(255,255,255,1)", "text_align": "center", "group_id": group_id, "z_index": 3},
    ])
    return group_id


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

        changed = deepcopy(source)
        hero = next((element for element in changed["elements"] if element.get("id") in {"hero", "product"}), None)
        if hero is None:
            hero = next(element for element in changed["elements"] if element.get("id") == "logo")
        if hero is not None:
            old_w, old_h = float(hero["width"]), float(hero["height"])
            new_w, new_h = old_w * 1.25, old_h * 1.25
            hero["x"] = max(0.0, min(float(source["canvas"]["width"]) - new_w, float(hero["x"]) - (new_w - old_w) / 2))
            hero["y"] = max(0.0, min(float(source["canvas"]["height"]) - new_h, float(hero["y"]) - (new_h - old_h) / 2))
            hero["width"], hero["height"] = new_w, new_h
        cases.append((f"{sample.get('task_id','case')}_hero_resize", changed, target))

        changed = deepcopy(source)
        logo = next(element for element in changed["elements"] if element.get("id") == "logo")
        logo["x"], logo["y"] = source["canvas"]["width"] * 0.06, source["canvas"]["height"] * 0.04
        cases.append((f"{sample.get('task_id','case')}_logo_move", changed, target))

        changed = deepcopy(source)
        w, h = source["canvas"]["width"], source["canvas"]["height"]
        badge_x, badge_y, badge_w, badge_h = w * 0.08, h * 0.78, w * 0.28, h * 0.07
        changed["elements"].extend([
            {"id": "mutation_badge_bg", "type": "shape", "x": badge_x, "y": badge_y,
             "width": badge_w, "height": badge_h, "shape_type": "rectangle", "fill_color": "rgba(232,106,58,1)",
             "corner_radius": badge_h / 2, "group_id": "mutation_badge", "z_index": 3},
            {"id": "mutation_badge_label", "type": "text", "x": badge_x + 4, "y": badge_y + badge_h * 0.22,
             "width": badge_w - 8, "height": badge_h * 0.56, "content": "SEASONAL PICK",
             "font_family": "Solstice Sans", "font_size": max(8, badge_h * 0.32), "font_weight": "bold",
             "color": "rgba(255,255,255,1)", "text_align": "center", "group_id": "mutation_badge", "z_index": 4},
        ])
        cases.append((f"{sample.get('task_id','case')}_add_badge", changed, target))

        changed = deepcopy(source)
        changed["elements"].append({
            "id": "mutation_support_copy", "type": "text", "x": w * 0.08, "y": h * 0.47,
            "width": w * 0.84, "height": h * 0.07, "content": "Made for the golden hour.",
            "font_family": "Solstice Sans", "font_size": 18, "color": "rgba(255,255,255,1)",
            "text_align": "left", "z_index": 3,
        })
        cases.append((f"{sample.get('task_id','case')}_add_copy", changed, target))

        changed = deepcopy(source)
        shape = next((element for element in changed["elements"]
                      if element.get("type") == "shape" and not element.get("group_id")
                      and "deco" in str(element.get("id", "")).casefold()), None)
        if shape is None:
            shape = next((element for element in changed["elements"]
                          if element.get("type") == "shape" and element.get("rotation") is not None), None)
        if shape is None:
            shape = _ensure_shape(changed)
        shape["rotation"] = float(shape.get("rotation", 0)) + 17
        cases.append((f"{sample.get('task_id','case')}_rotate_shape", changed, target))

        changed = deepcopy(source)
        shape = _ensure_shape(changed)
        shape["opacity"] = 0.35
        cases.append((f"{sample.get('task_id','case')}_transparency", changed, target))

        changed = deepcopy(source)
        headline = next(element for element in changed["elements"] if element.get("id") == "headline")
        headline["text_align"] = {"left": "right", "right": "center", "center": "left"}.get(headline.get("text_align", "center"), "left")
        cases.append((f"{sample.get('task_id','case')}_alignment", changed, target))

        changed = deepcopy(source)
        group_id = _ensure_group(changed)
        members = [element for element in changed["elements"] if element.get("group_id") == group_id]
        left, top = min(float(e["x"]) for e in members), min(float(e["y"]) for e in members)
        right = max(float(e["x"]) + float(e["width"]) for e in members)
        bottom = max(float(e["y"]) + float(e["height"]) for e in members)
        dx = min(source["canvas"]["width"] * 0.04, source["canvas"]["width"] - right) if right < source["canvas"]["width"] else -left
        dy = min(source["canvas"]["height"] * 0.025, source["canvas"]["height"] - bottom) if bottom < source["canvas"]["height"] else -top
        for element in members:
            element["x"], element["y"] = float(element["x"]) + dx, float(element["y"]) + dy
        cases.append((f"{sample.get('task_id','case')}_move_group", changed, target))

        for label, target2 in (("wide", (1920, 1080)), ("tall", (480, 1200)), ("story", (1080, 1920)), ("near_aspect", (round(w * 1.03), h))):
            cases.append((f"{sample.get('task_id','case')}_{label}", deepcopy(source),
                          {"width": target2[0], "height": target2[1]}))

        changed = deepcopy(source)
        hero = next((element for element in changed["elements"] if element.get("id") in {"hero", "product"}), None)
        if hero is None:
            hero = next(element for element in changed["elements"] if element.get("id") == "logo")
        hero["asset_id"] = "missing_optional_mutation.png"
        cases.append((f"{sample.get('task_id','case')}_missing_asset", changed, target))
    return cases
