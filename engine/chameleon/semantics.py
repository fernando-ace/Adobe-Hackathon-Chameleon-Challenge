"""Conservative semantic role inference based only on general design cues."""

from __future__ import annotations

import re
from typing import Any


_DATE_WORDS = re.compile(
    r"\b(?:mon(?:day)?|tue(?:s|sday)?|wed(?:nesday)?|thu(?:rs|rsday)?|fri(?:day)?|"
    r"sat(?:urday)?|sun(?:day)?|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\b",
    re.IGNORECASE,
)
_CLOCK_TIME = re.compile(r"\b\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)\b", re.IGNORECASE)
_NUMERIC_DATE = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b")


def infer_roles(elements: list[dict[str, Any]], canvas: dict[str, float]) -> dict[str, tuple[str, float, float]]:
    width, height = float(canvas["width"]), float(canvas["height"])
    area = max(1.0, width * height)
    result: dict[str, tuple[str, float, float]] = {}
    texts = [e for e in elements if e.get("type") == "text"]
    sizes = sorted((float(e.get("font_size", 1)) for e in texts), reverse=True)
    largest = sizes[0] if sizes else 1.0
    cta_verbs = {
        "apply", "book", "browse", "buy", "call", "claim", "click", "contact",
        "discover", "download", "explore", "find", "get", "join", "learn",
        "order", "play", "register", "reserve", "save", "see", "shop", "sign",
        "start", "subscribe", "try", "view", "visit", "watch",
    }

    for element in elements:
        eid = str(element.get("id", ""))
        etype = element.get("type")
        x, y = float(element.get("x", 0)), float(element.get("y", 0))
        w, h = max(0.0, float(element.get("width", 0))), max(0.0, float(element.get("height", 0)))
        fraction = (w * h) / area
        cx, cy = (x + w / 2) / width, (y + h / 2) / height
        z = int(element.get("z_index", 0))
        if etype == "image":
            if fraction >= 0.58 and z <= min((int(e.get("z_index", 0)) for e in elements), default=0) + 1:
                result[eid] = ("background", 0.94, 0.25)
            elif fraction < 0.10 and cy < 0.30 and h > 0 and w / h >= 1.5:
                result[eid] = ("logo", 0.58, 0.90)
            else:
                result[eid] = ("hero_image" if fraction >= 0.08 else "supporting_image", 0.62, 0.84 if fraction >= 0.08 else 0.55)
        elif etype == "text":
            size = float(element.get("font_size", 1))
            content = str(element.get("content", "")).strip()
            length = len(content)
            action_words = set(re.findall(r"[a-z]+", content.lower()))
            rel_size = size / max(1.0, largest)
            date_time = bool(_DATE_WORDS.search(content) or _CLOCK_TIME.search(content) or _NUMERIC_DATE.search(content))
            if size <= max(14.0, largest * 0.28) and (cy > 0.78 or length > 60):
                role, confidence, importance = "legal", 0.66, 0.25
            elif rel_size >= 0.72:
                role, confidence, importance = "headline", 0.78, 1.0
            elif date_time:
                role, confidence, importance = "subheadline", 0.72, 0.62
            elif length <= 24 and element.get("font_weight") == "bold" and element.get("group_id"):
                role, confidence, importance = "group_label", 0.68, 0.54
            elif length <= 42 and (element.get("font_weight") == "bold" or action_words & cta_verbs):
                role, confidence, importance = "cta_text", 0.55, 0.72
            elif length > 44:
                role, confidence, importance = "body_copy", 0.67, 0.48
            else:
                role, confidence, importance = "subheadline", 0.55, 0.64
            result[eid] = (role, confidence, importance)
        elif etype == "shape":
            grouped = bool(element.get("group_id"))
            result[eid] = ("group_container" if grouped else "decoration", 0.58 if grouped else 0.65, 0.54 if grouped else 0.22)
        else:
            result[eid] = ("unknown", 0.0, 0.4)

    # Group membership and containment are general signals for buttons and badges.
    groups: dict[str, list[dict[str, Any]]] = {}
    for element in elements:
        gid = element.get("group_id")
        if gid:
            groups.setdefault(str(gid), []).append(element)
    # Imperative/action language is a general CTA cue. Tokenize into words so
    # phrases such as "explore the collection" work without matching inside
    # unrelated words or depending on a particular campaign's IDs.
    for members in groups.values():
        labels = [e for e in members if e.get("type") == "text"]
        shapes = [e for e in members if e.get("type") == "shape"]
        if not labels or not shapes:
            continue
        text = " ".join(str(e.get("content", "")) for e in labels).lower()
        is_rotated = any(abs(float(e.get("rotation", 0))) >= 5 for e in members)
        group_words = set(re.findall(r"[a-z]+", text))
        group_role = ("cta" if group_words & cta_verbs
                      else "ribbon" if is_rotated else "badge")
        for e in members:
            eid = str(e.get("id", ""))
            old = result.get(eid, ("unknown", 0.0, 0.4))
            if e.get("type") == "shape":
                result[eid] = (f"{group_role}_container", max(old[1], 0.76), 0.68 if group_role == "cta" else 0.42)
            elif e.get("type") == "text":
                label_role = "cta_text" if group_role == "cta" else "ribbon_text" if group_role == "ribbon" else "badge_text"
                result[eid] = (label_role, max(old[1], 0.72), 0.78 if group_role == "cta" else 0.48)
    return result
