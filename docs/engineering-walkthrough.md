# Engineering walkthrough

## Why this architecture exists

Stage 1 receives a finished design as structured JSON and must adapt it without changing its identity: IDs, element count, text, font families, asset references, and image content stay fixed. A single scale factor cannot satisfy those constraints across a square post, a wide ad, and a narrow banner. The engine therefore separates source analysis, layout generation, candidate judging, repair, and final contract validation. Each part runs locally and deterministically; the renderer and brand kit provide the actual fonts and source images.

## What is deterministic and what is heuristic

Given the same input, the engine uses the same role rules, generated families and variants, tie-breaking order, font measurements, and repair order. It makes no model or network calls. The result is reproducible.

The meaning inferred from the source is heuristic. Text length, font size, z-order, shape type, position, opacity, group IDs, and geometry suggest roles such as headline, logo, badge, and hero image. Asset dimensions and pixel summaries help distinguish image roles. Those signals can be wrong; confidence and source geometry remain available in `get_last_diagnostics()`.

## Design DNA and constraints

`analyze_design` constructs a `DesignDNA` record with source and target canvases, normalized element geometry, inferred roles, groups, anchors, reading order, alignment and spacing cues, source overlaps, image metadata, and transformation severity. Pairwise relations describe containment, alignment, proximity, grouping, and overlap.

The final validator protects IDs and count, required fields, text, font families, image references, and positive finite geometry. Candidate scoring separately enforces image proportions. Text fitting uses the installed brand fonts and renderer-compatible line wrapping. An exact-size request returns the source elements unchanged when the source is valid; explicitly documented intentional source bleed is retained. Invalid, undocumented source geometry still enters normal planning and must pass validation.

## Candidate generation and scoring

Depending on target aspect ratio, the planner emits 12 or 18 candidates from source-fit, stack, split, mirrored split, banner, and mirrored banner families. Each family places the inferred narrative roles differently while transforming grouped elements together and keeping image proportions.

The local proxy reports canvas legality, image fidelity, measured text fit, collisions, group cohesion, target adaptation, canvas use, sampled contrast, and hierarchy. It is a ranking aid, not Adobe's score. Overlap already present in the source is not called new unless the output worsens it; documented corner bleed is treated similarly when its normalized amount does not increase. New or worsened violations remain penalized. Candidate score, family, variant, validity, and issues are available in diagnostics.

## Repair and placement explanations

The two best candidates enter a deterministic repair pass. The pass moves lower-priority units in a fixed set of directions, keeps group members together, and accepts a move only if the proxy improves. Final validation can reject a candidate and use the bounded fallback instead.

For each chosen element, `get_last_diagnostics()` reports its inferred role, confidence, group, normalized source/output rectangles, and a short family-and-role placement reason. This makes a decision inspectable: compare the source rectangle, final rectangle, semantic cue, chosen layout family, and candidate rankings. These are explanations of the heuristics the engine applied, not evidence that its role inference is always correct.

## Research influence and tradeoffs

Layout generation research motivated an explicit relationship graph and multiple candidates; constraint-based design work motivated separate legality, fidelity, and aesthetic signals. Renderer-backed font measurement and image-background sampling address fit and contrast without introducing remote dependencies. See [research notes](research-notes.md) for sources and the distinction between findings, hypotheses, implementation, and measurements.

The deterministic system is explainable, portable, and compliant with offline execution. Its limitations are heuristic role inference, simplified image/background analysis, a small official sample set, and limited ability to make a crowded 728×90 creative readable while preserving every text string. The internal proxy can also reward legal geometry that still looks weak. The Level 3 result and its tiny supporting type remain a known quality gap.
