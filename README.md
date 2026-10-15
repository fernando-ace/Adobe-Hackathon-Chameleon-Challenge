# Chameleon — responsive campaign design engine

Chameleon takes a finished design and a target canvas, then returns the same elements composed for the new format. It keeps every source ID, element, text string, font family, asset reference, and non-layout property. It can move and resize elements and adjust text font sizes; it never generates or replaces image pixels.

The public Stage 1 entry point remains `resize(source, target_canvas) -> dict` in `engine/resize.py`. This implementation is deterministic and runs locally without inference services.

## Current architecture

1. **Design DNA:** `engine/chameleon/analyzer.py` derives normalized geometry, visible image bounds, asset size/luminance, semantic-role confidence, source composition, groups, anchors, reading order, spacing, alignment, and relationship cues.
2. **Semantic roles:** `semantics.py` uses type, text length/size, position, opacity, area, z-order, rotation, and group context to estimate roles such as background, logo, headline, body, badge, CTA, ribbon, and decoration. These are fallible signals, not labels supplied by Adobe.
3. **Relationship graph:** `relationships.py` records proximity, alignment, containment, same-row/column, group membership, and source overlaps. Existing intentional layering is allowed during collision scoring.
4. **Responsive planning:** `planner.py` creates source-preserving, poster-stack, split, mirrored split, banner, and mirrored-banner candidates. It uses the target aspect ratio and inferred roles, preserving image proportions and grouped pieces.
5. **Typography and image analysis:** `typography.py` measures text with the bundled brand fonts and Skia glyph widths, using the renderer's word-wrap behavior to fit the largest size that fits. `visual_analysis.py` samples text/background contrast over the target background image; this is a lightweight proxy, not a full composite renderer or accessibility certification. `analyzer.py` records image size, alpha bounds, and average linear luminance without editing source assets.
6. **Candidate judge:** `scoring.py` separates canvas legality, image fidelity, typography, collisions, group cohesion, canvas use, target adaptation, and sampled contrast. The score is an internal heuristic and is not Adobe's hidden score.
7. **Repair and validation:** `repair.py` moves lower-priority units in response to diagnosed overlaps or rotated overflow and keeps only score improvements. `validator.py` checks the final output contract. `resize.py` falls back to a contained, bounded transformation if analysis or planning fails. Diagnostics include per-element source/output rectangles, inferred roles, placement reasons, and candidate rankings.

Depending on target aspect ratio, the engine generates 12 or 18 deterministic candidates and repairs the two highest-ranked. Candidate count and diagnostics are available through `get_last_diagnostics()` for local evaluation; the challenge entry-point return value remains the design JSON.

## Setup

Python 3.10 or later is required. Python 3.11 is the development version used for validation.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The renderer dependency is pinned to the commit captured in [`docs/baseline.md`](docs/baseline.md). All required fonts and the real renderer are supplied locally or installed at build time; the engine does not make runtime network requests.

## Run the official samples

```powershell
.\.venv\Scripts\python.exe -m engine.main
```

The three tasks in `input/` produce JSON and renderer-backed PNG previews in `output/`. The upstream, untouched output is preserved in `evidence/baseline/`; current visual evidence and benchmark results are under `evidence/`.

## Tests and benchmarks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m tools.benchmark
```

The test suite checks official examples, ID/count/content/font preservation, geometry, image ratios, rendering, determinism, error fallback, repair, 64 generated adversarial designs (up to 45 elements each), and 45 official-sample mutations. The benchmark writes `evidence/benchmark/report.md`, detailed JSON diagnostics, rendered comparisons, and `evidence/gallery/index.html`.

The [engineering walkthrough](docs/engineering-walkthrough.md) explains the deterministic and heuristic parts, constraint handling, candidate selection, repairs, placement explanations, and current tradeoffs.

All proxy metrics are labeled as internal and should not be interpreted as Adobe scores. Synthetic cases are test fixtures, not unseen-design evidence.

## Docker

Build and run the same offline container shape used by the starter:

```powershell
docker build --platform linux/amd64 -t chameleon-engine .
docker run --rm --network none `
  -v "${PWD}/input:/app/input" `
  -v "${PWD}/output:/app/output" `
  chameleon-engine
```

The image built successfully with `linux/amd64` on 2026-10-15. The three official tasks then ran with `--network none`; JSON and renderer-backed PNG outputs are preserved under [`evidence/docker/`](evidence/docker/). The engine needs no network after the image is built.

## Adobe Express finale prototype

The Stage 2 prototype lives in [`chameleon-express/`](chameleon-express/). It uses the current React/TypeScript add-on scaffold, previews six formats generated by the real local engine, supports per-format placement locking, and contains a Document Sandbox apply path that adds the selected adaptation as a new page.

Start the local engine API from the repository root:

```powershell
.\.venv\Scripts\python.exe chameleon-express/server.py
```

In another terminal, start the add-on from its directory:

```powershell
cd chameleon-express
npm run build
npm run start
```

The add-on host uses `https://localhost:5241`; the local engine API uses `https://localhost:18765`. Adobe's CLI requires a locally trusted HTTPS certificate for sideloading. The development certificate and key are intentionally excluded under `chameleon-express/.local-dev/`; they are not part of the repository.

Finale research, current integration boundaries, demo flow, and pitch are documented in [`docs/finale/`](docs/finale/).

## Evidence and limitations

- [`docs/baseline.md`](docs/baseline.md): untouched starter run and visual findings.
- [`docs/research-notes.md`](docs/research-notes.md): Stage 1 source-backed research, hypotheses, implemented behavior, and measured limits.
- [`docs/finale/express-api-research.md`](docs/finale/express-api-research.md): official Adobe Express API findings and prototype validation limits.
- [`docs/failure-taxonomy.md`](docs/failure-taxonomy.md): current recurring failures, regression evidence, and residual issues.
- [`evidence/gallery/index.html`](evidence/gallery/index.html): rendered source/baseline/current comparisons.
- [`evidence/benchmark/report.md`](evidence/benchmark/report.md): current internal proxy and stress metrics.

The supplied examples and generated corpus are small compared with the hidden evaluation set. Semantic inference and image saliency are heuristic; the contrast estimate samples the background image without compositing every foreground layer. Very wide formats can preserve required content but still force tiny supporting text. The Level 3 sample remains particularly dense at 728×90. The Express prototype currently accepts only the three supplied structured designs and its live Adobe-hosted document-apply path has not yet been verified. Docker's offline build/run passed; the validation and rendered evidence are under `evidence/docker/`.
