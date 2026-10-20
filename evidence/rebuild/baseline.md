# Fresh rebuild baseline

Authoritative engine base: `487bc7d9a158ec0a55d6fa3126a5f71d6dc6fa43`.
All measurements below were made before connecting hardening code.
Historical lost-run numbers were not used as evidence.

- All 31 existing Python/integration tests pass (33.068 s).
- Existing official/stress/mutation benchmark: 3 / 64 / 45 cases. Zero structural,
  collision, clipping, off-canvas, image-ratio, hierarchy or fallback failures;
  all 112 repeat evaluations match exactly.
- New development split: 300 cases, seed 420100. Zero contract/ratio/fallback
  failures. 3 rotation-aware hard-invalid cases, 35 collision cases (3307 pair
  intersections), 1 clipped text element, 6 rotated overflows, 675 pairwise
  hierarchy regressions. Repeat determinism: 300/300.
- Development headline min / p5 / p10 / median: 7.571573 / 15.690267 /
  23.450879 / 33.44 px. Important-role minimum: 5.323864 px.
- Development runtime median / p95: 0.880859 / 4.472262 s. These wall times were
  measured in concurrent process workers on a shared 3-CPU workspace, alongside
  other baseline runs and a Docker build. They are not isolated latency claims.
- Official samples rendered with the supplied renderer into ignored local work.
- Linux/amd64 baseline Docker image built successfully, using a temporary
  Dockerfile that mounts the session CA for pip/git without changing dependencies.
  Offline execution result is recorded in the final validation report.

Detailed compact summaries and bucket metrics are in `baseline-*.json`.
The synthetic three-way split uses independent seeds 420100 / 730100 / 960100,
with 300 development, 300 holdout and 1000 final-blind cases. Blind individual
results remain unopened during tuning. Bucket assignment cycles through 13
categories; these generators test geometry and content variation within a single
brand kit, not general visual-design distribution coverage. Source-relative
collision classification is inherited unchanged from the base scorer.

Reproduce: `python -m tools.hardening_benchmark --split development --size 300
--workers 4 --repeat --output work/baseline-development.json`.
Use `--split legacy` for the existing 112 cases.
