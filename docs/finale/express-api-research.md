# Adobe Express add-on research

Research checked against Adobe's official developer documentation on 2026-10-15.

## Findings, hypotheses, and implementation

| Research finding | Product hypothesis | Implemented behavior | Evidence and limits |
|---|---|---|---|
| The Add-on UI SDK runs in the panel iframe. The Document API runs in a separate sandbox, and `runtime.apiProxy()` connects them. | Keep controls, preview, and network calls in the iframe; perform document edits in the sandbox. | `chameleon-express/src/ui` hosts the React panel and API calls. `src/sandbox/code.ts` exposes `applyLayout()` through the proxy. | Adobe [Add-on architecture](https://developer.adobe.com/express/add-ons/docs/guides/learn/platform-concepts/architecture) and [project anatomy](https://developer.adobe.com/express/add-ons/docs/guides/getting-started/addon-project-anatomy). Webpack build passes. No live Express document has been edited in this environment yet. |
| The UI SDK exposes document title, page metadata, image import, and rendition/export operations. The Document API exposes the active page scenegraph and can create pages and author elements. | Generate from a known structured source, then add the selected adaptation as a new page whose text, shapes, and images remain separate objects. | The prototype catalogs the three supplied challenge designs, runs the real Python engine, previews six output canvases, and uses `documentRoot.pages.addPage()` to apply one selected output as a new page. | Adobe [Add-on UI SDK reference](https://developer.adobe.com/express/add-ons/docs/references/addonsdk/) and [Document API reference](https://developer.adobe.com/express/add-ons/docs/references/document-sandbox/document-apis/). The prototype does not yet inspect arbitrary user-authored page elements as an input source. |
| The sandbox API supports `editor.createText`, shapes, image containers, page geometry, and asynchronous image loading with `keepContentActiveDuringAsync()`. | Create editable elements in z-order and avoid flattening a whole campaign preview into one image. | `applyLayout()` creates text nodes, filled rectangles, and image nodes on a new page. Image files are fitted to the generated element bounds and sent as per-element PNGs. | Adobe [Editor API](https://developer.adobe.com/express/add-ons/docs/references/document-sandbox/document-apis/classes/editor), [page management](https://developer.adobe.com/express/add-ons/docs/guides/learn/how-to/manage-pages), and [large document support](https://developer.adobe.com/express/add-ons/docs/guides/learn/platform-concepts/large-document-support). Live authoring remains unverified until the add-on is run inside Express. |
| Fonts are document resources and a font can only be applied when `fonts.fromPostscriptName()` returns an `AvailableFont`. | Preserve editable text and choose a licensed, available font with a compatible serif/sans category when an exact font cannot be resolved. | The apply path tries Source Serif 4 or Source Sans 3 names based on the source's family category, then leaves the Express default if none is available. | Adobe [Text API guide](https://developer.adobe.com/express/add-ons/docs/guides/learn/how-to/use-text). Exact Stage 1 font-family preservation is not claimed for the Express output. |
| Adobe's CLI provides React/TypeScript templates with Document Sandbox support and an HTTPS local development server. | Use the supported scaffold and local sideload path rather than inventing a host runtime. | Created with `@adobe/create-ccweb-add-on` using `react-typescript-with-document-sandbox`; configured with a local HTTPS certificate; `npm run build` and `npm run start` both succeed. | Adobe [CLI tooling and templates](https://developer.adobe.com/express/add-ons/docs/guides/getting-started/local-development/dev-tooling). The generator's automatic certificate path required OpenSSL, which was unavailable, so a local Windows certificate was created and manually configured. |

## Scope and known gaps

- The prototype's input picker is limited to the three supplied challenge JSON designs. It does not claim to parse arbitrary existing Express pages.
- The selected output is appended as a new page; the existing page is not replaced.
- Text and shapes are separate editable objects. Image content is fitted to the returned geometry and imported as separate image objects. Exact source font licensing, rounded-corner styling, and all renderer-specific effects are not guaranteed in the Express document.
- Element locking preserves the selected element's rectangle for each generated format on subsequent local regeneration. It is a Chameleon placement constraint, not an Adobe Express native lock-state integration.
- Browser access is waiting on Chrome's local remote-debugging consent. The app build and local API flow pass, but browser-level layout inspection and live Express apply are still pending.

## Prototype validation so far

- Adobe React/TypeScript add-on production build: passed.
- Local API served all three source designs and six target presets.
- The Level 3 design generated all six target previews using the current engine and renderer: 6 layouts, 102 returned elements, 6 fitted image assets, and 1,176,764 preview base64 characters.
- Regeneration with the headline locked retained its exact x/y/width/height for both the square and wide-banner formats (maximum coordinate delta 0).
- These are local prototype results, not Adobe-hosted or physical-device results.
