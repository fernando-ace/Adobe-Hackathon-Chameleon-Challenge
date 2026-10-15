# Stage 1 failure taxonomy

This is the current diagnostic snapshot from `evidence/benchmark/report.json`. The proxy is internal, not Adobe's evaluator. Update this taxonomy when a recurring failure is reproduced, fixed, or superseded by new evidence.

| Category | Current evidence | Status and next action |
|---|---|---|
| Typography and hierarchy | Zero hierarchy regressions across all 64 stress cases and 45 mutations. The earlier 108 stress flags were inherited source ratios, not output regressions. | The scorer compares candidate hierarchy with the source. Compact banner band spacing was rebalanced to resolve the 4× headline and added-copy mutation regressions without clipping or new collisions. |
| Text clipping and excessive shrinkage | No clipped text in the official outputs, stress cases, or mutations. The official Level 3 banner text sizes are: headline 15.09 px, subhead 8.45 px, and legal line 7.91 px. | Preserve every source string. Compact banner tests enforce headline, legal, badge, and CTA floors. Supporting copy is still small at 728×90 and remains a visual limitation. |
| Banner reflow | The official 1600×400 and 728×90 tasks select a banner family. Their current renderer-backed outputs use distinct title, copy, action, and product areas. | Continue visual inspection; a legal banner can still be too dense. The advanced sample remains the weakest official composition. |
| Vertical reflow and target underuse | The 1080×1080 → 1080×1350 warm-up uses a lower action band. A regression test bounds the CTA center to 70–86% of the target height. | The output has intentional negative space below the action. Revisit only if a rendered comparison shows the composition is unbalanced. |
| Collision and grouping | Zero new collisions in the 64-case stress set and 45 mutations. Grouped elements are checked for intact membership and pair placement. | Keep mutation and stress collision checks enabled. No current recurring collision is identified. |
| Off-canvas geometry and image distortion | Zero off-canvas cases and zero image-ratio failures in both suites. Official output validation preserves IDs, counts, text, font families, and source image references. | Keep source bleed distinct from newly introduced overflow; do not regenerate or replace source assets. |
| Rotation and alignment | Rotated decorations and alignment changes are present in the generated mutations; the current suite reports no clipping or collision regressions from them. | These are covered as synthetic cases, not as proof for arbitrary rotations or alignments. Inspect any new failure by its per-element diagnostics. |
| Missing assets | The advanced official sample references a missing optional badge. The renderer emits its placeholder and a warning; the engine keeps the reference. | Preserve this behavior. Do not invent replacement pixels or claim the placeholder is the supplied asset. |
| Runtime and fallback | The 64 stress cases are deterministic and structurally valid; the separate fallback test injects an analyzer failure and checks that IDs and target canvas survive. | The fallback is a last resort, not a quality result. Continue to record fallback use and runtime in benchmark runs. |
| Background contrast and visual balance | Contrast is sampled against the fitted background, but foreground layers are not fully composited. All official renders were inspected; the internal score alone is not a visual acceptance test. | Treat contrast and balance as heuristic signals. Re-render and inspect representative outputs after layout changes. |

## Regression workflow

For a recurring failure, save a deterministic input, identify whether the cause is source data, role inference, candidate placement, text fitting, scoring, or rendering, then fix the general rule. Run the focused regression, the full test suite, the official renderer, and the full benchmark before recording the updated evidence.

The latest full benchmark records 100% structural validity and determinism, zero off-canvas cases, clipping cases, image-ratio failures, and collisions across both suites. Docker build and offline execution passed for all three official samples; see [the Docker validation record](../evidence/docker/validation.md).
