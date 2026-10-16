# Wide-source event campaign fixture

`source.json` is a hand-composed synthetic 1600×900 Solstice event campaign. It
uses only the challenge's bundled background, product, and logo assets. The
source has a left-side event headline and details, grouped badge and CTA, and a
right-side hero product. It is not an Adobe challenge sample.

Five targets exercise wide-to-square, wide-to-tall, wide-to-mobile, leaderboard,
and medium-rectangle adaptation. Reproduce the outputs from the repository root:

```powershell
.\.venv\Scripts\python.exe -m tools.evaluate_curated_fixture `
  --fixture evidence/curated/market/source.json `
  --output-dir evidence/curated/market
```

The evaluator checks content, IDs, image references, deterministic JSON,
geometry, clipping, image ratios, collisions, and the internal source-relative
proxy. The report and renderer-backed PNGs are adjacent. Read
[`visual-review.md`](visual-review.md) before interpreting the measurements.
The fixture broadens source-composition coverage; it is synthetic and does not
prove generalization to Adobe's hidden designs.
