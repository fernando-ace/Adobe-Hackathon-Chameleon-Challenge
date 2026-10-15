"""Lightweight image and local text/background contrast analysis."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import Image

from renderer.converter.assets import load_asset_image
from renderer.converter.colorutil import parse_rgba


@lru_cache(maxsize=4)
def _cover_background(asset_path: str, width: int, height: int) -> Image.Image:
    return load_asset_image(str(Path(asset_path).parent), Path(asset_path).name, width, height, "cover").convert("RGB")


def _linear(channel: int) -> float:
    value = channel / 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def _contrast(a: float, b: float) -> float:
    light, dark = max(a, b), min(a, b)
    return (light + 0.05) / (dark + 0.05)


def _color_samples(element: dict[str, Any]) -> list[tuple[int, int, int, float]]:
    values = [element.get("color")]
    values.extend(run.get("color") for run in element.get("style_runs", []) if run.get("color"))
    samples = []
    for value in values:
        if value:
            samples.append(parse_rgba(str(value), default=(0, 0, 0, -1.0)))
    return [color for color in samples if color[3] >= 0]


def minimum_local_contrast(
    element: dict[str, Any], background: Image.Image,
) -> float | None:
    """Compare text colors to a 3×3 sample of the image beneath its box."""
    colors = _color_samples(element)
    if not colors:
        return None
    x, y = float(element.get("x", 0)), float(element.get("y", 0))
    w, h = max(1.0, float(element.get("width", 1))), max(1.0, float(element.get("height", 1)))
    points = []
    for fy in (0.15, 0.5, 0.85):
        for fx in (0.15, 0.5, 0.85):
            px = min(background.width - 1, max(0, round(x + w * fx)))
            py = min(background.height - 1, max(0, round(y + h * fy)))
            points.append(background.getpixel((px, py)))
    ratios = []
    for color in colors:
        r, g, b, alpha = color
        fg = (_linear(r), _linear(g), _linear(b))
        for pixel in points:
            bg = tuple(_linear(c) for c in pixel)
            blended = tuple(alpha * fg[i] + (1 - alpha) * bg[i] for i in range(3))
            fl = 0.2126 * blended[0] + 0.7152 * blended[1] + 0.0722 * blended[2]
            ratios.append(_contrast(fl, _luminance(pixel)))
    return min(ratios) if ratios else None


def background_for_design(dna, assets_dir: str | Path = "brand_kit/assets") -> Image.Image | None:
    for eid in dna.background_ids:
        fact = dna.by_id[eid]
        asset = Path(assets_dir) / str(fact.element.get("asset_id", ""))
        if asset.is_file():
            return _cover_background(str(asset), int(dna.target_canvas["width"]), int(dna.target_canvas["height"]))
    return None
