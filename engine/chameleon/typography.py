"""Renderer-compatible font measurement and deterministic font fitting."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from renderer.converter.brand_fonts import load_brand_font_manager
import skia
from renderer.converter.wrap import wrap_text


@dataclass(frozen=True)
class TextMeasure:
    fits: bool
    line_count: int
    required_height: float
    widest_line: float
    wrapped_text: str


@lru_cache(maxsize=4)
def _font_manager(fonts_dir: str):
    return load_brand_font_manager(fonts_dir)


@lru_cache(maxsize=32)
def _typeface(fonts_dir: str, family: str, weight: str, style: str):
    manager = _font_manager(fonts_dir)
    return skia.Typeface.MakeFromData(manager.lookup(family, weight, style))


def _font_style(element: dict[str, Any]) -> tuple[str, str]:
    weight = str(element.get("font_weight", "regular")).lower()
    style = "italic" if element.get("font_style") == "italic" else "regular"
    if weight == "bold":
        style = "bolditalic" if style == "italic" else "bold"
    return weight, style


def measure_text(
    element: dict[str, Any], width: float, height: float,
    font_size: float | None = None, fonts_dir: str | Path = "brand_kit/fonts",
) -> TextMeasure:
    content = str(element.get("content", ""))
    size = max(1.0, float(font_size if font_size is not None else element.get("font_size", 1)))
    width = max(0.0, float(width))
    weight, style = _font_style(element)
    fonts_dir = str(Path(fonts_dir))
    face = _typeface(fonts_dir, str(element.get("font_family", "")), weight, style)
    advances = list(skia.Font(face, size).getWidths(skia.Font(face, size).textToGlyphs(content))) if content else []
    letter_spacing = float(element.get("letter_spacing", 0.0))
    advances = [max(0.0, a + (letter_spacing if content[i] not in "\r\n" else 0.0)) for i, a in enumerate(advances)]
    wrapped = wrap_text(content, advances, width)
    lines = wrapped.split("\n") if wrapped else [""]
    line_widths: list[float] = []
    start = 0
    for i, char in enumerate(wrapped):
        if char == "\n":
            line_widths.append(sum(advances[start:i]))
            start = i + 1
    line_widths.append(sum(advances[start:len(wrapped)]))
    line_height = max(0.5, float(element.get("line_height", 1.2)))
    required_height = max(1, len(lines)) * size * line_height
    widest = max(line_widths, default=0.0)
    return TextMeasure(widest <= width + 0.5 and required_height <= float(height) + 0.5,
                       max(1, len(lines)), required_height, widest, wrapped)


def fit_font_size(
    element: dict[str, Any], width: float, height: float,
    maximum: float | None = None, minimum: float = 1.0,
    fonts_dir: str | Path = "brand_kit/fonts",
) -> tuple[float, TextMeasure]:
    """Find the largest renderer-compatible size that fits the proposed box."""
    start = float(maximum if maximum is not None else element.get("font_size", 1))
    low, high = max(1.0, minimum), max(max(1.0, minimum), start)
    best = low
    best_measure = measure_text(element, width, height, best, fonts_dir)
    if best_measure.fits:
        for _ in range(11):
            mid = (low + high) / 2
            candidate = measure_text(element, width, height, mid, fonts_dir)
            if candidate.fits:
                best, best_measure, low = mid, candidate, mid
            else:
                high = mid
    else:
        best_measure = measure_text(element, width, height, best, fonts_dir)
    return max(1.0, best), best_measure
