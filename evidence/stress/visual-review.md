# Visual review of representative synthetic stress cases

These are generated schema-shaped fixtures. They help inspect renderer output
and inherited overlaps, but they are not professional designs, Adobe test cases,
or evidence of hidden-set quality.

## `synthetic_049` — slowest measured case, 45 elements

The 1200×628 source already contains many overlapping supporting lines, badges,
and decorative shapes. Its same-size output retains that source composition and
clutter. This is a stress/runtime sample, not a visual-quality win. The benchmark
reports no new or worsened collisions relative to the input.

## `synthetic_005` — 45 elements, landscape to portrait

The 1200×628 source already contains repeated overlapping copy and badges, with
decorative shapes competing for attention. The 1080×1350 output reorganizes
content into a vertical composition and a separate badge/action area while
retaining the same content. Inherited clutter remains; the source-relative
collision result does not claim absolute legibility.

## `synthetic_001` — narrow portrait target

The source is a sparse promotional poster with a stray supporting-copy element
near the upper left. The 300×600 output establishes a readable headline, centered
product, supporting copy, and prominent CTA in a coherent vertical stack. The
stray source copy remains, so this is a positive layout example rather than a
fully polished design.

The source and output PNGs for all selected cases are adjacent to this file.
`manifest.json` records their current selection and measured runtime. The
complete benchmark remains in `../benchmark/report.json`; collision counts are
source-relative and are defined there.
