"""Deterministic candidate generation across source, stack, split, and banner families."""

from __future__ import annotations

from copy import deepcopy
from math import cos, radians, sin
from typing import Any

from .model import DesignDNA, ElementFacts
from .typography import fit_font_size


def _clamp_rect(rect: tuple[float, float, float, float], canvas: dict[str, int]) -> tuple[float, float, float, float]:
    x, y, w, h = rect
    cw, ch = float(canvas["width"]), float(canvas["height"])
    w, h = min(max(1.0, w), cw), min(max(1.0, h), ch)
    return min(max(0.0, x), cw - w), min(max(0.0, y), ch - h), w, h


def _unit_rect(dna: DesignDNA, ids: list[str]) -> tuple[float, float, float, float]:
    elements = [dna.by_id[eid].element for eid in ids]
    x0 = min(float(e.get("x", 0)) for e in elements)
    y0 = min(float(e.get("y", 0)) for e in elements)
    x1 = max(float(e.get("x", 0)) + float(e.get("width", 0)) for e in elements)
    y1 = max(float(e.get("y", 0)) + float(e.get("height", 0)) for e in elements)
    return x0, y0, max(1.0, x1 - x0), max(1.0, y1 - y0)


def _fit_image_to_rect(element: dict[str, Any], rect: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x, y, w, h = rect
    sw, sh = max(1e-6, float(element.get("width", w))), max(1e-6, float(element.get("height", h)))
    scale = min(w / sw, h / sh)
    nw, nh = sw * scale, sh * scale
    return x + (w - nw) / 2, y + (h - nh) / 2, nw, nh


def _fit_size(fact: ElementFacts, box: tuple[float, float, float, float], fonts_dir: str = "brand_kit/fonts") -> float:
    e = fact.element
    x, y, w, h = box
    min_size = {"headline": 8.0, "subheadline": 7.0, "body_copy": 6.0, "legal": 4.0,
                "cta_text": 6.0, "badge_text": 5.0, "group_label": 5.0}.get(fact.role, 5.0)
    # Keep original size as a cap for compact target formats. Small canvases may
    # still need a controlled reduction, found with the actual bundled font.
    maximum = max(1.0, float(e.get("font_size", 12)))
    size, measure = fit_font_size(e, w, h, maximum=maximum, minimum=min(min_size, maximum), fonts_dir=fonts_dir)
    if not measure.fits and size > 1.0:
        # Clipping is more damaging than reducing an already small size. This
        # last resort is explicitly surfaced by scoring as an unreadable-type
        # penalty, while keeping every source word visible.
        size, _measure = fit_font_size(e, w, h, maximum=size, minimum=1.0, fonts_dir=fonts_dir)
    return size


def _apply_rect(
    dna: DesignDNA, output_by_id: dict[str, dict[str, Any]],
    eid: str, rect: tuple[float, float, float, float], assigned: set[str],
) -> None:
    fact = dna.by_id.get(eid)
    if fact is None or eid in assigned:
        return
    rect = _clamp_rect(rect, dna.target_canvas)
    element = fact.element
    members = dna.groups.get(fact.group_id, []) if fact.group_id else []
    if members:
        gx, gy, gw, gh = _unit_rect(dna, members)
        x, y, w, h = rect
        if fact.role in {"cta_container", "badge_container"} and float(dna.target_canvas["height"]) >= 150:
            # Keep button and badge groups geometrically coherent. Stretching
            # their union to every allocated box distorts capsule shapes and
            # the spacing between label and container. Fit the original group
            # aspect inside the candidate's available rectangle instead.
            group_aspect = gw / max(1.0, gh)
            if w / max(1.0, h) > group_aspect:
                fitted_w, fitted_h = h * group_aspect, h
            else:
                fitted_w, fitted_h = w, w / group_aspect
            x += (w - fitted_w) / 2
            y += (h - fitted_h) / 2
            w, h = fitted_w, fitted_h
            group_scale = min(w / gw, h / gh)
            if group_scale > 1.25:
                # Text fitting caps a group's font at the source size. Beyond
                # modest growth, enlargeable boxes become empty color slabs.
                fitted_w, fitted_h = gw * 1.25, gh * 1.25
                x += (w - fitted_w) / 2
                y += (h - fitted_h) / 2
                w, h = fitted_w, fitted_h
        sx, sy = w / gw, h / gh
        for member_id in members:
            original = dna.by_id[member_id].element
            out = output_by_id[member_id]
            ox, oy = float(original.get("x", 0)), float(original.get("y", 0))
            out["x"], out["y"] = x + (ox - gx) * sx, y + (oy - gy) * sy
            out["width"], out["height"] = max(1.0, float(original.get("width", 1)) * sx), max(1.0, float(original.get("height", 1)) * sy)
            mf = dna.by_id[member_id]
            if original.get("type") == "image" and member_id not in dna.background_ids:
                ix, iy, iw, ih = _fit_image_to_rect(original, (out["x"], out["y"], out["width"], out["height"]))
                out.update(x=ix, y=iy, width=iw, height=ih)
            if original.get("type") == "text":
                out["font_size"] = _fit_size(mf, (out["x"], out["y"], out["width"], out["height"]))
            assigned.add(member_id)
        if fact.role == "cta_container" and float(dna.target_canvas["height"]) < 150:
            # Compact ads reserve a narrow action rail. Use more of the button
            # interior vertically for its label so it stays readable without
            # enlarging the button into the adjacent legal-copy row.
            shape = next((output_by_id[mid] for mid in members
                          if dna.by_id[mid].type == "shape"), None)
            label_id = next((mid for mid in members if dna.by_id[mid].type == "text"), None)
            if shape is not None and label_id is not None:
                label = output_by_id[label_id]
                center_y = float(label["y"]) + float(label["height"]) / 2
                label_height = min(float(shape["height"]) * 0.84, float(label["height"]) * 1.2)
                label["y"] = center_y - label_height / 2
                label["height"] = label_height
                label_fact = dna.by_id[label_id]
                label["font_size"] = _fit_size(
                    label_fact,
                    (float(label["x"]), float(label["y"]), float(label["width"]), label_height),
                )
        return
    out = output_by_id[eid]
    x, y, w, h = rect
    if element.get("type") == "image" and eid not in dna.background_ids:
        x, y, w, h = _fit_image_to_rect(element, rect)
    out.update(x=x, y=y, width=w, height=h)
    if element.get("type") == "text":
        out["font_size"] = _fit_size(fact, (x, y, w, h))
    assigned.add(eid)


def _source_fit(dna: DesignDNA, factor: float = 1.0) -> dict[str, Any]:
    source = dna.source
    sw, sh = float(source["canvas"]["width"]), float(source["canvas"]["height"])
    tw, th = float(dna.target_canvas["width"]), float(dna.target_canvas["height"])
    scale = min(tw / sw, th / sh) * factor
    left, top = (tw - sw * scale) / 2, (th - sh * scale) / 2
    output = deepcopy(source)
    output["canvas"] = dict(dna.target_canvas)
    for e in output["elements"]:
        eid = str(e.get("id", ""))
        if eid in dna.background_ids:
            e.update(x=0.0, y=0.0, width=tw, height=th)
            continue
        e["x"] = left + float(e.get("x", 0)) * scale
        e["y"] = top + float(e.get("y", 0)) * scale
        e["width"] = float(e.get("width", 0)) * scale
        e["height"] = float(e.get("height", 0)) * scale
        if e.get("type") == "text":
            e["font_size"] = max(1.0, float(e.get("font_size", 1)) * scale)
        if e.get("type") == "image" and e.get("fit") != "cover":
            x, y, w, h = _fit_image_to_rect(e, (e["x"], e["y"], e["width"], e["height"]))
            e.update(x=x, y=y, width=w, height=h)
    return output


def _prepare_output(dna: DesignDNA) -> dict[str, Any]:
    output = deepcopy(dna.source)
    output["canvas"] = dict(dna.target_canvas)
    return output


def _legalize_units(dna: DesignDNA, design: dict[str, Any]) -> None:
    """Fit each placed element/group inside the canvas, including rotated bounds."""
    cw, ch = float(dna.target_canvas["width"]), float(dna.target_canvas["height"])
    by_id = {str(element.get("id", "")): element for element in design["elements"]}
    units: list[list[str]] = []
    seen: set[str] = set()
    for ids in dna.groups.values():
        members = [eid for eid in ids if eid in by_id and eid not in dna.background_ids]
        if members:
            units.append(members)
            seen.update(members)
    units.extend([[eid] for eid in by_id if eid not in seen and eid not in dna.background_ids])

    def union_bounds(elements: list[dict[str, Any]]) -> tuple[float, float, float, float]:
        bounds = []
        for element in elements:
            x, y = float(element["x"]), float(element["y"])
            w, h = float(element["width"]), float(element["height"])
            angle = radians(float(element.get("rotation", 0)))
            rw = abs(w * cos(angle)) + abs(h * sin(angle))
            rh = abs(w * sin(angle)) + abs(h * cos(angle))
            cx, cy = x + w / 2, y + h / 2
            bounds.append((min(x, cx - rw / 2), min(y, cy - rh / 2),
                           max(x + w, cx + rw / 2), max(y + h, cy + rh / 2)))
        return (min(b[0] for b in bounds), min(b[1] for b in bounds),
                max(b[2] for b in bounds), max(b[3] for b in bounds))

    for ids in units:
        elements = [by_id[eid] for eid in ids]
        x0, y0, x1, y1 = union_bounds(elements)
        group_cx, group_cy = (x0 + x1) / 2, (y0 + y1) / 2
        factor = min(1.0, cw / max(1.0, x1 - x0), ch / max(1.0, y1 - y0))
        if factor < 1.0:
            for element in elements:
                cx = float(element["x"]) + float(element["width"]) / 2
                cy = float(element["y"]) + float(element["height"]) / 2
                element["width"] = max(1.0, float(element["width"]) * factor)
                element["height"] = max(1.0, float(element["height"]) * factor)
                element["x"] = group_cx + (cx - group_cx) * factor - float(element["width"]) / 2
                element["y"] = group_cy + (cy - group_cy) * factor - float(element["height"]) / 2
                if element.get("type") == "text":
                    element["font_size"] = max(1.0, float(element.get("font_size", 1)) * factor)
        x0, y0, x1, y1 = union_bounds(elements)
        dx = -x0 if x0 < 0 else cw - x1 if x1 > cw else 0.0
        dy = -y0 if y0 < 0 else ch - y1 if y1 > ch else 0.0
        for element in elements:
            element["x"] = float(element["x"]) + dx
            element["y"] = float(element["y"]) + dy


def _group_ids(dna: DesignDNA, role_prefix: str) -> list[str]:
    found = []
    for gid, ids in dna.groups.items():
        roles = [dna.by_id[eid].role for eid in ids]
        if any(role.startswith(role_prefix) for role in roles):
            found.append(gid)
    return found


def _wide_banner(dna: DesignDNA, output: dict[str, Any], by_id: dict[str, dict[str, Any]],
                 assigned: set[str], family: str) -> dict[str, Any]:
    """Place wide creatives in distinct horizontal bands around a focal rail."""
    cw, ch = float(dna.target_canvas["width"]), float(dna.target_canvas["height"])
    left_hero = family == "banner_mirror"
    facts = dna.facts
    roles = lambda *names: [fact for fact in facts if fact.role in names]
    logos = roles("logo")
    heroes = sorted(roles("hero_image", "supporting_image"), key=lambda fact: -fact.importance)
    headlines = sorted(roles("headline"), key=lambda fact: -float(fact.element.get("font_size", 1)))
    narrative = sorted(roles("subheadline", "body_copy"), key=lambda fact: (fact.center[1], fact.center[0]))
    legal = roles("legal")
    cta_groups = _group_ids(dna, "cta")
    badge_groups = _group_ids(dna, "badge")
    other_groups = [gid for gid in dna.groups if gid not in cta_groups and gid not in badge_groups]
    copy_x = cw * (0.28 if left_hero else 0.05)
    copy_right = cw * (0.95 if left_hero else 0.72)
    copy_w = copy_right - copy_x
    hero_x = cw * (0.035 if left_hero else 0.80)
    hero_w, hero_y, hero_h = cw * 0.17, ch * 0.14, ch * 0.74
    for index, fact in enumerate(heroes):
        if index == 0:
            rect = (hero_x, hero_y, hero_w, hero_h)
        else:
            # Preserve secondary artwork in its own small anchor beside the
            # focal rail without letting it sit over campaign copy.
            side_x = cw * (0.22 if left_hero else 0.72)
            rect = (side_x, ch * 0.80, cw * 0.06, ch * 0.10)
        _apply_rect(dna, by_id, fact.id, rect, assigned)

    logo_x = cw * (0.78 if left_hero else 0.05)
    for fact in logos:
        _apply_rect(dna, by_id, fact.id, (logo_x, ch * 0.035, cw * 0.17, ch * 0.15), assigned)

    head_count = max(1, len(headlines))
    head_band = ch * 0.25 / head_count
    for index, fact in enumerate(headlines):
        _apply_rect(dna, by_id, fact.id,
                    (copy_x, ch * 0.27 + index * head_band, copy_w, head_band * 0.92), assigned)
    narrative_count = max(1, len(narrative))
    narrative_band = ch * 0.16 / narrative_count
    for index, fact in enumerate(narrative):
        _apply_rect(dna, by_id, fact.id,
                    (copy_x, ch * 0.53 + index * narrative_band, copy_w, narrative_band * 0.88), assigned)

    if badge_groups:
        gap = cw * 0.014
        cell_w = (copy_w - gap * (len(badge_groups) - 1)) / len(badge_groups)
        for index, gid in enumerate(badge_groups):
            _apply_rect(dna, by_id, dna.groups[gid][0],
                        (copy_x + index * (cell_w + gap), ch * 0.70, cell_w, ch * 0.095), assigned)
    cta_x, cta_w = copy_x, copy_w * 0.40
    for gid in cta_groups:
        _apply_rect(dna, by_id, dna.groups[gid][0], (cta_x, ch * 0.81, cta_w, ch * 0.12), assigned)
    for fact in roles("cta_text"):
        if fact.id not in assigned:
            _apply_rect(dna, by_id, fact.id, (cta_x, ch * 0.81, cta_w, ch * 0.12), assigned)

    for gid in other_groups:
        members = [dna.by_id[eid] for eid in dna.groups[gid]]
        rotated = any(abs(float(member.element.get("rotation", 0))) >= 5 for member in members)
        x = cw * (0.62 if not left_hero else 0.25) if rotated else cw * (0.72 if not left_hero else 0.22)
        y = ch * 0.035 if rotated else ch * 0.82
        w, h = (cw * 0.15, ch * 0.09) if rotated else (cw * 0.06, ch * 0.10)
        _apply_rect(dna, by_id, dna.groups[gid][0], (x, y, w, h), assigned)
    for fact in legal:
        _apply_rect(dna, by_id, fact.id, (copy_x, ch * 0.94, copy_w, ch * 0.05), assigned)

    # Keep any semantics not covered by a named role or group in a quiet rail
    # outside the text and hero columns.
    for fact in facts:
        if fact.id in assigned:
            continue
        e = fact.element
        x = cw * (0.73 if not left_hero else 0.21)
        rect = (x, ch * 0.45, cw * 0.05, ch * 0.12)
        _apply_rect(dna, by_id, fact.id, rect, assigned)
    return output


def _layout(dna: DesignDNA, family: str, variant: int = 0) -> dict[str, Any]:
    if family == "source_fit":
        return _source_fit(dna, (0.88, 0.96, 1.0)[variant % 3])
    output = _prepare_output(dna)
    by_id = {str(e.get("id", "")): e for e in output["elements"]}
    assigned: set[str] = set()
    cw, ch = float(dna.target_canvas["width"]), float(dna.target_canvas["height"])
    margin_scale = (0.055, 0.075, 0.10)[variant % 3]
    mx, my = cw * margin_scale, ch * min(0.09, margin_scale)

    for eid in dna.background_ids:
        _apply_rect(dna, by_id, eid, (0, 0, cw, ch), assigned)

    facts = dna.facts
    logos = [f for f in facts if f.role == "logo"]
    heroes = [f for f in facts if f.role in {"hero_image", "supporting_image"}]
    heads = [f for f in facts if f.role == "headline"]
    subs = [f for f in facts if f.role == "subheadline"]
    bodies = [f for f in facts if f.role == "body_copy"]
    legals = [f for f in facts if f.role == "legal"]
    standalone_ctas = [f for f in facts if f.role == "cta_text" and f.group_id is None]
    cta_groups = _group_ids(dna, "cta")
    badge_groups = _group_ids(dna, "badge")
    other_groups = [gid for gid in dna.groups if gid not in cta_groups and gid not in badge_groups]
    # Any grouped element already consumed as a background is excluded.
    cta_groups = [gid for gid in cta_groups if any(eid not in assigned for eid in dna.groups[gid])]
    badge_groups = [gid for gid in badge_groups if any(eid not in assigned for eid in dna.groups[gid])]

    banner = family in {"banner", "banner_mirror"}
    split = family in {"split", "split_mirror"}
    if banner:
        # The 728x90 leaderboard keeps the specialized compact-row treatment
        # below. Wide campaign canvases have enough vertical room for distinct
        # headline, body, badge, and action bands.
        if dna.target_aspect >= 4.5 and ch >= 300:
            return _wide_banner(dna, output, by_id, assigned, family)
        hero_left = family == "banner_mirror"
        compact = ch < 150
        short_landscape = 360 <= ch < 500
        compact_wide_copy = False
        if compact and len(heads) == 1:
            headline = heads[0].element
            maximum = max(1.0, float(headline.get("font_size", 12)))
            base_size, base_measure = fit_font_size(
                headline, cw * 0.74, ch * 0.40, maximum=maximum, minimum=8.0,
            )
            if base_size <= 8.0 and not base_measure.fits:
                expanded_size, expanded_measure = fit_font_size(
                    headline, cw * 0.875, ch * 0.45, maximum=maximum, minimum=8.0,
                )
                compact_wide_copy = expanded_measure.fits and expanded_size >= 8.0
        hero_x = cw * 0.91 if compact_wide_copy else mx if hero_left else cw * (
            0.88 if compact else 0.79
        )
        hero_w = max(1.0, cw * (
            0.083 if compact_wide_copy else 0.105 if compact else 0.18
        ))
        image_facts = sorted(heroes, key=lambda f: (-f.importance, -f.area_fraction))
        secondary_count = max(0, len(image_facts) - 1)
        hero_y = ch * (0.29 if compact else 0.30)
        hero_h = ch * (0.69 if compact else 0.48 if secondary_count else 0.60)
        for index, fact in enumerate(image_facts):
            if index == 0:
                _apply_rect(dna, by_id, fact.id, (hero_x, hero_y, hero_w, hero_h), assigned)
            elif compact_wide_copy:
                # Keep decorative art in the far-right gutter, away from the
                # full-width supporting and legal copy bands.
                _apply_rect(dna, by_id, fact.id,
                            (cw * 0.84, ch * 0.55, cw * 0.055, ch * 0.07), assigned)
            elif fact.asset_size is None and compact:
                # A missing optional image is rendered as a placeholder by the
                # official renderer; place it in the gap beside the copy and
                # product so neither source text nor the focal image is hidden.
                _apply_rect(dna, by_id, fact.id, (cw * 0.83, ch * 0.55, cw * 0.055, ch * 0.14), assigned)
            elif not compact:
                # Secondary artwork gets its own lower slot in the hero rail;
                # it must not sit under long narrative text in the center.
                rail_y = hero_y + hero_h + ch * 0.025
                rail_bottom = ch * 0.98
                slot_h = max(1.0, (rail_bottom - rail_y) / max(1, secondary_count))
                slot_index = index - 1
                side_x = hero_x + hero_w * 0.08
                side_w = hero_w * 0.65
                _apply_rect(dna, by_id, fact.id,
                            (side_x, rail_y + slot_index * slot_h, side_w, slot_h * 0.88), assigned)
            else:
                # A supporting/secondary image sits beside the primary focal image if space allows.
                x = cw * 0.72 if compact and not hero_left else max(mx, hero_x - hero_w * (index + 1) * 0.92) if not hero_left else min(cw - mx - hero_w, hero_x + hero_w * (index + 1) * 0.92)
                y = ch * 0.39 if compact else hero_y + index * ch * 0.04
                _apply_rect(dna, by_id, fact.id, (x, y, hero_w * (0.72 if compact else 0.42), hero_h * (0.34 if compact else 0.32)), assigned)
        copy_x = mx if not hero_left else min(cw * 0.65, hero_x + hero_w + mx * 0.35)
        copy_w = max(1.0, (hero_x - copy_x - mx * 0.55) if not hero_left else (cw - copy_x - mx))
        if compact:
            # A short banner needs a single broad reading column. Keeping the
            # product in a narrow right rail lets long source copy fit at a
            # useful size while preserving the same elements and wording.
            if compact_wide_copy:
                copy_x, copy_w = cw * 0.02, cw * 0.875
            else:
                copy_x, copy_w = mx, cw * 0.74
        if logos:
            # Anchor the logo in the same side rail as the hero instead of
            # letting it intrude into the copy column on denser banners.
            if compact:
                if compact_wide_copy:
                    logo_x, logo_w = cw * 0.91, cw * 0.083
                else:
                    logo_x = cw * (0.035 if hero_left else 0.88)
                    logo_w = cw * 0.095
            elif hero_left:
                logo_x, logo_w = cw * 0.035, cw * 0.12
            else:
                logo_x, logo_w = hero_x, cw * 0.18
            logo_y = ch * 0.025
            for f in logos:
                logo_h = ch * (0.25 if compact else 0.20)
                _apply_rect(dna, by_id, f.id, (logo_x, logo_y, logo_w, max(1, logo_h)), assigned)
        # Strong type hierarchy in a compact copy column.
        head_y = ch * (
            0.0 if compact_wide_copy else 0.14 if not compact else 0.07
        )
        ordered_heads = sorted(heads, key=lambda a: -float(a.element.get("font_size", 1)))
        ordered_support = sorted(subs + bodies, key=lambda a: (a.center[1], a.center[0]))
        many_narrative = compact and len(ordered_heads) + len(ordered_support) > 2
        if len(ordered_heads) + len(ordered_support) > 2:
            narrative = ordered_heads + ordered_support
            bottom = (0.74 if legals else 0.76) if compact else 0.58
            start = ch * (0.01 if compact else 0.06)
            gap = ch * (0.003 if compact else 0.008)
            weights = [2.0 if f.role == "headline" else 1.0 for f in narrative]
            available = max(1.0, ch * bottom - start - gap * (len(narrative) - 1))
            total_weight = sum(weights)
            for fact, weight in zip(narrative, weights):
                band_h = available * weight / total_weight
                _apply_rect(dna, by_id, fact.id, (copy_x, start, copy_w, band_h), assigned)
                start += band_h + gap
        else:
            for f in ordered_heads:
                current_head_h = ch * (
                    0.45 if compact_wide_copy else 0.40 if compact else 0.24
                )
                _apply_rect(dna, by_id, f.id, (copy_x, head_y, copy_w, current_head_h), assigned)
                head_y += current_head_h * (1.0 if compact else 1.04)
            for f in ordered_support:
                h = ch * (0.16 if ch > 140 else 0.22)
                support_w = copy_w * 0.82 if compact_wide_copy else copy_w
                _apply_rect(dna, by_id, f.id, (copy_x, head_y, support_w, h), assigned)
                head_y += h * 1.02
        for f in standalone_ctas:
            _apply_rect(dna, by_id, f.id, (copy_x, ch * (0.76 if compact else 0.74), min(copy_w * 0.58, cw * 0.34), ch * (0.14 if compact else 0.13)), assigned)
        # Grouped badges form a compact row above the call to action.
        group_y = ch * (0.63 if not compact else 0.80)
        if badge_groups:
            gap = max(2.0, cw * 0.012)
            available = cw * (0.50 if compact else 0.52)
            cell_w = max(1.0, min(cw * (0.16 if compact else 0.19), (available - gap * (len(badge_groups) - 1)) / len(badge_groups)))
            for i, gid in enumerate(badge_groups):
                x = mx + i * (cell_w + gap)
                badge_h = ch * (0.21 if compact else 0.08 if short_landscape else 0.13)
                badge_y = ch * 0.79 if compact else group_y
                _apply_rect(dna, by_id, dna.groups[gid][0], (x, badge_y, cell_w, max(1.0, badge_h)), assigned)
        cta_y = group_y if not badge_groups else group_y + ch * (
            0.19 if compact else 0.10 if short_landscape else 0.14
        )
        for gid in cta_groups:
            x = cw * (0.57 if compact else 0.07)
            w = cw * 0.27
            y = ch * 0.79 if compact else min(ch - ch * 0.24, cta_y)
            h = max(1.0, ch * (0.21 if compact else 0.18 if short_landscape else 0.13))
            _apply_rect(dna, by_id, dna.groups[gid][0], (x, y, w, h), assigned)
        for index, gid in enumerate(other_groups):
            # Unclassified grouped ornaments retain a visible compact treatment.
            is_ribbon = any(abs(float(dna.by_id[eid].element.get("rotation", 0))) >= 5 for eid in dna.groups[gid])
            if compact:
                lane_step = min(0.20, 0.32 / max(1, len(other_groups) - 1)) if len(other_groups) > 1 else 0.0
                if is_ribbon:
                    if compact_wide_copy:
                        rect = (cw * 0.75, ch * 0.59, cw * 0.08, ch * 0.14)
                    elif len(other_groups) == 1:
                        rect = (cw * 0.80, ch * 0.31, cw * 0.08, ch * 0.16)
                    else:
                        rect = (cw * 0.78, ch * (0.25 + lane_step * index), cw * 0.08, ch * 0.16)
                else:
                    rect = (cw * 0.72, ch * (0.42 + lane_step * index), cw * 0.12, ch * 0.16)
            elif is_ribbon:
                rect = (cw * 0.56, ch * (0.04 + 0.08 * index), cw * 0.14, ch * 0.05)
            else:
                rect = (copy_x + copy_w * 0.62, ch * (0.61 + 0.14 * index), copy_w * 0.32, ch * 0.13)
            _apply_rect(dna, by_id, dna.groups[gid][0], rect, assigned)
        for f in legals:
            legal_y = 0.74 if many_narrative else 0.69 if compact else 0.91
            legal_h = 0.05 if many_narrative else 0.10 if compact else 0.07
            legal_w = copy_w * (0.82 if compact_wide_copy else 0.95)
            _apply_rect(dna, by_id, f.id, (copy_x, ch * legal_y, max(1, legal_w), ch * legal_h), assigned)
    elif split:
        image_side_left = family == "split_mirror"
        hero_x = mx if image_side_left else cw * 0.58
        hero_w = cw * 0.34
        for index, f in enumerate(sorted(heroes, key=lambda a: -a.importance)):
            _apply_rect(dna, by_id, f.id, (hero_x, ch * (0.16 + 0.08 * index), hero_w * (0.85 if index else 1), ch * (0.62 if index == 0 else 0.45)), assigned)
        copy_x = cw * 0.53 if image_side_left else mx
        copy_w = cw * 0.40
        if logos:
            for f in logos:
                _apply_rect(dna, by_id, f.id, (copy_x, my, copy_w * 0.44, ch * 0.13), assigned)
        cursor = ch * 0.21
        for f in sorted(heads, key=lambda a: -float(a.element.get("font_size", 1))):
            h = ch * 0.20
            _apply_rect(dna, by_id, f.id, (copy_x, cursor, copy_w, h), assigned)
            cursor += h * 1.12
        for f in subs + bodies:
            h = ch * (0.15 if len(bodies) + len(subs) > 1 else 0.20)
            _apply_rect(dna, by_id, f.id, (copy_x, cursor, copy_w, h), assigned)
            cursor += h * 1.06
        for f in standalone_ctas:
            _apply_rect(dna, by_id, f.id, (copy_x, ch * 0.78, copy_w * 0.62, ch * 0.12), assigned)
        for index, gid in enumerate(badge_groups + cta_groups):
            _apply_rect(dna, by_id, dna.groups[gid][0], (copy_x + (index % 2) * copy_w * 0.50, ch * (0.72 + (index // 2) * 0.12), copy_w * 0.46, ch * 0.11), assigned)
        for f in legals:
            _apply_rect(dna, by_id, f.id, (copy_x, ch * 0.91, copy_w, ch * 0.07), assigned)
    elif dna.target_aspect < 0.72:
        # Compact story/mobile stack with explicit vertical bands. This avoids
        # forcing a wide source into a scaled strip and leaves space for groups.
        for f in logos:
            _apply_rect(dna, by_id, f.id, (cw * 0.34, ch * 0.025, cw * 0.32, ch * 0.08), assigned)
        head_n = max(1, len(heads))
        for i, f in enumerate(heads):
            head_h = min(ch * 0.14, ch * 0.16 / head_n)
            _apply_rect(dna, by_id, f.id, (mx, ch * (0.12 + i * (0.16 / head_n)), cw - 2 * mx, head_h), assigned)
        if heroes:
            for i, f in enumerate(sorted(heroes, key=lambda a: -a.importance)):
                _apply_rect(dna, by_id, f.id, (cw * (0.30 + 0.12 * i), ch * 0.29, cw * (0.40 if i == 0 else 0.24), ch * (0.18 if i == 0 else 0.12)), assigned)
        copy_facts = sorted(subs + bodies, key=lambda f: (float(f.element.get("y", 0)), f.center[0]))
        if copy_facts:
            copy_start = ch * (0.49 if heroes else 0.31)
            copy_band = min(ch * 0.18, max(ch * 0.08, ch * 0.14 * len(copy_facts))) / len(copy_facts)
            for i, f in enumerate(copy_facts):
                _apply_rect(dna, by_id, f.id, (mx, copy_start + i * copy_band, cw - 2 * mx, copy_band * 0.9), assigned)
            badge_start = copy_start + len(copy_facts) * copy_band + ch * 0.02
        else:
            badge_start = ch * (0.56 if heroes else 0.34)
        if badge_groups:
            gap_x, gap_y = max(2.0, cw * 0.018), ch * 0.008
            available_w = cw - 2 * mx
            cell_w = cw * 0.26
            columns = max(1, min(len(badge_groups), int((available_w + gap_x) / (cell_w + gap_x))))
            rows = (len(badge_groups) + columns - 1) // columns
            row_h = min(ch * 0.055, ch * 0.14 / max(1, rows))
            for i, gid in enumerate(badge_groups):
                row, col = divmod(i, columns)
                x = mx + col * (available_w / columns)
                y = badge_start + row * (row_h + gap_y)
                _apply_rect(dna, by_id, dna.groups[gid][0], (x, y, available_w / columns - gap_x, row_h), assigned)
            cta_y = max(ch * 0.77, badge_start + rows * (row_h + gap_y))
        else:
            cta_y = max(ch * 0.77, badge_start)
        for gid in cta_groups:
            _apply_rect(dna, by_id, dna.groups[gid][0], (cw * 0.10, min(ch * 0.89, cta_y), cw * 0.80, ch * 0.12), assigned)
        for f in standalone_ctas:
            _apply_rect(dna, by_id, f.id, (cw * 0.10, min(ch * 0.89, cta_y), cw * 0.80, ch * 0.12), assigned)
        for gid in other_groups:
            _apply_rect(dna, by_id, dna.groups[gid][0], (cw * 0.72, ch * 0.12, cw * 0.12, ch * 0.08), assigned)
        for f in legals:
            _apply_rect(dna, by_id, f.id, (mx, ch * 0.94, cw - 2 * mx, ch * 0.05), assigned)
    elif len(facts) > 30:
        # A dense poster gets distinct narrative, focal, badge, and action bands
        # instead of piling all supporting copy into the same lower region.
        for f in logos:
            _apply_rect(dna, by_id, f.id, (cw * 0.36, ch * 0.025, cw * 0.28, ch * 0.075), assigned)
        for i, f in enumerate(sorted(heads, key=lambda a: -float(a.element.get("font_size", 1)))):
            _apply_rect(dna, by_id, f.id, (mx, ch * (0.11 + i * 0.13), cw - 2 * mx, ch * 0.12), assigned)
        for i, f in enumerate(sorted(heroes, key=lambda a: -a.importance)):
            _apply_rect(dna, by_id, f.id, (cw * (0.40 + 0.12 * i), ch * 0.27, cw * 0.20, ch * 0.14), assigned)
        copy_facts = sorted(subs + bodies + standalone_ctas, key=lambda f: (f.center[1], f.center[0]))
        copy_start, copy_end = ch * 0.43, ch * (0.67 if legals else 0.70)
        copy_band = (copy_end - copy_start) / max(1, len(copy_facts))
        for i, fact in enumerate(copy_facts):
            _apply_rect(dna, by_id, fact.id, (mx, copy_start + i * copy_band, cw - 2 * mx, copy_band * 0.9), assigned)
        if badge_groups:
            gap = cw * 0.018
            available = cw - 2 * mx
            cell_w = (available - gap * (len(badge_groups) - 1)) / len(badge_groups)
            for i, gid in enumerate(badge_groups):
                _apply_rect(dna, by_id, dna.groups[gid][0], (mx + i * (cell_w + gap), ch * 0.71, cell_w, ch * 0.08), assigned)
        for i, gid in enumerate(cta_groups):
            _apply_rect(dna, by_id, dna.groups[gid][0], (cw * 0.34, ch * (0.82 + 0.085 * i), cw * 0.32, ch * 0.075), assigned)
        for i, gid in enumerate(other_groups):
            _apply_rect(dna, by_id, dna.groups[gid][0], (cw * 0.70, ch * (0.22 + i * 0.08), cw * 0.20, ch * 0.055), assigned)
        for f in legals:
            _apply_rect(dna, by_id, f.id, (mx, ch * 0.94, cw - 2 * mx, ch * 0.05), assigned)
    else:
        # Poster/stack family: distribute the narrative vertically with a
        # focal image between title and supporting copy.
        if logos:
            for f in logos:
                _apply_rect(dna, by_id, f.id, (cw * 0.35, my, cw * 0.30, ch * 0.09), assigned)
        if heads:
            for i, f in enumerate(heads):
                head_start = 0.18 if heroes else 0.30
                _apply_rect(dna, by_id, f.id, (mx, ch * (head_start + 0.1 * i), cw - 2 * mx, ch * (0.13 if ch / cw > 1.1 else 0.16)), assigned)
        if heroes:
            area_y = ch * (0.34 if heads else 0.22)
            for i, f in enumerate(sorted(heroes, key=lambda a: -a.importance)):
                _apply_rect(dna, by_id, f.id, (cw * (0.30 + 0.08 * i), area_y + i * ch * 0.04, cw * (0.40 if i == 0 else 0.25), ch * (0.28 if i == 0 else 0.20)), assigned)
        cursor = ch * (0.66 if heroes else 0.40)
        for f in subs + bodies:
            box_h = ch * min(0.15, 0.19 / max(1, len(subs) + len(bodies)))
            _apply_rect(dna, by_id, f.id, (mx, cursor, cw - 2 * mx, box_h), assigned)
            cursor += box_h * 1.06
        if badge_groups:
            gap = cw * 0.025
            cell = min(cw * 0.24, (cw - 2 * mx - gap * (len(badge_groups) - 1)) / len(badge_groups))
            for i, gid in enumerate(badge_groups):
                _apply_rect(dna, by_id, dna.groups[gid][0], (mx + i * (cell + gap), ch * 0.74, cell, ch * 0.10), assigned)
        action_y = 0.82 if heroes or bodies or subs else 0.72
        for i, gid in enumerate(cta_groups):
            _apply_rect(dna, by_id, dna.groups[gid][0], (cw * 0.34, ch * action_y, cw * 0.32, ch * 0.10), assigned)
        for f in standalone_ctas:
            _apply_rect(dna, by_id, f.id, (cw * 0.30, ch * action_y, cw * 0.40, ch * 0.10), assigned)
        for f in legals:
            _apply_rect(dna, by_id, f.id, (mx, ch * 0.93, cw - 2 * mx, ch * 0.05), assigned)

    # Decorations and uncertain elements preserve their broad source position,
    # but are clamped to legal target bounds and never scaled out of view.
    sw, sh = float(dna.source["canvas"]["width"]), float(dna.source["canvas"]["height"])
    for f in facts:
        if f.id in assigned:
            continue
        e = f.element
        x, y, w, h = float(e.get("x", 0)), float(e.get("y", 0)), float(e.get("width", 1)), float(e.get("height", 1))
        if e.get("type") == "image":
            desired_w = min(cw * 0.16, max(20.0, w * min(cw / sw, ch / sh)))
            desired_h = min(ch * 0.25, max(12.0, h * min(cw / sw, ch / sh)))
        else:
            uniform = min(cw / sw, ch / sh)
            desired_w, desired_h = w * uniform, h * uniform
            if f.role == "decoration":
                desired_w, desired_h = min(desired_w, cw * 0.18), min(desired_h, ch * 0.48)
        rect = _clamp_rect((x / sw * cw, y / sh * ch, desired_w, desired_h), dna.target_canvas)
        _apply_rect(dna, by_id, f.id, rect, assigned)
    return output


def generate_candidates(dna: DesignDNA) -> list[dict[str, Any]]:
    families: list[str] = ["source_fit", "stack"]
    if dna.target_aspect >= 0.72:
        families.extend(["split", "split_mirror"])
    if dna.target_aspect >= 1.2:
        families.extend(["banner", "banner_mirror"])
    candidates = []
    for family in families:
        variants = range(3)
        for variant in variants:
            design = _layout(dna, family, variant)
            _legalize_units(dna, design)
            candidates.append({"family": family, "variant": variant, "design": design})
    return candidates
