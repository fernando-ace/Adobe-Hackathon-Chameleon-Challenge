# Visual review of representative synthetic stress cases

These are visual inspections of generated synthetic fixtures. They are useful
for checking renderer output and inherited-overlap behavior, but they are not
professional designs, Adobe test cases, or evidence of hidden-set quality.

## `synthetic_001` — narrow portrait target

The source is a sparse promotional poster with a stray supporting-copy element
near the upper left. The 300×600 output establishes a readable headline, centered
product, supporting copy, and prominent CTA. It uses a coherent vertical stack.
The stray source copy remains, so this is a positive layout example rather than
a fully polished design.

## `synthetic_005` — 45 elements, landscape to portrait

The 1200×628 source already contains repeated overlapping copy and badges, with
decorative shapes competing for attention. The 1080×1350 output keeps that
clutter while reorganizing content into a vertical composition. The benchmark
reports no new/worsened overlap relative to the input, but the result is not
absolutely legible or judge-ready. The zero-regression collision metric must not
be read as a zero-overlap or readability claim.

## `synthetic_028` — 45 elements, square to tall story

The 1080×1080 source already has colliding supporting copy and badges and uses a
deliberately missing image asset that renders as a placeholder. The 2160×3840
output uses `source_fit` and retains the inherited clutter and placeholder. This
case demonstrates a limit of the present heuristic: source-relative safety
checks do not repair a badly composed source, and a high proxy score does not
guarantee good absolute visual quality. It should be treated as a diagnostic
limitation, not evidence that the source was a polished design.

The source and output PNGs for all three cases are adjacent to this file. The
complete benchmark counts remain in `../benchmark/report.json`; collision counts
are source-relative and are defined explicitly in that report.
