# Sidecar fixture visual review

This is a hand-composed synthetic source with a left-copy/right-product layout,
two informational badges, a logo, and a CTA. The same 11 elements are carried
through each renderer-backed adaptation.

| Target | Family | Human review |
|---|---|---|
| 1600×900 landscape | `banner` | Retains a clear copy column and product rail. The empty center is broad, but the hierarchy remains easy to scan. [Render](wide_landscape_output.png) |
| 728×90 leaderboard | `banner` | Headline and supporting copy fit the narrow strip; the CTA remains distinct. Supporting copy is small at this size. [Render](leaderboard_output.png) |
| 300×600 story | `stack` | The tighter bands keep headline, copy, badges, and action in a clear order. The product remains small because the original square asset has transparent margins. [Render](story_output.png) |
| 1080×1920 vertical story | `stack` | The tighter bands bring the hero closer to the copy and move actions upward. CTA and badge fills keep source proportions and are capped at modest growth; a broad interval remains between copy and benefit badges. [Render](vertical_story_output.png) |
| 300×250 medium rectangle | `banner` | Compact, legible hierarchy with all elements present. The product and logo are small but recognizable. [Render](medium_rectangle_output.png) |

The evaluation script reports preserved IDs/counts, copy, font families, image
references, determinism, and internal validation for all five targets. It found
no clipping, off-canvas geometry, image-ratio failures, or new collisions. These
five outputs broaden human-inspected synthetic coverage; they do not represent
official test cases or prove hidden-set performance.
