# Independent synthetic visual evaluation

`source.json` is a hand-composed, synthetic Solstice campaign using only the
provided local background, bottle, and logo assets. It is not an Adobe challenge
sample. Its nine elements have a clear headline, supporting copy, product,
badge, and grouped call to action, so the fixture can help distinguish layout
quality from the inherited clutter in the randomized stress corpus.

Four target sizes exercise a nearby portrait, a landscape, a 728×90 ultra-wide
banner, and a narrow story. `tools/evaluate_curated_fixture.py` writes the engine
outputs, renderer PNGs, and per-format diagnostics beside this README. Inspect
the renders before drawing conclusions: a low collision count alone is not a
human readability score.

The report also checks preservation of element IDs/count, text, font families,
image asset IDs, and byte-stable JSON across a repeated resize call.

Rebuild from the repository root with:

```powershell
.\.venv\Scripts\python.exe -m tools.evaluate_curated_fixture
```

The fixture is a small qualitative check, not a statistical generalization
claim or substitute for the official hidden evaluator.

See [`visual-review.md`](visual-review.md) for measured and visual findings.
The separate [`sidecar`](sidecar/README.md) fixture adds an independently
composed side-by-side source and five target formats, including leaderboard
and medium-rectangle canvases. Reuse the same evaluator with `--fixture` and
`--output-dir` to reproduce it.
