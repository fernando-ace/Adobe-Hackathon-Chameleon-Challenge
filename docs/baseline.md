# Untouched starter baseline

## Starting point

- Starter repository: `https://github.com/jhaaj08/chameleon.git`
- Upstream commit: `a44a06046b0413f0785e7203955c3822e0acbc32` (`Flatten repo to starter root, drop dummy-submission`)
- Development branch: `chameleon-2026-submission`
- Baseline code was run before any engine edits. The original engine is the uniform x/y stretch in `engine/resize.py`.
- Runtime: Python 3.11.9 on Windows x64. Dependencies installed in `.venv/`; `cr-renderer` resolved to `a17e1fb9a732959dd6c21ae168d5ee09d74bd64f`.
- CPU: Intel Core Ultra 9 185H, 16 cores / 22 logical processors. Docker CLI/buildx are installed. The initial Docker Desktop startup failed; recovery and the later successful container validation are recorded below.

## Run

```powershell
.\.venv\Scripts\python.exe -m engine.main
```

The command completed successfully for all three official samples and rendered through `renderer.converter.convert` (the vendored renderer, not the fallback box preview). Baseline JSON and PNG files are preserved in [`evidence/baseline/`](../evidence/baseline/).

## Official sample results

| Sample | Source → target | Elements | Engine time shown by runner | Structural warning | Visual finding |
|---|---:|---:|---:|---|---|
| Level 1 warm-up | 1080×1080 → 1080×1350 | 4 | <0.01 s | None | Text and logo remain legible, but the square composition leaves a large unused lower region; no target-aware vertical reflow occurs. |
| Level 2 core | 1080×1080 → 1600×400 | 11 | <0.01 s | `deco_circle_1` remains outside the canvas, consistent with the sample's intentionally bleeding decoration. | Independent x/y scaling distorts the product and logo, compresses vertical hierarchy, and leaves the headline, subhead, and CTA crowded into the lower strip. |
| Level 3 advanced | 1080×1350 → 728×90 | 17 | <0.01 s | None | All elements are crushed to the same tiny vertical scale; the long headline, supporting copy, badges, CTA, legal text, logo, and product do not form a readable banner. The missing asset is tolerated by the renderer as a placeholder. |

The full process took about 18 seconds on this Windows host, including imports and rendering; the runner's reported resize-only timings were below its 0.01-second display precision. The Level 2 warning is expected for a deliberately corner-bleeding element, not evidence of a new collision. `engine.main` does not currently surface renderer warnings to its console.

## Renderer and supplied assets

The official samples rendered with the supplied local fonts and assets. Asset dimensions observed:

- `solstice_bg_gradient.png`: 1200×1500 RGB
- `solstice_bottle.png`: 800×800 RGBA
- `solstice_logo_lockup.png`: 900×300 RGBA

The advanced sample intentionally references a missing holiday badge; the renderer emits a placeholder rather than crashing. This placeholder is renderer behavior and is not a generated replacement asset.

## Baseline artifacts

The six untouched outputs in `evidence/baseline/` are the source of truth for baseline comparisons. Do not overwrite them when producing later runs. The baseline demonstrates that passing the starter self-check does not imply visually valid recomposition: it checks element IDs, required fields, and axis-aligned bounds, but does not detect image distortion, text clipping, collisions, or poor composition.

## Environment follow-up

The initial Docker check on 2026-10-15 could not connect to `npipe:////./pipe/dockerDesktopLinuxEngine`. Docker Desktop's local diagnostic (ID `316C4AAB-61F2-4485-ADD1-0108FC3B3194`; not uploaded) reported that backend startup failed while removing `%LOCALAPPDATA%\Docker\run\dockerInference`: “The file cannot be accessed by the system.” After that socket was cleared, startup exposed a second orphaned socket at `%LOCALAPPDATA%\docker-secrets-engine\engine.sock`. Both parents contained only runtime sockets marked as reparse points; direct deletion returned Windows error 1920. Renaming the two runtime directories aside let Docker Desktop recreate them. Docker engine 29.5.3 then answered `docker info`, ran `hello-world`, and built and ran the challenge image offline. See [`evidence/docker/validation.md`](../evidence/docker/validation.md) for the full validation. Node 22.17.1 and npm 10.9.2 are present for the finale prototype. The `py` launcher is not installed; use `python` or `.venv\Scripts\python.exe`.
