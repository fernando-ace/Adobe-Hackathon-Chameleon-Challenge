# Stage-1 Chameleon rebuild: verified results

Engine frozen at `ff3bdae7595b6d4c1c06cfed05c6f4207a49eb22` before final evaluation. Date: 2026-10-20.

**Assessment: materially safer and more readable, but not ready under the requested strict typography standard.** The primary 1,600-case synthetic corpus has no measured new collisions, clipping, geometry/ratio/contract failures or hierarchy regressions. Small headlines and supporting text still occur; an independent unbreakable-copy red team contains one clipping/fallback case. These are internal, source-relative proxies from one brand kit, not Adobe hidden-set evidence.

## Remote and recovery (items 1–7)

Initial live remote contained only `chameleon-2026-submission`, at `487bc7d9a158ec0a55d6fa3126a5f71d6dc6fa43`. Explicit queries for the lost branch, rebuild branch, main and master were empty. Local `work` was clean at the same SHA. Origin: https://github.com/fernando-ace/Adobe-Hackathon-Chameleon-Challenge.git.

The bounded `/workspace` search found no alternate worktree, bundle, patch or unreachable hardening commits. The old four commits were unrecoverable in this environment. After fetch, the new `goal-2-extreme-format-generalization-rebuild` branch was pushed immediately; local and live remote both matched `487bc7d9a158ec0a55d6fa3126a5f71d6dc6fa43`. Full record: [remote-recovery.md](remote-recovery.md). Historical lost-run metrics were not used as evidence.

## Fresh baseline and final quality (items 8–19, 36–43)

Baseline: all **31 tests passed**. The existing corpus contained 3 official samples, 64 stress cases and 45 sample mutations; no large three-way split existed. All 112 existing cases passed the measured baseline invariants and repeats. Baseline repeats were also checked on development (300), but not on holdout/blind; missing repeat results are not evidence of determinism.

| Split | Cases | Contract failures before → after | Hard-invalid cases before → after | Collision pairs (cases) before → after | Clipped elements before → after | Rotated overflow elements before → after | Ratio failures before → after | Hierarchy pairs before → after | Fallback before → after |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| development | 300 | 0 → 0 | 3 → 0 | 3307 (35) → 0 (0) | 1 → 0 | 6 → 0 | 0 → 0 | 675 → 0 | 0 → 0 |
| holdout | 300 | 0 → 0 | 4 → 0 | 1536 (33) → 0 (0) | 3 → 0 | 2 → 0 | 0 → 0 | 239 → 0 | 0 → 0 |
| blind | 1000 | 0 → 0 | 8 → 0 | 8812 (118) → 0 (0) | 7 → 0 | 3 → 0 | 0 → 0 | 1648 → 0 | 0 → 0 |
| legacy | 112 | 0 → 0 | 0 → 0 | 0 (0) → 0 (0) | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |

Contract validity checks IDs/count, finite positive geometry, required properties, content, fonts, assets and unchanged non-layout properties. Hard validity additionally includes measured text fit, rotated containment and image proportions. Final selection requires these checks plus zero new/worsened intersections under the unchanged base collision classifier. Existing intentional overlap, grouped members, backgrounds and low-z decoration retain the original exemptions; zero counts do not prove pixel-level collision freedom.

All **38 final Python tests pass**, including integration, renderer, source-preservation, identity, minor resize, hierarchy, rotation, dense content, repair and fallback regressions ([tests.txt](tests.txt)). There are zero repeat mismatches across 1,712 final evaluations (1,600 split cases + 112 existing cases). Independent serial/process-worker parity matches **300/300** outputs (100 per split; [parity.json](parity.json)); the engine has no internal parallel-candidate mode.

## Typography (items 44–49)

Headline px, before → after:

| Split | Minimum | p5 | p10 | Median | p90 |
|---|---:|---:|---:|---:|---:|
| development | 7.572 → 7.865 | 15.690 → 21.740 | 23.451 → 27.987 | 33.440 → 37.982 | 53.978 → 54.000 |
| holdout | 4.309 → 5.697 | 21.089 → 22.077 | 23.467 → 27.987 | 33.440 → 37.985 | 53.978 → 54.000 |
| blind | 3.227 → 8.055 | 14.784 → 22.077 | 23.451 → 27.987 | 33.440 → 37.985 | 53.978 → 54.000 |
| legacy | 8.000 → 8.000 | 16.578 → 16.578 | 16.578 → 17.267 | 37.985 → 39.992 | 59.975 → 59.975 |

Important-role metric is the per-design minimum over inferred headline, subheadline and CTA text. It is deliberately separate from headline-only progress:

| Split | Minimum before → after | p5 before → after | p10 before → after | Median before → after |
|---|---:|---:|---:|---:|
| development | 5.324 → 5.666 | 9.861 → 8.987 | 10.107 → 9.861 | 15.996 → 15.996 |
| holdout | 1.990 → 5.387 | 9.861 → 9.031 | 9.861 → 9.861 | 15.996 → 15.996 |
| blind | 3.227 → 3.628 | 8.709 → 7.604 | 9.861 → 9.435 | 15.996 → 15.996 |
| legacy | 8.000 → 6.286 | 9.656 → 7.795 | 9.656 → 9.656 | 15.996 → 17.992 |

**Readability tradeoff:** headline tails improve, but some supporting/CTA tails regress. The existing 112-case important-text minimum falls from 8.000 to 6.286 px. Development important p5 falls from 9.861 to 8.987 px. These regressions are not hidden by the headline result. On the 265 development cases already feasible at baseline, important minimum stays 5.666 px and p5 declines 9.861 → 9.429 px. Dense cases that previously collided now fit, often using smaller secondary typography. This is a remaining quality blocker, not a claim that every readability objective was met.

Blind results by bucket (source-relative proxy; no individual blind case was inspected or used for tuning):

| Bucket | Count | Headline min | p5 | p10 | Median | Important min | Collision / clipping / hard-invalid cases |
|---|---:|---:|---:|---:|---:|---:|---|
| BACKGROUND_HEAVY | 77 | 25.926 | 27.987 | 27.990 | 37.985 | 9.031 | 0 / 0 / 0 |
| CROSS_ORIENTATION | 77 | 27.990 | 27.990 | 27.990 | 37.985 | 15.993 | 0 / 0 / 0 |
| DENSE | 77 | 22.077 | 27.987 | 27.989 | 37.985 | 6.286 | 0 / 0 / 0 |
| GROUP_HEAVY | 77 | 22.077 | 27.987 | 27.987 | 37.985 | 6.286 | 0 / 0 / 0 |
| INTENTIONAL_OVERLAP | 77 | 23.453 | 27.987 | 27.987 | 38.000 | 9.031 | 0 / 0 / 0 |
| LONG_COPY | 77 | 9.436 | 11.679 | 14.231 | 37.982 | 7.501 | 0 / 0 / 0 |
| MISSING_ASSET | 76 | 23.469 | 27.987 | 27.990 | 37.985 | 6.846 | 0 / 0 / 0 |
| NORMAL | 77 | 27.987 | 28.000 | 28.000 | 38.000 | 14.080 | 0 / 0 / 0 |
| ROTATION_HEAVY | 77 | 8.055 | 10.377 | 16.181 | 29.789 | 3.628 | 0 / 0 / 0 |
| TEXT_HEAVY | 77 | 19.736 | 23.322 | 27.945 | 37.982 | 6.286 | 0 / 0 / 0 |
| TRANSPARENT_IMAGES | 77 | 23.453 | 27.838 | 27.990 | 37.985 | 9.031 | 0 / 0 / 0 |
| ULTRA_TALL | 77 | 27.990 | 27.990 | 27.990 | 37.985 | 8.262 | 0 / 0 / 0 |
| ULTRA_WIDE | 77 | 9.572 | 9.580 | 12.278 | 28.303 | 5.666 | 0 / 0 / 0 |

## Engine changes (items 20–30)

- **Extreme-wide:** content-measured headline/narrative lanes compete with secondary columns and a full-height action lane. Image-rail widths vary meaningfully. Source wrapping is not assumed suitable for banners.
- **Extreme-tall and dense:** a coherent logo/headline/metadata/hero/support/action order; dense secondary content can use measured columns instead of one excessively long stack. Sparse extreme-tall designs can still waste height.
- **Readability and wrapping:** measured boxes, several width and line-count choices for rotated text, bounded growth when both usable dimensions increase, source-aware hierarchy protection and stronger severe-headline penalties. No global minimum font was introduced to conceal infeasible layouts.
- **Groups:** complete groups fit uniformly in rotation-aware reserved cells. Secondary groups and text compact before primary text. Source relative alignment and image proportions are preserved; internal group whitespace is not arbitrarily squashed.
- **Candidates and families:** aspect delta, rotation and density determine search budget; identical output geometries are deduplicated. Old families remain available, with allocated lanes/stacks added. All original candidates remain eligible after the top-two repair pass.
- **Collision feasibility and repair:** structural/geometry/image/text/collision feasibility outranks aesthetic score. Repair no longer privileges typography above collision reduction. Source-preserving preference applies to near-identical feasible outputs. A rare disjoint emergency grid is separately diagnosed.
- **Identity and validation:** exact-size identity checks rotation and clipping. At most one pixel of inherited rotated bleed can retain identity, with measured invalidity still reported; resizing has no such exemption. Zero-size geometry and any edits to original non-layout properties are rejected.
- **Render-aware scoring:** existing bundled-font/wrap measurement and 3×3 sampled contrast are retained. No new full-composite top-K rendering term was kept; extra candidate rasterizations = 0. This run does not establish that a pixel-aware reranker improves holdout quality.
- **Performance:** cached DNA ID lookup avoids repeatedly rebuilding maps. No new dependencies or runtime downloads. Finale UI/API source files were untouched.

## Corpora, diagnostics and visual review (items 31–35, 57)

Fixed independent seeds: development **420100**, holdout **730100**, final blind **960100**. Sizes: **300 / 300 / 1000**. Assignment cycles through 13 buckets: normal, cross-orientation, ultra-wide, ultra-tall, dense, text-heavy, long-copy, group-heavy, rotation-heavy, intentional-overlap, background-heavy, transparent images, and missing assets. Development/holdout contain 24 NORMAL and 23 of every other bucket. Blind has 77 in each of the first 12 buckets and 76 MISSING_ASSET. The generator uses a single brand kit and shared design primitives; independent seeds do not establish independent real-world design coverage.

Per-case final data are retained as small `final-*-cases.json.gz` files; full quantiles and bucket metrics are in `final-*.json`. Tools regenerate the source cases from documented seeds. Baseline collision forensics preserve all **3,307 pairs across 35 development cases**, including source/target geometry, family, element roles, overlap area, source relationship, repair count, root class and visual-review status. The compressed file is intentionally curated evidence, not a render cache. Categories: 2,249 rotation-bound pairs; 826 text/text; 224 insufficient-lane; 8 group/group. These are conservative AABB diagnostics, not 3,307 individually confirmed glyph collisions.

The [20-case development contact sheet](development-worst20.png) was generated from smallest headline/important type, lowest proxy, crowding and low-use/readability risks, and visually reviewed. Native renders were inspected at the gallery/contact-sheet level; representative native banner and official images were opened. Dense grids improve over scattered tiny clusters, but tiny rotated labels, missing-asset placeholders, transparent hero padding, weak reading flow and sparse tall under-use remain visible. The score can still overrate legal geometry. No final-blind individual cases were inspected during tuning.

## Runtime and search budget (items 50–53)

Wall-clock seconds; shared 3-CPU workspace with concurrent validation and Docker work. These are observed loaded timings, not isolated speed comparisons:

| Split | Baseline median / p95 | Final median / p95 / worst | Final candidate min / median / p95 / max |
|---|---|---|---|
| development | 0.881 / 4.472 | 0.916 / 3.912 / 7.928 | 1 / 14.500 / 30.000 / 30 |
| holdout | 0.765 / 3.501 | 0.894 / 2.848 / 5.018 | 1 / 9.000 / 30.000 / 30 |
| blind | 0.300 / 2.395 | 0.378 / 1.923 / 10.405 | 1 / 11.000 / 30.000 / 30 |
| legacy | 1.077 / 4.830 | 0.581 / 1.325 / 2.295 | 9 / 15.000 / 30.000 / 30 |

Proxy-score and occupancy min/p5/p10/median/p90 are retained in the JSON summaries. Proxy weights changed, so before/after total proxy scores are not a common calibrated quality scale. Occupancy uses swept union area in the benchmark; the engine still has a coarser canvas-use score and does not yet optimize largest empty rectangles.

## Official samples and Docker (items 54–59)

- **level_1_warmup**: stack; headline 59.975 px; contract, measured fit, ratios and collision checks pass. [PNG](chameleon_sample_level1_warmup.png).
- **level_2_core**: banner; headline 55.977 px; contract, measured fit, ratios and collision checks pass. [PNG](chameleon_sample_level2_core.png).
- **level_3_advanced**: banner; headline 16.578 px; contract, measured fit, ratios and collision checks pass. [PNG](chameleon_sample_level3_advanced.png).

Level 1 retains a readable headline and lower action band. Level 2 keeps copy, campaign marker and action in a broad banner composition. Level 3 uses two headline lines but has very small supporting/legal type and a small transparent product. It retains the source reference to missing `solstice_holiday_badge_2025.png`; the official renderer emits its expected placeholder warning. No asset reference was replaced.

Both baseline and final Linux/amd64 Docker builds succeeded. Final image ID: `2fa94fb25e4feece7b77ecd69601df3a100cc331aee52d38404ebbeb80b6613a`. The build used the original dependencies with a temporary Dockerfile adding only session-CA mounts for build-time pip/git TLS. No session CA is shipped in the image. Under `--network none`, the final image ran **11/11** cases (all 3 official + 8 hard development designs), produced real renderer PNGs, and passed contract/ratio/rotated geometry/clipping/collision checks. All three official JSON outputs exactly match host output. See [docker-validation.json](docker-validation.json) and [docker-official-parity.json](docker-official-parity.json).

## Red team and readiness (items 68–71)

Independent fixed cases test 35 elements with 28 foreground images, multiple CTA groups, Unicode copy, unusual source whitespace, a dense wide-to-tall resize, explicit newlines and unbreakable text. All IDs/content/font families/assets remain intact and all eight repeat exactly. Seven cases are measured feasible; one is explicitly reported infeasible/fallback. No new collisions occurred.

- A 400-character unbreakable `W` headline at 320×50 clips. At the contractual minimum font size and renderer word-wrap rules it cannot fit without breaking fixed copy, altering its rendering, or permitting a smaller font. Fallback diagnostics expose the failure.
- The 120-character unbreakable headline fits at only **2.453 px**; 12 fixed lines fit at **5.950 px**. Structural success is not readability success.
- Held-out/blind minimum headlines and some supporting/CTA fonts remain too small. Supporting-tail regressions are listed above. Sparse ultra-tall canvases can contain large empty regions; transparent asset padding reduces apparent hero mass.
- Semantic roles, group intent and overlap exemptions are heuristic. Multiple unrelated brand systems, difficult scripts/shaping, style-run glyph bounds, extreme intra-group structures and foreground alpha-bound collisions are under-tested.

**Submission readiness:** the requested zero measured primary-corpus collision target is met, but the strict important-text readability objective is only partially met. No claim is made about hidden Adobe performance or guaranteed finale advancement.

**Most dangerous remaining input:** long unbreakable or fixed-line copy combined with rotation and a tiny banner, especially with several mandatory groups/heroes.

**Highest-value next goal:** protect supporting/CTA lower tails without losing the new feasibility gains, add a truly independent multi-brand/script corpus, and validate alpha/glyph-aware occupancy and a render-based top-K judge on held-out data. First resolve legal behavior for copy that is physically infeasible under the 1 px floor.

## Git milestones and closure (items 60–67)

1. Initial branch push at `487bc7d9a158ec0a55d6fa3126a5f71d6dc6fa43`: live equality verified.
2. `2c6057962778c69b69977597c93a96281c9ae8d3` — verified baseline and split tooling: pushed, live equality verified.
3. `ff3bdae7595b6d4c1c06cfed05c6f4207a49eb22` — frozen engine hardening: pushed, live equality verified.
4. This validation/evidence milestone is committed and pushed separately; exact final local/live SHA and clean-tree closure are recorded in the final response because a commit cannot contain its own SHA.

No force pushes, merges or deployments were performed. No Finale UI features or production build changes were made. Generated corpora, environment caches, full temporary galleries, virtual environments and Docker build output remain ignored. Only compact metrics, compressed inspectable case/forensic data and four curated image sheets/samples are tracked.

Reproduce from repository root using the installed requirements:

```sh
python -m unittest discover -s tests -v
python -m tools.hardening_benchmark --split development --size 300 --workers 3 --repeat --output work/development-final.json
python -m tools.hardening_benchmark --split holdout --size 300 --workers 2 --repeat --output work/holdout-validated.json
python -m tools.hardening_benchmark --split blind --size 1000 --workers 2 --repeat --seal --output work/blind-final.json
python -m tools.hardening_benchmark --split legacy --workers 2 --repeat --output work/legacy-final.json
python -m tools.hardening_parity --references work/development-final.json work/holdout-validated.json work/blind-final.json --output work/parity.json
python -m tools.redteam_hardening
```
