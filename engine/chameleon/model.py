"""Typed, read-only facts extracted from a Chameleon source design."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Relationship:
    source_id: str
    target_id: str
    kind: str
    strength: float
    intentional: bool = False


@dataclass
class ElementFacts:
    element: dict[str, Any]
    role: str
    confidence: float
    importance: float
    center: tuple[float, float]
    normalized_box: tuple[float, float, float, float]
    area_fraction: float
    aspect_ratio: float
    group_id: str | None = None
    asset_size: tuple[int, int] | None = None
    alpha_bounds: tuple[int, int, int, int] | None = None
    luminance: float | None = None

    @property
    def id(self) -> str:
        return str(self.element.get("id", ""))

    @property
    def type(self) -> str:
        return str(self.element.get("type", "unknown"))


@dataclass
class DesignDNA:
    source: dict[str, Any]
    target_canvas: dict[str, int]
    facts: list[ElementFacts]
    relationships: list[Relationship]
    groups: dict[str, list[str]]
    background_ids: set[str]
    composition: str
    transformation: str
    source_aspect: float
    target_aspect: float
    reading_order: list[str] = field(default_factory=list)
    alignments: list[tuple[str, str, str, float]] = field(default_factory=list)
    spacing_samples: list[tuple[str, str, float]] = field(default_factory=list)
    intentional_overlaps: list[tuple[str, str]] = field(default_factory=list)
    anchor_ids: list[str] = field(default_factory=list)
    repeated_groups: list[list[str]] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    @property
    def by_id(self) -> dict[str, ElementFacts]:
        return {fact.id: fact for fact in self.facts}
