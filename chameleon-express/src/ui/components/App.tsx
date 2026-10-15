import "@spectrum-web-components/theme/express/scale-medium.js";
import "@spectrum-web-components/theme/express/theme-light.js";
import { Button } from "@swc-react/button";
import { Theme } from "@swc-react/theme";
import React, { useEffect, useMemo, useState } from "react";
import { AddOnSDKAPI } from "https://new.express.adobe.com/static/add-on-sdk/sdk.js";
import { DocumentSandboxApi } from "../../models/DocumentSandboxApi";
import "./App.css";

const API = "https://localhost:18765";

type Format = { id: string; name: string; detail: string; width: number; height: number };
type Sample = { id: string; name: string; canvas: { width: number; height: number }; element_count: number };
type Element = Record<string, unknown> & { id: string; type: string; x: number; y: number; width: number; height: number; content?: string; asset_id?: string };
type Layout = { format: Format; design: { canvas: { width: number; height: number }; elements: Element[] }; preview: string; elementAssets: Record<string, string>; family: string; placements: Array<{ id: string; role: string; reason: string }> };
type Generation = { layouts: Layout[]; source: { canvas: { width: number; height: number }; elements: Element[] } };
type Props = { addOnUISdk?: AddOnSDKAPI; sandboxProxy?: DocumentSandboxApi; sdkError?: string };

const FALLBACK_FORMATS: Format[] = [
    { id: "poster", name: "Portrait poster", detail: "1080 × 1350 px · 4:5", width: 1080, height: 1350 },
    { id: "square", name: "Square social", detail: "1080 × 1080 px · Social", width: 1080, height: 1080 },
    { id: "story", name: "Story", detail: "1080 × 1920 px · Mobile", width: 1080, height: 1920 },
    { id: "landscape", name: "Landscape", detail: "1200 × 628 px · Social", width: 1200, height: 628 },
    { id: "event", name: "Event header", detail: "1920 × 1080 px · Event", width: 1920, height: 1080 },
    { id: "banner", name: "Wide banner", detail: "3000 × 600 px · Web", width: 3000, height: 600 },
];

const imageUrl = (base64: string) => `data:image/png;base64,${base64}`;
const shortSize = (format: Format) => `${format.width} × ${format.height}`;

const App = ({ addOnUISdk, sandboxProxy, sdkError }: Props) => {
    const [samples, setSamples] = useState<Sample[]>([]);
    const [formats, setFormats] = useState<Format[]>(FALLBACK_FORMATS);
    const [sampleId, setSampleId] = useState("chameleon_sample_level3_advanced");
    const [selectedIds, setSelectedIds] = useState<string[]>(FALLBACK_FORMATS.map((format) => format.id));
    const [generation, setGeneration] = useState<Generation | null>(null);
    const [sourcePreview, setSourcePreview] = useState("");
    const [activeId, setActiveId] = useState("banner");
    const [lockId, setLockId] = useState("");
    const [locked, setLocked] = useState(false);
    const [lockedRects, setLockedRects] = useState<Record<string, Record<string, { x: number; y: number; width: number; height: number }>>>({});
    const [compare, setCompare] = useState(58);
    const [loading, setLoading] = useState(false);
    const [applying, setApplying] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");

    const active = generation?.layouts.find((layout) => layout.format.id === activeId) ?? generation?.layouts[0];
    const selectedSample = samples.find((sample) => sample.id === sampleId);
    const isExpress = Boolean(addOnUISdk && sandboxProxy);
    const elementOptions = useMemo(() => generation?.source.elements.filter((element) => element.type === "text" || element.id === "logo") ?? [], [generation]);
    const selectedElement = elementOptions.find((element) => element.id === lockId) ?? elementOptions.find((element) => element.id === "headline") ?? elementOptions[0];
    const selectedCount = selectedIds.length;

    useEffect(() => {
        let disposed = false;
        fetch(`${API}/api/catalog`).then((response) => response.json()).then((data) => {
            if (disposed) return;
            setSamples(data.samples ?? []);
            setFormats(data.formats ?? FALLBACK_FORMATS);
            setSelectedIds((data.formats ?? FALLBACK_FORMATS).map((format: Format) => format.id));
        }).catch(() => setError("The local Chameleon engine is unavailable. Start the prototype service and try again."));
        return () => { disposed = true; };
    }, []);

    useEffect(() => {
        if (!sampleId) return;
        let disposed = false;
        setSourcePreview("");
        fetch(`${API}/api/source-preview?id=${encodeURIComponent(sampleId)}`).then((response) => response.json()).then((data) => {
            if (!disposed && data.preview) setSourcePreview(imageUrl(data.preview));
        }).catch(() => { if (!disposed) setSourcePreview(""); });
        return () => { disposed = true; };
    }, [sampleId]);

    useEffect(() => {
        if (!generation || !elementOptions.length) return;
        if (!lockId) setLockId(elementOptions.find((element) => element.id === "headline")?.id ?? elementOptions[0].id);
    }, [generation, elementOptions, lockId]);

    async function generate() {
        if (!selectedCount) { setError("Choose at least one canvas format."); return; }
        setLoading(true); setError(""); setNotice("");
        try {
            const response = await fetch(`${API}/api/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    sample_id: sampleId,
                    format_ids: selectedIds,
                    locked_ids: locked ? [selectedElement?.id].filter(Boolean) : [],
                    locked_rects: lockedRects,
                }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error ?? "Chameleon could not generate these formats.");
            setGeneration(data);
            setActiveId((current) => data.layouts.some((layout: Layout) => layout.format.id === current) ? current : data.layouts[data.layouts.length - 1].format.id);
            if (locked && selectedElement) {
                const next = { ...lockedRects };
                for (const layout of data.layouts as Layout[]) {
                    const element = layout.design.elements.find((item) => item.id === selectedElement.id);
                    if (element) next[layout.format.id] = { ...next[layout.format.id], [element.id]: { x: element.x, y: element.y, width: element.width, height: element.height } };
                }
                setLockedRects(next);
            }
            setNotice(`${data.layouts.length} format${data.layouts.length === 1 ? "" : "s"} generated with the Chameleon engine.`);
        } catch (caught) {
            setError(caught instanceof Error ? caught.message : "Generation failed. Please try again.");
        } finally { setLoading(false); }
    }

    async function applyToDocument() {
        if (!active || !sandboxProxy) return;
        setApplying(true); setError(""); setNotice("");
        try {
            const message = await sandboxProxy.applyLayout({ layout: active.design, elementAssets: active.elementAssets ?? {}, title: active.format.name });
            setNotice(message || `${active.format.name} was added as an editable page.`);
        } catch (caught) {
            setError(caught instanceof Error ? caught.message : "Adobe Express could not apply this layout.");
        } finally { setApplying(false); }
    }

    function toggleFormat(id: string) {
        setSelectedIds((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id]);
        setGeneration(null);
        setNotice("");
    }

    function selectLayout(id: string) { setActiveId(id); setNotice(""); }

    return (
        <Theme system="express" scale="medium" color="light">
            <div className="app-shell">
                <header className="topbar">
                    <a className="brand" href="#" aria-label="Chameleon home"><span className="brand-mark">C</span><span>Chameleon</span></a>
                    <span className="topbar-divider" />
                    <span className="topbar-context">Campaign studio</span>
                    <div className="topbar-spacer" />
                    <span className={`connection ${isExpress ? "is-connected" : ""}`}><i />{isExpress ? "Connected to Adobe Express" : "Preview mode"}</span>
                    <button className="quiet-button" type="button" aria-label="Help" title="Chameleon preserves source content and uses the bundled deterministic layout engine.">?</button>
                </header>

                <main className="workbench">
                    <section className="canvas-area" aria-label="Campaign preview">
                        <div className="canvas-heading">
                            <div>
                                <p className="eyebrow">CAMPAIGN FAMILY</p>
                                <h1>{selectedSample?.name ?? "Solstice campaign"}</h1>
                            </div>
                            <div className="canvas-status"><span className="status-dot" />{generation ? `${generation.layouts.length} formats ready` : "Ready to adapt"}</div>
                        </div>

                        <div className="comparison-board">
                            <div className="preview-column source-column">
                                <div className="preview-label"><span>Source design</span><small>{selectedSample ? `${selectedSample.canvas.width} × ${selectedSample.canvas.height}` : "Original canvas"}</small></div>
                                <div className="artboard source-artboard">
                                    {sourcePreview ? <img src={sourcePreview} alt="Original campaign design" /> : <div className="preview-placeholder"><span className="spinner" />Loading source</div>}
                                </div>
                            </div>
                            <div className="compare-connector" aria-hidden="true"><span>→</span></div>
                            <div className="preview-column result-column">
                                <div className="preview-label"><span>{active?.format.name ?? "Adapted preview"}</span><small>{active ? shortSize(active.format) : "Choose a format to begin"}</small></div>
                                <div className="artboard result-artboard" style={{ aspectRatio: active ? `${active.format.width} / ${active.format.height}` : "1.2 / 1" }}>
                                    {active ? <>
                                        <img className="result-image" src={imageUrl(active.preview)} alt={`${active.format.name} generated layout`} />
                                        <img className="compare-image" src={sourcePreview} alt="Original design comparison" style={{ clipPath: `inset(0 ${100 - compare}% 0 0)` }} />
                                        <div className="compare-divider" style={{ left: `${compare}%` }} aria-hidden="true" />
                                    </> : <div className="preview-placeholder"><span className="empty-spark">✳</span><p>Your campaign family will appear here.</p></div>}
                                </div>
                                {active && <label className="compare-control"><span>Before</span><input type="range" min="0" max="100" value={compare} onChange={(event) => setCompare(Number(event.target.value))} aria-label="Before and after comparison"/><span>After</span></label>}
                            </div>
                        </div>

                        <div className="family-header"><div><h2>Format family</h2><p>{generation ? "Each canvas rebuilt around the same campaign story." : "Select a format to create a coordinated campaign set."}</p></div><span className="family-count">{generation ? `${generation.layouts.length} previews` : "No previews yet"}</span></div>
                        <div className="preview-strip">
                            {generation?.layouts.map((layout) => <button className={`format-preview ${active?.format.id === layout.format.id ? "is-active" : ""}`} key={layout.format.id} onClick={() => selectLayout(layout.format.id)} type="button" aria-pressed={active?.format.id === layout.format.id}>
                                <span className={`thumbnail-frame ratio-${layout.format.id}`}><img src={imageUrl(layout.preview)} alt="" /></span>
                                <span className="thumbnail-caption"><strong>{layout.format.name}</strong><small>{shortSize(layout.format)}</small></span>
                            </button>)}
                            {!generation && <div className="family-empty"><span className="empty-spark">✳</span><span>Six formats, one consistent campaign.</span></div>}
                        </div>
                        <div className="canvas-footer"><span>Content and font families come from the selected source design.</span><span className="deterministic-label"><i />Deterministic layout engine</span></div>
                    </section>

                    <aside className="side-panel" aria-label="Chameleon controls">
                        <div className="panel-title"><div><p className="panel-eyebrow">DESIGN ADAPTATION</p><h2>Chameleon</h2></div><span className="panel-icon">✳</span></div>
                        <p className="panel-lede">One campaign. Every canvas.</p>
                        <p className="panel-description">Recompose your design for every format while keeping its story and visual identity intact.</p>

                        <div className="source-card">
                            <div className="source-thumb">{sourcePreview && <img src={sourcePreview} alt="" />}</div>
                            <label className="source-select"><span>Source campaign</span><select value={sampleId} onChange={(event) => { setSampleId(event.target.value); setGeneration(null); setLockedRects({}); setLocked(false); setNotice(""); }}>{samples.map((sample) => <option key={sample.id} value={sample.id}>{sample.name}</option>)}</select><small>{selectedSample?.element_count ?? "—"} elements · Provided challenge design</small></label>
                        </div>

                        <section className="format-section">
                            <div className="section-heading"><h3>Choose formats</h3><span>{selectedCount} selected</span></div>
                            <div className="format-list">
                                {formats.map((format) => <label className={`format-row ${selectedIds.includes(format.id) ? "checked" : ""}`} key={format.id}>
                                    <input type="checkbox" checked={selectedIds.includes(format.id)} onChange={() => toggleFormat(format.id)} />
                                    <span className={`format-glyph glyph-${format.id}`} aria-hidden="true"><i /></span>
                                    <span className="format-copy"><strong>{format.name}</strong><small>{format.detail}</small></span>
                                </label>)}
                            </div>
                            <Button className="generate-button" size="m" onClick={generate} disabled={loading || !selectedCount}>
                                {loading ? <><span className="button-spinner" />Composing {selectedCount} formats</> : <>{generation ? "Regenerate campaign" : `Generate ${selectedCount} formats`}<span aria-hidden="true">→</span></>}
                            </Button>
                            {error && <div className="message error-message" role="alert">{error}</div>}
                            {notice && <div className="message success-message" role="status">{notice}</div>}
                        </section>

                        {generation && active && <section className="results-section">
                            <div className="section-heading"><h3>Campaign previews</h3><span>{generation.layouts.length} ready</span></div>
                            <div className="results-grid">{generation.layouts.slice(0, 3).map((layout) => <button type="button" className={`result-card ${active.format.id === layout.format.id ? "is-active" : ""}`} key={layout.format.id} onClick={() => selectLayout(layout.format.id)} aria-pressed={active.format.id === layout.format.id}>
                                <span className="result-thumb"><img src={imageUrl(layout.preview)} alt="" /></span><strong>{layout.format.name}</strong><small>{shortSize(layout.format)}</small>
                            </button>)}</div>
                            <button className="view-all" type="button" onClick={() => document.querySelector(".preview-strip")?.scrollIntoView({ behavior: "smooth", block: "nearest" })}>View all {generation.layouts.length} formats <span>↓</span></button>
                            <div className="rationale"><span className="rationale-icon">✳</span><div><strong>Layout rationale</strong><p>{active.family.split("_").join(" ")} layout · {active.placements.find((placement) => placement.role === "hero_image")?.reason ?? "Preserved the campaign's key visual relationships."}</p></div></div>
                        </section>}

                        <section className="steering-section">
                            <div className="section-heading"><h3>Keep an element fixed</h3><span>Optional</span></div>
                            <label className="lock-select-label">Element<select value={selectedElement?.id ?? ""} onChange={(event) => { setLockId(event.target.value); setLockedRects({}); setLocked(false); }} disabled={!generation || !elementOptions.length}><option value="" disabled>Select element</option>{elementOptions.map((element) => <option key={element.id} value={element.id}>{element.content ? String(element.content).slice(0, 32) : element.id}</option>)}</select></label>
                            <button className={`lock-row ${locked ? "is-locked" : ""}`} type="button" onClick={() => {
                                if (!generation || !selectedElement) return;
                                if (locked) { setLocked(false); setNotice("Element unlocked. Regenerate to let Chameleon recompose it."); return; }
                                const snapshot: typeof lockedRects = {};
                                for (const layout of generation.layouts) {
                                    const element = layout.design.elements.find((item) => item.id === selectedElement.id);
                                    if (element) snapshot[layout.format.id] = { [element.id]: { x: element.x, y: element.y, width: element.width, height: element.height } };
                                }
                                setLockedRects(snapshot); setLocked(true); setNotice("Regenerate to keep this element's placement fixed for each selected format.");
                            }} disabled={!generation || !selectedElement} aria-pressed={locked}>
                                <span className="switch"><i /></span><span><strong>{locked ? "Element locked" : "Lock selected element"}</strong><small>{locked ? "Its current position will be held on regeneration." : "Keep this element in place when regenerating."}</small></span><span className="lock-glyph" aria-hidden="true">⌑</span>
                            </button>
                        </section>

                        <div className="panel-bottom">
                            {!isExpress && <p className="integration-note">{sdkError ? "Express connection unavailable in this preview." : "Open in Adobe Express to add an editable campaign page."}</p>}
                            <Button className="apply-button" size="m" onClick={applyToDocument} disabled={!isExpress || !active || applying}>
                                {applying ? <><span className="button-spinner" />Adding page…</> : <>Apply selected format<span aria-hidden="true">↗</span></>}
                            </Button>
                            <small className="apply-footnote">Adds a new page with editable text, shapes, and imagery.</small>
                        </div>
                    </aside>
                </main>
            </div>
        </Theme>
    );
};

export default App;
