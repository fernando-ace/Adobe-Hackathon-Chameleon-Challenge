# Golden Hour fixture review

The hand-composed source is a synthetic 1080×1080 campaign. It uses the supplied
Solstice background, product bottle, and logo with separate headline, support
copy, badge, and CTA. The fixture contains nine elements and is not one of
Adobe's challenge inputs.

| Target | Layout | Inspection |
|---|---|---|
| 1080×1350 social portrait | `source_fit`, 12 candidates | Strong source continuity with a centered headline, product, and paired badge/CTA. The extra height is used without changing the hierarchy. [Render](social_portrait_output.png) |
| 1920×1080 landscape | `banner`, 18 candidates | Clear left-to-right separation between copy, actions, and the product/logo. CTA and badge groups now retain their source proportions, removing the oversized vertical fill seen in the prior render. The broad spacing between narrative and action bands remains a tuning opportunity. [Render](campaign_landscape_output.png) |
| 728×90 ultra-wide banner | `banner`, 18 candidates | The headline and supporting line remain readable at the rendered size, with a compact logo/product on the right and visible actions on the left. [Render](ultrawide_banner_output.png) |
| 300×600 story | `stack`, 6 candidates | A clear vertical flow with a wrapped headline, centered product, legible support copy, and grouped actions. The primary CTA now spans a useful mobile width and is clearly readable. [Render](story_output.png) |

All four outputs preserve the nine IDs, text, font families, and original image
asset IDs. The internal validator reports no clipping, off-canvas elements, or
image-ratio failures; repeated resize calls produce identical JSON. This review
includes the CTA/badge source-proportion repair, which keeps button geometry
coherent on medium and large canvases while leaving compact banners free to
prioritize readable labels. These are useful positive results for one designed
fixture, not evidence of broad generalization; the fixture does not clear the
Stage 1 completion gate.
