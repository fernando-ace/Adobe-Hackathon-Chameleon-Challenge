# Internal benchmark report

This score is an internal proxy, not Adobe's hidden evaluator.

- Official samples: 3
- Synthetic stress cases: 24
- Mutations: 15
- Stress structural validity: 100.0%
- Stress off-canvas cases: 0
- Image-ratio failures: 0
- Text-clipping cases: 0
- Collision-free rate: 100.0%
- Determinism rate: 100.0%
- Stress runtime median / p95: 0.2876s / 0.9797s

| Official sample | Baseline proxy | Current proxy | Layout | Candidates | Repairs |
|---|---:|---:|---|---:|---:|
| chameleon_sample_level1_warmup | 68.00 | 100.00 | stack | 12 | 0 |
| chameleon_sample_level2_core | 0.00 | 100.00 | banner | 18 | 0 |
| chameleon_sample_level3_advanced | 0.00 | 100.00 | banner | 18 | 1 |

See `report.json` for per-case diagnostics. Rendered source/baseline/current comparisons are in `../gallery/index.html`.
