# Chameleon — Final Report

**Current status (2026-10-18 client date):** the compact-banner headline fix is implemented and committed locally on `chameleon-2026-submission`; the working tree began clean at baseline `47f805b31d5dd107b74bce43f132dd697715adca`. The full Python suite, official renders, synthetic benchmark, API integration tests, and Adobe Express production build passed in this Linux environment. This follow-up has not been pushed. Hidden-set quality, leaderboard score, and competition outcome remain unknown.

## Current follow-up: reproducibility and compact-banner result

The checkout's active branch initially appeared as `work`; the remote tracking branch `origin/chameleon-2026-submission` pointed to the reported baseline commit. Work continued on a local `chameleon-2026-submission` branch. No `AGENTS.md` files were present. The baseline working tree was clean.

The initial Linux run reproduced the reported 29/30 test result. `test_compact_banner_reserves_readable_action_row` received a 16.296875 px headline against its 16.5 px threshold. The planner had capped the compact headline at 87.5% of canvas width despite available room before the hero rail. Increasing that lane to 88% leaves the headline's right edge at 90% of canvas width and the hero rail starts at 91%. The renderer-compatible size is now 16.578125 px on the 728×90 official sample. The supporting line remains 9.203125 px and legal copy 7.9140625 px. No dependencies were changed. The historical Windows pass is not independently reproduced here, so platform differences cannot be ruled out as a contributor; the observed Linux failure itself was caused by the planner geometry and now passes on Linux.

### Synthetic holdout and regression evidence

`tools/evaluate_compact_headlines.py` compares baseline commit `47f805b` with the current planner over 42 deterministic synthetic cases: six compact target sizes, seven headline lengths, optional grouped ribbon/badge elements, rotated translucent decorations, and varied hero-image proportions. This is a synthetic robustness check, not evidence about the hidden set. The measured summary is in `evidence/benchmark/compact-headline-holdout.json`.

| Measure | Before | After |
|---|---:|---:|
| Mean headline size | 16.0107 px | 16.0390 px |
| Minimum headline size | 6.1372 px | 6.1372 px |
| Cases with a larger headline | — | 10 / 42 |
| Invalid outputs | 0 | 0 |
| Clipped text / new collisions / image-ratio failures | 0 / 0 / 0 | 0 / 0 / 0 |
| Fallback cases | 0 | 0 |
| Median / p95 runtime | 0.1551 / 0.2459 s | 0.1595 / 0.2429 s |

The 640×80 heldout headline grows from 13.578125 px to 14.078125 px. The smallest synthetic banner remains difficult; this targeted change does not improve the set's minimum typography. Official samples retained their 100/100 internal proxy scores. Across the 64 stress cases and 45 input mutations, the benchmark reports 100% validity and determinism, with zero clipping, off-canvas elements, image-ratio failures, hierarchy regressions, or new/worsened collisions before and after. Stress median/p95 runtime in this Linux run was 0.13472/0.58742 s; the previous report's different environment recorded 0.16486/0.96593 s, so that timing difference is not attributed to this change.

Representative official Level 3 renders were visually reviewed. The 728×90 hierarchy and asset placements remain the same; the headline uses the previously unused gutter without touching the product rail. Images: [before](benchmark/compact_headline_before.png) and [after](benchmark/compact_headline_after.png). These are rendered examples, not an independent visual-quality score.

### Commands and environment

Environment: Python 3.12.14, Linux 6.18.55 x86_64, Pillow 13.0.0, skia-python 144.0.post2, `cr-renderer` 0.1.0 at the existing pinned commit `a17e1fb9a732959dd6c21ae168d5ee09d74bd64f`, Node 24.19.0, and npm 11.9.0.

- `.venv/bin/python -m unittest discover -s tests -v` — 31/31 passed; none skipped. This includes official renderer execution and the Finale API tests for six-format generation, previews/assets, locking, and invalid input.
- `.venv/bin/python -m engine.main` — rendered all three official samples successfully.
- `PYTHONPATH=. .venv/bin/python tools/benchmark.py` — 64 stress cases and 45 mutations passed the reported checks.
- `PYTHONPATH=. .venv/bin/python tools/evaluate_compact_headlines.py` — generated the 42-case before/after holdout report.
- `npm run build` from `chameleon-express/` — webpack production build passed.

The API tests and add-on build ran locally. An authenticated Adobe Express browser session was not available in this execution, so live generation, lock regeneration, and editable page application were not rerun. The live result recorded below is historical evidence from the prior report, not a current confirmation.

## Prior validation context (historical)

1. **Starting point:** The official starter was cloned into the supplied empty folder root; challenge materials were retained.
2. **Upstream base:** a44a06046b0413f0785e7203955c3822e0acbc32 — Flatten repo to starter root, drop dummy-submission.
3. **Branch and remote:** chameleon-2026-submission; origin remains https://github.com/jhaaj08/chameleon.git.
4. **Environment:** Windows 11, project Python 3.11 venv, Node 22.17.1/npm 10.9.2, Docker Desktop 4.77.0 with Engine 29.5.3, Linux AMD64.
5. Original baseline findings and setup are in ../docs/baseline.md.

### Engine and design intelligence

6. **Engine/API:** engine/resize.py preserves resize(source, target_canvas) -> dict and delegates to deterministic modules under engine/chameleon/.
7. **Design DNA:** analyzer.py records normalized geometry, asset metadata/visible bounds, role confidence, source composition, groups, anchors, reading order, spacing/alignment, transformation severity, and relationships.
8. **Semantic inference:** semantics.py estimates background, logo, headline, copy, event date/time metadata, CTA, badge, ribbon, hero, and decorative roles from generic visual/text signals; it does not special-case official IDs. These estimates are heuristic.
9. **Relationship extraction:** relationships.py captures grouping, proximity, containment, alignment, row/column, and overlap; scoring distinguishes existing intentional overlap from new or worsened collisions.
10. **Typography:** typography.py uses supplied fonts, Skia glyph widths, renderer-compatible wrapping, and search for the largest fitting size. Stage 1 preserves text/font-family fields; tiny-banner readability remains a gap.
11. **Image analysis:** asset dimensions, alpha bounds, and luminance are recorded; background contrast is sampled. Pixels/references are not regenerated. Contrast sampling is not full compositing or accessibility certification.
12. **Layout families:** source-fit, stack/poster-stack, split and mirrored split, banner and mirrored banner, and very-wide banded layouts.
13. **Candidates:** deterministic 12 or 18 per geometry; official Level 1 used 12 and Levels 2–3 used 18. The two best are offered to repair; official samples needed zero repair moves.
14. **Scoring:** legality, image fidelity, typography, collisions, group cohesion, canvas use, target adaptation, sampled contrast, and source-relative hierarchy. This is an internal proxy, not Adobe's score.
15. **Repair/fallback:** repair.py applies deterministic score-improving moves for diagnosed overlaps/rotated overflow. resize.py provides bounded fallback; the injected-failure test checks preservation of IDs and target canvas.

### Stage 1 results

16. **Level 1:** 1080×1080 to 1080×1350, 4 elements, stack, 12 candidates, 0 repairs, 0.03285 s in the latest local benchmark. Internal proxy 68 to 100; starter distorted logo aspect by 20%; current report has no issues.
17. **Level 2:** 1080×1080 to 1600×400, 11 elements, banner, 18 candidates, 0 repairs, 0.071 s. Internal proxy 0 to 100; starter distorted logo/product by 300%; current report has no issues.
18. **Level 3:** 1080×1350 to 728×90, 17 elements, banner, 18 candidates, 0 repairs, 0.16778 s. Internal proxy 0 to 100; starter distorted three image ratios, had two out-of-bounds items, and reduced headline/subhead/legal text to 2.7/1.5/1.0 px. Current sizes are 17.08/9.20/7.91 px after reallocating two pixels of vertical space to supporting copy; the supporting and legal text remain small. Renderer uses a placeholder for the missing optional badge; no replacement asset was made.
19. Baseline JSON/PNGs remain under evidence/baseline. Baseline scores 68/0/0 and current scores 100/100/100 are internal proxy values on three supplied fixtures only.
20. **Tests:** 30/30 passed in the latest `.venv` Python unittest discovery run (37.507 s). Coverage includes official contracts/rendering, metamorphic identity and small change, minor portrait source-composition preservation, typography, hierarchy, event-date semantic inference and mobile metadata sizing, wide-source square recomposition, medium-rectangle action hierarchy, CTA group geometry, tall-format control sizing and band spacing, compact-banner headline and supporting-copy sizing, extra-copy collision protection, banner regressions, grouping, repair/fallback, stress/mutations, and local Finale API integration.
21. **Stress/mutations:** 64 generated stress cases (up to 45 elements) and 45 official-input mutations; three representative synthetic stress inputs and before/after renders are preserved in evidence/stress with a reproducible exporter. Synthetic fixtures do not prove hidden-brand generalization.
22. **Structural validity:** 100% in both suites; all official outputs hard-valid under the internal validator. Tests cover IDs, counts, text, fonts, and image references.
23. **Collisions and hierarchy:** 100% no-new-collision rate across both suites and zero hierarchy regressions in the latest full benchmark. The collision metric is source-relative: it detects new or worsened overlaps, so pre-existing clutter in the 45-element synthetic cases is not counted as a collision regression. See evidence/stress/visual-review.md.
24. **Clipping:** zero clipping cases in official, stress, and mutation reports. This does not mean all text is comfortable to read.
25. **Image fidelity:** zero current image-ratio failures in official/stress/mutation evidence. Baseline had 1, 2, and 3 failures respectively.
26. **Determinism:** 100% in stress/mutation reports. Two network-disabled Docker runs were byte-identical for all three samples and matched evidence/docker outputs.
27. **Runtime:** the current Windows venv benchmark stress median/p95 were 0.16486/0.96593 s. Renderer-compatible text measurement increases stress runtime but remains deterministic. The latest clean offline Docker runs took 0.15–0.18 s/0.18 s/0.19–0.21 s for Levels 1–3. The 2026-10-18 incremental-image runs took 0.13 s/0.16–0.18 s/0.17–0.22 s. Timing varies by host and run.
28. **Docker:** Both ordinary and `--no-cache` linux/amd64 builds succeeded. After the compact-banner text-band change and again after source-fit scoring alignment, all three official samples ran twice under `--network none`; JSON/PNG outputs were byte-identical across each pair. The latest clean build reinstalled dependencies and matched all six current artifact hashes. The scoring update left official outputs unchanged. The only warning was nonfatal Fontconfig output. See evidence/docker/validation.md.
29. **Visual inspection:** Level 1 preserves identity and uses more of the taller canvas. Level 2 changes the compressed starter into a horizontal hierarchy with proportional product imagery and a compact pill-shaped action. Level 3 becomes a deliberate row/banner rather than a crushed design; the headline stays at 17.08 px and supporting copy rises from 8.45 px to 9.20 px, while legal copy remains small. Three hand-composed synthetic campaigns (9, 11, and 11 elements) cover 14 target renders. The Golden Hour campaign now preserves its centered source composition for a minor square-to-4:5 shift. The wide-source event fixture selects split for square and stack for portrait; the 300×600 date has its own band above the product and no new hierarchy/collision issues. Its leaderboard copy remains small; medium-rectangle action groups are more legible and do not trigger hierarchy warnings. The sidecar's 1080×1920 bands use measured text height and are tighter, though open space remains between groups; transparent product artwork still looks small in 300×600. The current stress evidence selects `synthetic_049`, `synthetic_005`, and `synthetic_001`; the 45-element cases start cluttered, so source-relative collision metrics do not establish absolute legibility. See evidence/curated/visual-review.md, evidence/curated/sidecar/visual-review.md, evidence/curated/market/visual-review.md, evidence/stress/visual-review.md, evidence/final, evidence/baseline, and evidence/gallery.
30. **Weaknesses:** Only three official examples; three synthetic human-reviewed sources remain a small sample; role/contrast heuristics; small 728×90 copy; missing optional asset placeholder; tiny Level 3 supporting/legal copy; transparent product art appears small; hidden-design quality and Adobe score unknown. See ../docs/failure-taxonomy.md.
31. **Research:** ../docs/research-notes.md covers LayoutGAN, constrained layout, WCAG contrast and metamorphic checks. ../docs/finale-research.md links current Adobe documentation and distinguishes API capability from local evidence.

### Finale

32. **Prototype:** React/TypeScript Adobe add-on scaffold calls the real local Python engine through chameleon-express/server.py. Production webpack build and local package build succeeded. The ZIP in evidence/finale is a local test package, not an Adobe-reviewed listing.
33. **Features:** Three structured sources, six target formats, renderer-backed previews, per-format placement locks, and a Document Sandbox Apply path that appends an editable page with separate text/shapes/images. It does not extract arbitrary open Express designs or follow native selection.
34. **Finale tests:** tests/test_finale_api.py validates six-format generation, preview/image assets, locked headline rectangles, and invalid-source response. Local test passes are not Adobe-hosted behavior.
35. **Demo/pitch:** docs/finale/demo-script.md and docs/finale/pitch.md; concept image at docs/finale/chameleon-express-concept.png.
36. **Adobe Express live gate (historical):** The prior report recorded a successful local development build in a signed-in Express editor: six Level 3 previews, headline locking through regeneration, and Apply creating an editable 1080×1350 page with 8 text nodes, 5 shapes, and 3 image nodes. The optional `holiday_watermark` source asset was skipped. This live check was not rerun in the current Linux execution; see the current validation section above. It does not verify Marketplace review, hidden-set quality, or competition results. Adobe's [Large Document Support guide](https://developer.adobe.com/express/add-ons/docs/guides/learn/platform-concepts/large-document-support) describes the active-page callback requirement. Earlier failed connection attempts and Adobe startup errors are retained in docs/finale/express-api-research.md.

### Git and readiness at the prior checkpoint

37. **Local commits:** The 71 commits since the upstream base preceding that report update are listed below; its final validation/report update was the 72nd local commit.
38. **Working tree:** clean at that prior checkpoint.
39. **Push/deploy:** commits through that prior report were pushed to `fernando-ace/Adobe-Hackathon-Chameleon-Challenge` on `chameleon-2026-submission`. The current follow-up has not been pushed. No deployment was requested or performed.
40. **Stage 1 judgment:** Credible and materially stronger than the starter on available samples, but not proven submission-ready for hidden designs. Three official samples, three hand-composed synthetic sources, adversarial synthetic suites, visual inspection, and an internal proxy do not prove generalization; Level 3 readability and poor-source recovery remain weaknesses.
41. **Highest-value next improvement:** Expand independently designed fixtures and improve small text in compact banners and posters. The live integration is verified locally; a hidden-set or Adobe leaderboard result is still unavailable.

### Every local commit after the upstream base

```text
efd1601 docs: preserve untouched chameleon baseline
16472f5 feat: add deterministic responsive layout engine
5200345 test: add metamorphic checks and placement diagnostics
7c12082 fix: give compact banner actions more room
0a9a851 test: expand adversarial corpus and harden crowded layouts
73a491c improve compact banner visual hierarchy
9efe23c assert compact banner prominence
eb14b9a document Docker startup blocker
e10285f report mutation quality and determinism
66c1020 test larger canvas typography stability
c818276 improve sparse portrait vertical rhythm
620902f score hierarchy regressions against source
a0ad95d balance dense banner narrative bands
27a44a0 record offline Docker validation evidence
8f6f096 build Adobe Express finale prototype
45c29e6 refresh final benchmark evidence
05e16bf fix Express apply image asset wiring
4d13085 improve extreme wide banner composition
00af391 document Adobe Express finale research
d0d9525 package Adobe Express finale add-on
47ea631 record Express developer terms gate
dc9c6d2 update Express consent and sideload status
391f6e5 refresh final stress benchmark evidence
9963813 record latest offline Docker validation
8ecc41e remove redundant Docker platform pin
b36a0ac record restarted Express API generation check
5d4e187 record live Express generation attempt
ef6967d correct Express live validation claims
36bee0b Improve banner layout regression coverage
3752dff Refresh Linux benchmark and Express status evidence
5a9e9b6 Add Express prototype API integration tests
e2e57b8 Document Finale API integration coverage
7c65ac5 Test source preview in finale API integration
3c643bd Record Express browser verification blocker
ee9c5a2 Record final Docker benchmark and Express status
4d5a47d Document Chrome local access sideload blocker
57fddd5 Add current Chameleon evidence audit report
8e636e0 Record Chrome version in Express access audit
902d881 Record representative synthetic stress evidence
820005f Record current Express loading diagnostics
e5dc410 Clarify source-relative collision evidence
c410ebd Add independent curated layout evaluation
7f2bf86 Record Express editor startup failures
2109fcb Record final Docker benchmark validation
8b25fee Improve responsive CTA group layout
498a009 Add independent sidecar layout fixture
caba8c3 Cap tall-format button group scaling
313caba Tighten tall story layout bands
7d4057d Refresh tall reflow evidence report
26a0266 Refresh portrait copy sizing evidence
8a1de95 Size portrait copy bands from rendered text
c6d0feb Improve wide-source portrait recomposition
92fcb95 Record wide-source benchmark results
a626d7d Improve medium-rectangle action hierarchy
9d9f312 Record medium-rectangle validation
f323086 Keep event date hierarchy in mobile layouts
79d1606 Record event metadata benchmark evidence
671ff82 Refresh current stress visual evidence
4908720 Update final report with current stress evidence
cbb7e04 Record clean offline Docker build
f18c233 Record clean Docker validation
11fa3d8 Improve compact banner headline fit
aa8cd5c Refresh final banner validation report
6ad8564 Record latest Express connection failure
050b48a Update Express live verification status
d892560 docs: record renewed Express connection attempt
a2d84bb evidence: refresh stress benchmark
439b4ef improve compact banner supporting copy
058785d improve source-fit scoring for minor changes
3f0dab5 document Express sideload diagnostics
b2fed24 fix Express document apply async editing
```
