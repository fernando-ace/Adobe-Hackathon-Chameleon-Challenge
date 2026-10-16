# Chameleon — Current Final Report

**Status: incomplete.** The Adobe-hosted add-on flow has not been completed; this report does not claim competition victory or proven hidden-set performance.

## Repository and environment

1. **Starting point:** The official starter was cloned into the supplied empty folder root; challenge materials were retained.
2. **Upstream base:** a44a06046b0413f0785e7203955c3822e0acbc32 — Flatten repo to starter root, drop dummy-submission.
3. **Branch and remote:** chameleon-2026-submission; origin remains https://github.com/jhaaj08/chameleon.git.
4. **Environment:** Windows 11, project Python 3.11 venv, Node 22.17.1/npm 10.9.2, Docker Desktop 4.77.0 with Engine 29.5.3, Linux AMD64.
5. Original baseline findings and setup are in ../docs/baseline.md.

## Engine and design intelligence

6. **Engine/API:** engine/resize.py preserves resize(source, target_canvas) -> dict and delegates to deterministic modules under engine/chameleon/.
7. **Design DNA:** analyzer.py records normalized geometry, asset metadata/visible bounds, role confidence, source composition, groups, anchors, reading order, spacing/alignment, transformation severity, and relationships.
8. **Semantic inference:** semantics.py estimates background, logo, headline, copy, CTA, badge, ribbon, hero, and decorative roles from generic visual/text signals; it does not special-case official IDs. These estimates are heuristic.
9. **Relationship extraction:** relationships.py captures grouping, proximity, containment, alignment, row/column, and overlap; scoring distinguishes existing intentional overlap from new or worsened collisions.
10. **Typography:** typography.py uses supplied fonts, Skia glyph widths, renderer-compatible wrapping, and search for the largest fitting size. Stage 1 preserves text/font-family fields; tiny-banner readability remains a gap.
11. **Image analysis:** asset dimensions, alpha bounds, and luminance are recorded; background contrast is sampled. Pixels/references are not regenerated. Contrast sampling is not full compositing or accessibility certification.
12. **Layout families:** source-fit, stack/poster-stack, split and mirrored split, banner and mirrored banner, and very-wide banded layouts.
13. **Candidates:** deterministic 12 or 18 per geometry; official Level 1 used 12 and Levels 2–3 used 18. The two best are offered to repair; official samples needed zero repair moves.
14. **Scoring:** legality, image fidelity, typography, collisions, group cohesion, canvas use, target adaptation, sampled contrast, and source-relative hierarchy. This is an internal proxy, not Adobe's score.
15. **Repair/fallback:** repair.py applies deterministic score-improving moves for diagnosed overlaps/rotated overflow. resize.py provides bounded fallback; the injected-failure test checks preservation of IDs and target canvas.

## Stage 1 results

16. **Level 1:** 1080×1080 to 1080×1350, 4 elements, stack, 12 candidates, 0 repairs, 0.03834 s in the refreshed local benchmark. Internal proxy 68 to 100; starter distorted logo aspect by 20%; current report has no issues.
17. **Level 2:** 1080×1080 to 1600×400, 11 elements, banner, 18 candidates, 0 repairs, 0.07217 s. Internal proxy 0 to 100; starter distorted logo/product by 300%; current report has no issues.
18. **Level 3:** 1080×1350 to 728×90, 17 elements, banner, 18 candidates, 0 repairs, 0.48678 s. Internal proxy 0 to 100; starter distorted three image ratios, had two out-of-bounds items, and reduced headline/subhead/legal text to 2.7/1.5/1.0 px. Current sizes are 15.09/8.45/7.91 px; supporting text is still too small. Renderer uses a placeholder for the missing optional badge; no replacement asset was made.
19. Baseline JSON/PNGs remain under evidence/baseline. Baseline scores 68/0/0 and current scores 100/100/100 are internal proxy values on three supplied fixtures only.
20. **Tests:** 27/27 passed with .venv Python unittest discovery (119.336 s). Coverage includes official contracts/rendering, metamorphic identity and small change, typography, hierarchy, event-date semantic inference, wide-source square recomposition, medium-rectangle action hierarchy, CTA group geometry, tall-format control sizing and band spacing, banner regressions, grouping, repair/fallback, stress/mutations, and local Finale API integration.
21. **Stress/mutations:** 64 generated stress cases (up to 45 elements) and 45 official-input mutations; three representative synthetic stress inputs and before/after renders are preserved in evidence/stress with a reproducible exporter. Synthetic fixtures do not prove hidden-brand generalization.
22. **Structural validity:** 100% in both suites; all official outputs hard-valid under the internal validator. Tests cover IDs, counts, text, fonts, and image references.
23. **Collisions and hierarchy:** 100% no-new-collision rate across both suites and zero hierarchy regressions in the latest full benchmark. The collision metric is source-relative: it detects new or worsened overlaps, so pre-existing clutter in the 45-element synthetic cases is not counted as a collision regression. See evidence/stress/visual-review.md.
24. **Clipping:** zero clipping cases in official, stress, and mutation reports. This does not mean all text is comfortable to read.
25. **Image fidelity:** zero current image-ratio failures in official/stress/mutation evidence. Baseline had 1, 2, and 3 failures respectively.
26. **Determinism:** 100% in stress/mutation reports. Two network-disabled Docker runs were byte-identical for all three samples and matched evidence/docker outputs.
27. **Runtime:** the current Windows venv benchmark stress median/p95 were 0.314205/1.83487 s. Renderer-compatible text measurement increases stress runtime but remains deterministic. Docker sample runs took 0.15/0.17–0.18/0.26–0.32 s for Levels 1–3. Timing varies by host and run.
28. **Docker:** linux/amd64 build succeeded. All three official samples ran and rendered twice under --network none, returning OK with zero validator issues and byte-identical JSON/PNGs; only a nonfatal Fontconfig warning. JSON/PNG hashes matched across runs; PNG hashes were also unchanged from prior validated samples. See evidence/docker/validation.md.
29. **Visual inspection:** Level 1 preserves identity and uses more of the taller canvas. Level 2 changes the compressed starter into a horizontal hierarchy with proportional product imagery and a compact pill-shaped action. Level 3 becomes a deliberate row/banner rather than a crushed design, but its supporting/legal type remains minute. Three hand-composed synthetic campaigns (9, 11, and 11 elements) cover 14 target renders. The wide-source event fixture selects split for square and stack for portrait; its 300×600 date no longer overlaps the CTA. Its leaderboard copy remains small; medium-rectangle action groups are now more legible and no longer trigger hierarchy warnings. The sidecar's 1080×1920 bands use measured text height and are tighter, though open space remains between groups; transparent product artwork still looks small in 300×600. Synthetic_005 and Synthetic_028 are already cluttered at input and remain cluttered after resize; source-relative zero-new-collision metrics do not establish absolute legibility. See evidence/curated/visual-review.md, evidence/curated/sidecar/visual-review.md, evidence/curated/market/visual-review.md, evidence/stress/visual-review.md, evidence/final, evidence/baseline, and evidence/gallery.
30. **Weaknesses:** Only three official examples; three synthetic human-reviewed sources remain a small sample; role/contrast heuristics; the market mobile date/CTA hierarchy warning; small 728×90 copy; missing optional asset placeholder; tiny Level 3 supporting copy; transparent product art appears small; hidden-design quality and Adobe score unknown. See ../docs/failure-taxonomy.md.
31. **Research:** ../docs/research-notes.md covers LayoutGAN, constrained layout, WCAG contrast and metamorphic checks. ../docs/finale-research.md links current Adobe documentation and distinguishes API capability from local evidence.

## Finale

32. **Prototype:** React/TypeScript Adobe add-on scaffold calls the real local Python engine through chameleon-express/server.py. Production webpack build and local package build succeeded. The ZIP in evidence/finale is a local test package, not an Adobe-reviewed listing.
33. **Features:** Three structured sources, six target formats, renderer-backed previews, per-format placement locks, and a Document Sandbox Apply path that appends an editable page with separate text/shapes/images. It does not extract arbitrary open Express designs or follow native selection.
34. **Finale tests:** tests/test_finale_api.py validates six-format generation, preview/image assets, locked headline rectangles, and invalid-source response. Local test passes are not Adobe-hosted behavior.
35. **Demo/pitch:** docs/finale/demo-script.md and docs/finale/pitch.md; concept image at docs/finale/chameleon-express-concept.png.
36. **Adobe-hosted gate:** NOT PASSED. Chrome 155.0.8059.41 previously showed the site-specific Local Network Access setting for https://express.adobe.com at Ask. The user authorized changing it to Allow, but Browser Use's security policy blocked the Chrome-internal settings URL and explicitly disallowed alternate routes; the change could not be applied or re-verified. Adobe's current guide names new.express.adobe.com as the origin that requests local-network access; navigating there in this profile resolved to express.adobe.com. The signed-in home page and Create dialog respond, but opening a blank Instagram Story leads to an editor whose viewport turns white; the Add-ons view remains skeleton placeholders. Console output reports Adobe startup dependency timeouts including AccessProfileStore, CanvasWebView, SelectionStore, and AddOnSettingManager; see docs/finale/express-api-research.md and evidence/finale/express-addons-loading.png. The add-on server returns HTTP 200. No successful Connect, SDK panel load, in-Express generation, lock/regenerate, or Apply was observed. No browser-wide flag was disabled. See Adobe's https://developer.adobe.com/express/add-ons/docs/guides/getting-started/local-development/known-issues-limitations.

## Git and readiness

37. **Local commits:** The 54 commits preceding this final report update are listed below; this final validation/report update is the 55th local commit.
38. **Working tree:** clean after the final local validation and this report update.
39. **Push/deploy:** nothing pushed or deployed.
40. **Stage 1 judgment:** Credible and materially stronger than the starter on available samples, but not proven submission-ready for hidden designs. Three official samples, three hand-composed synthetic sources, adversarial synthetic suites, visual inspection, and an internal proxy do not prove generalization; Level 3 readability, one compact metadata hierarchy issue, and poor-source recovery remain weaknesses.
41. **Highest-value next improvement:** Expand independently designed fixtures and resolve the remaining compact mobile metadata hierarchy issue without compromising CTA prominence or intentional overlaps. The Adobe-hosted Express flow also remains gated on the site-specific Local Network Access setting and needs live Connect, generation, lock/regenerate, and Apply validation.

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
8a1de95 Size portrait copy bands from rendered text
c6d0feb Improve wide-source portrait recomposition
a626d7d Improve medium-rectangle action hierarchy
```
