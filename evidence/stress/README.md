# Representative synthetic stress evidence

These fixtures are generated locally by `tools/stress_corpus.py` with fixed seed
20261014. They are synthetic schema-shaped inputs, not Adobe challenge designs,
human-authored brand work, or evidence of hidden-set generalization.

`manifest.json` records how each representative case was selected and its
source/target dimensions, element count, internal hard-validity checks,
determinism result, and runtime measured in the complete benchmark run. The
runtime is host-dependent. Each case includes its generated source and resized
JSON plus PNG renders of both.

The bundle includes the slowest measured case, the most element-dense case, and
the case with the narrowest target aspect ratio. The complete 64-case stress and
45-case mutation aggregates remain in `../benchmark/report.json` and
`../benchmark/report.md`.

Rebuild this bundle from the repository root with:

```powershell
.\.venv\Scripts\python.exe -m tools.export_stress_evidence
```

The reported quality checks are internal diagnostics, not Adobe's evaluator.
Visual findings and source-relative collision limits are documented in
`visual-review.md`.
