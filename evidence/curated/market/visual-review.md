# Wide-source event campaign visual review

The hand-composed 1600×900 source places event copy on the left and product art
on the right. The same 11 elements are retained in all outputs.

| Target | Family | Human review |
|---|---|---|
| 1080×1080 square | `split` | Uses a clear headline, date, copy, product, action sequence and fills the square. The product is dominant but the event details remain readable. |
| 1080×1920 vertical story | `stack` | Preserves the order of headline, hero, event details, badge, CTA, and footer. The product looks small because of its source image's transparent bounds; gaps between bands remain. |
| 300×600 mobile story | `stack` | The bold date is informational copy in a dedicated band between the headline and product. It remains near source scale, and the date, product, supporting copy, badge, CTA, and legal line do not overlap. |
| 728×90 leaderboard | `banner` | The headline, date, and supporting copy are compressed into a busy strip. The grouped CTA remains visible, but the supporting copy is small. |
| 300×250 medium rectangle | `banner` | Wider action groups improve badge and CTA readability while keeping all content present without new intersections. Legal copy remains readable and no longer triggers a hierarchy regression. |

Every output preserves IDs/count, text, font families, and image references.
The evaluator reports no off-canvas elements, text clipping, image-ratio
failures, new accidental collisions, or hierarchy issues. These results are
synthetic fixture evidence, not an Adobe score or a claim about hidden-set
performance.
