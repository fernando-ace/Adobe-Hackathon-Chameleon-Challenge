# Solstice Sidecar Product Campaign

This is a hand-composed synthetic 1200×1200 design with left-aligned copy, a
right-side product image, two informational badges, a brand mark, and a grouped
CTA. It reuses the challenge's supplied background, logo, and product image;
none of the source pixels are altered.

It probes five target shapes, including a 728×90 leaderboard, a 300×600 story,
and a 300×250 medium rectangle. This is independent synthetic evidence, not an
official Chameleon input or proof of hidden-set generalization.

Reproduce the outputs from the repository root:

```powershell
.\.venv\Scripts\python.exe -m tools.evaluate_curated_fixture `
  --fixture evidence/curated/sidecar/source.json `
  --output-dir evidence/curated/sidecar
```

The `report.json` records identity, text, font, asset, determinism, structural,
clipping, image-ratio, collision, and internal-proxy checks. Inspect every PNG;
the proxy is not a substitute for human visual review.
