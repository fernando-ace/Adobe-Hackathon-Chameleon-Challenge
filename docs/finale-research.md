# Adobe Express finale research

Research checked against Adobe's official developer documentation on 2026-10-15. This document is the requested top-level research record for the finale. The implementation map and detailed API findings are also kept in [`docs/finale/express-api-research.md`](finale/express-api-research.md).

## Platform model

An Adobe Express add-on has two relevant execution contexts:

- The **panel UI** runs in an iframe and uses the Add-on UI SDK for document metadata, import/export, rendition previews, theme, and other host integrations.
- The **Document Sandbox** runs document-editing code separately. Document APIs such as selection, pages, and scenegraph authoring belong there. The SDK's communication/proxy APIs bridge the panel and sandbox; browser APIs should stay in the iframe and be exposed to the sandbox only when needed.

This split is a good fit for Chameleon: the panel can call the local Python engine and present candidate previews, while the sandbox creates editable Express objects. It does not make arbitrary source-page extraction automatic; that requires a separate, supported read path and compatibility handling.

Official references: [platform architecture](https://developer.adobe.com/express/add-ons/docs/guides/learn/platform-concepts/architecture), [Document Sandbox](https://developer.adobe.com/express/add-ons/docs/references/document-sandbox/), [communication APIs](https://developer.adobe.com/express/add-ons/docs/references/document-sandbox/communication/), and [Add-on UI SDK](https://developer.adobe.com/express/add-ons/docs/references/addonsdk/).

## Capabilities relevant to Chameleon

| Capability | Adobe API surface | Product use and current boundary |
|---|---|---|
| Read user selection | `editor.context.selection`, selection events in the Document Sandbox | Adobe supports reading and updating selected editable nodes. Selection-change callbacks should update panel state, not mutate the document. The current prototype's lock is a Chameleon placement constraint for local regeneration; it does not yet follow native Express selection. |
| Read and author document content | Document APIs (`editor`, pages, nodes, editor operations) in the Document Sandbox | The prototype adds an adapted page and keeps text, shapes, and images as separate objects. The current source picker is restricted to the three challenge JSON inputs; it does not inspect arbitrary open pages. |
| Show document previews | `addOnUISdk.app.document.createRenditions()` in the panel | Adobe supports preview renditions with `RenditionIntent.preview`; the manifest must enable `renditionPreview`. Chameleon's present previews come from its local renderer and engine, not from rendering the active Express document. |
| Build a native-feeling panel | Spectrum Web Components, with the Express theme; React wrappers are available | Adobe recommends Spectrum components for consistent, accessible controls. The current React panel uses the Spectrum React Button and Theme components, while most of its layout and remaining controls are custom; it still needs a focused Spectrum/accessibility pass before a public release. |
| Load local code | Adobe Express add-on CLI, HTTPS development server, Add-on Development mode | The CLI's `start` server and `adobe.com/go/addon-cli` entry point support sideloading. First use may require accepting Developer Terms and enabling Add-on Development. Chrome 142+ may separately ask for local-network access when Express connects to `https://localhost`; that browser permission is distinct from remote-debugging access. |
| Package and distribute | CLI packaging plus Adobe's publisher/review workflow | A local prototype package is not a published add-on. Public sharing requires Adobe's review process and listing requirements; this task has not requested submission or publication. |

Official references: [selection handling](https://developer.adobe.com/express/add-ons/docs/guides/learn/how-to/handle-selection), [Document APIs](https://developer.adobe.com/express/add-ons/docs/references/document-sandbox/document-apis/), [create renditions](https://developer.adobe.com/express/add-ons/docs/guides/learn/how-to/create-renditions), [Spectrum implementation guide](https://developer.adobe.com/express/add-ons/docs/guides/build/design/implementation-guide), [local development and sideloading](https://developer.adobe.com/express/add-ons/docs/guides/getting-started/local-development/dev-tooling), [Chrome local-network limitation](https://developer.adobe.com/express/add-ons/docs/guides/getting-started/local-development/known-issues-limitations), and [distribution review](https://developer.adobe.com/express/add-ons/docs/guides/build/distribute/).

## Prototype mapping

- `chameleon-express/src/ui/` contains the React panel, preset selection, six-format previews, generation, and placement-lock controls.
- `chameleon-express/server.py` calls the real local Stage 1 engine; the add-on does not substitute a browser-only resize mock.
- `chameleon-express/src/sandbox/code.ts` uses the Document Sandbox to append the chosen layout as a new page, creating editable text, shape, and image elements.
- The engine source picker is intentionally limited to the supplied structured challenge samples. It does not yet analyze an arbitrary selected Express design.
- Image pixels are imported as per-element assets; the whole design is not flattened into one page image. Express font availability and styling differences mean Stage 1's exact font-family preservation is not claimed for finale documents.

## Validation and current status

Previously recorded local evidence: the add-on production build passed; the local API served all three sources and six presets; browser testing of the local prototype generated six Level 3 formats and verified that a locked headline retained its rectangle. `npm run package` also succeeded and produced the ZIP at [`evidence/finale/chameleon-express-add-on.zip`](../evidence/finale/chameleon-express-add-on.zip); its CRC and manifest were inspected, and it contains no local development certificates. The build reports a 628 KiB panel bundle, above webpack's 244 KiB advisory limit. The precise local results and limits are in [`docs/finale/express-api-research.md`](finale/express-api-research.md).

The Adobe-hosted test remains **unverified**. The account owner reports accepting Adobe Developer Terms and acknowledging the external-server warning. On 2026-10-18, the account owner shared a cropped Chrome setting showing `Local network: Allow`, but the site origin was not visible. Reloading Express allowed its blank editor and Add-ons panel to initialize. We re-enabled Add-on testing and retried Connect with the Node add-on server and Python API running; Adobe continued to report “The development environment provided failed to load. Please check the PORT number and try again.” The actual add-on entry HTML and manifest returned HTTP 200 at the expected port, and the API catalog returned HTTP 200 on its separate port. This confirms local host reachability, not Adobe-hosted loading. The exact origin for the Chrome permission is unknown. Therefore no add-on installation, format generation inside Express, or Apply operation is claimed as complete.

The remaining gate is a successful Express connection to the running local server. After that, exercise generation, preview, lock/regeneration, Apply, and the resulting editable page in the actual document.

## Sources

All API and workflow claims above are based on the linked Adobe Developer documentation, checked on 2026-10-15. The prototype's local tests are not Adobe-hosted validation, Adobe scoring, or evidence of successful publication.
