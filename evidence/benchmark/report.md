# Internal benchmark report

This score is an internal proxy, not Adobe's hidden evaluator.

- Official samples: 3
- Synthetic stress cases: 64 (default 64)
- Mutations: 45
- Stress structural validity: 100.0%
- Stress off-canvas cases: 0
- Image-ratio failures: 0
- Text-clipping cases: 0
- Stress hierarchy regressions: 0 across 0 cases
- No-new-collision rate (source-relative): 100.0%
- Determinism rate: 100.0%
- Stress runtime median / p95: 0.2329s / 1.6725s

- Mutation structural validity: 100.0%
- Mutation off-canvas cases: 0
- Mutation image-ratio failures: 0
- Mutation text-clipping cases: 0
- Mutation hierarchy regressions: 0 across 0 cases
- Mutation no-new-collision rate (source-relative): 100.0%
- Mutation determinism rate: 100.0%

- Collision metric: Counts only new or worsened intersections relative to the source; pre-existing overlap is not counted as a regression.

| Official sample | Baseline proxy | Current proxy | Layout | Candidates | Repairs |
|---|---:|---:|---|---:|---:|
| chameleon_sample_level1_warmup | 65.52 | 100.00 | stack | 12 | 0 |
| chameleon_sample_level2_core | 0.00 | 100.00 | banner | 18 | 0 |
| chameleon_sample_level3_advanced | 0.00 | 100.00 | banner | 18 | 0 |

See `report.json` for per-case diagnostics. Rendered source/baseline/current comparisons are in `../gallery/index.html`.
