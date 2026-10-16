# Wide-source event campaign visual review

The hand-composed 1600×900 source places event copy on the left and product art
on the right. The same 11 elements are retained in all outputs.

| Target | Family | Human review |
|---|---|---|
| 1080×1080 square | `split` | Uses a clear headline, date, copy, product, action sequence and fills the square. The product is dominant but the event details remain readable. |
| 1080×1920 vertical story | `stack` | Preserves the order of headline, hero, event details, badge, CTA, and footer. The product looks small because of its source image's transparent bounds; gaps between bands remain. |
| 300×600 mobile story | `stack` | The bold date is now informational copy and no longer overlaps the CTA. The headline and action remain prominent; date and CTA type sizes are close, so the hierarchy diagnostic remains. |
| 728×90 leaderboard | `banner` | The headline, date, and supporting copy are compressed into a busy strip. The grouped CTA remains visible, but the supporting copy is small. |
| 300×250 medium rectangle | `banner` | All content remains present without new intersections. Badge and CTA are small; the hierarchy scorer reports that legal copy is too large relative to these labels. |

Every output preserves IDs/count, text, font families, and image references.
The evaluator reports no off-canvas elements, text clipping, image-ratio
failures, or new accidental collisions. Compact-format hierarchy warnings are
retained in `report.json`. These results are synthetic fixture evidence, not an
Adobe score or a claim about hidden-set performance.
