# Sidecar fixture visual review

This is a hand-composed synthetic source with a left-copy/right-product layout,
two informational badges, a logo, and a CTA. The same 11 elements are carried
through each renderer-backed adaptation.

| Target | Family | Human review |
|---|---|---|
| 1600×900 landscape | `banner` | Retains a clear copy column and product rail. The empty center is broad, but the hierarchy remains easy to scan. [Render](wide_landscape_output.png) |
| 728×90 leaderboard | `banner` | Headline and supporting copy fit the narrow strip; the CTA remains distinct. Supporting copy is small at this size. [Render](leaderboard_output.png) |
| 300×600 story | `stack` | Strong vertical reading order with clear headline, product, body, badges, and a readable primary action. [Render](story_output.png) |
| 1080×1920 vertical story | `stack` | All elements remain legal and readable, but large vertical intervals separate the title, product, copy, and actions. The action backgrounds take substantial area. [Render](vertical_story_output.png) |
| 300×250 medium rectangle | `banner` | Compact, legible hierarchy with all elements present. The product and logo are small but recognizable. [Render](medium_rectangle_output.png) |

The evaluation script reports preserved IDs/counts, copy, font families, image
references, determinism, and internal validation for all five targets. It found
no clipping, off-canvas geometry, image-ratio failures, or new collisions. These
five outputs broaden human-inspected synthetic coverage; they do not represent
official test cases or prove hidden-set performance.
