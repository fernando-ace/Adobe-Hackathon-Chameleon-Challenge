# Chameleon finale demo

**Target runtime:** Adobe Express add-on. The browser prototype is the fallback for showing the engine-backed generation flow when Express sideloading is unavailable.

## 45-second flow

1. Open the supplied Solstice campaign source (Level 3, 17 elements).
2. Keep the six presets selected: portrait 4:5, square, story, landscape, event header, and wide banner.
3. Select **Generate 6 formats**. Explain that each preview came from the same local deterministic engine used for Stage 1.
4. Choose the wide banner. Compare source and adaptation with the before/after control; point to the new horizontal reading order and unchanged copy/assets.
5. Choose the headline as the element to keep fixed. Regenerate and show that its rectangle is retained for the banner while other content can reflow.
6. Select **Apply selected format**. In Adobe Express, this adds a new page with separate text, shape, and image objects.

## Honest fallback

The current prototype selects from the three supplied challenge designs. It does not yet extract an arbitrary open Express page. If the Express host or local API is unavailable, do not imply that generation or application succeeded; show the locally rendered preview gallery and identify the missing host connection.

## Demo data

- Source: `input/chameleon_sample_level3_advanced.json`.
- Engine: `engine.resize.resize()`.
- Assets: `brand_kit/assets/`.
- Render previews: the bundled `renderer` integration.
- Product UI concept: [chameleon-express-concept.png](chameleon-express-concept.png).
