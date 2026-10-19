import addOnSandboxSdk from "add-on-sdk-document-sandbox";
import { constants, editor, fonts } from "express-document-sdk";
import { ApplyLayoutPayload, DocumentSandboxApi, LayoutElement } from "../models/DocumentSandboxApi";

const { runtime } = addOnSandboxSdk.instance;

function decodePng(base64: string): Blob {
    const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    const clean = base64.replace(/[^A-Za-z0-9+/=]/g, "");
    const bytes = new Uint8Array(Math.floor(clean.length * 3 / 4) - (clean.endsWith("==") ? 2 : clean.endsWith("=") ? 1 : 0));
    let output = 0;
    for (let index = 0; index < clean.length;) {
        const a = alphabet.indexOf(clean[index++]);
        const b = alphabet.indexOf(clean[index++]);
        const c = alphabet.indexOf(clean[index++]);
        const d = alphabet.indexOf(clean[index++]);
        bytes[output++] = (a << 2) | (b >> 4);
        if (c >= 0 && output < bytes.length) bytes[output++] = ((b & 15) << 4) | (c >> 2);
        if (d >= 0 && output < bytes.length) bytes[output++] = ((c & 3) << 6) | d;
    }
    return new Blob([bytes], { type: "image/png" });
}

function parseColor(value: unknown) {
    const match = String(value ?? "rgba(40,35,31,1)").match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)/i);
    if (!match) return { red: 0.16, green: 0.14, blue: 0.12, alpha: 1 };
    return { red: Number(match[1]) / 255, green: Number(match[2]) / 255, blue: Number(match[3]) / 255, alpha: match[4] === undefined ? 1 : Number(match[4]) };
}

function fontNames(element: LayoutElement): string[] {
    const family = String(element.font_family ?? "").toLowerCase();
    const bold = String(element.font_weight ?? "").toLowerCase().includes("bold");
    if (family.includes("serif")) return [bold ? "SourceSerif4-Bold" : "SourceSerif4-Regular", "AdobeCaslonPro-Regular", "SourceSans3-Regular"];
    return [bold ? "SourceSans3-Bold" : "SourceSans3-Regular", "SourceSansPro-Regular"];
}

function textAlignment(value: unknown): number {
    const alignments: Record<string, number> = { left: 1, right: 2, center: 3, justify: 4, justifyLeft: 4 };
    return alignments[String(value ?? "left")] ?? alignments.left;
}

async function findAvailableFont(element: LayoutElement) {
    for (const postscriptName of fontNames(element)) {
        const font = await fonts.fromPostscriptName(postscriptName);
        if (font) return font;
    }
    return undefined;
}

function setNodePosition(node: { setPositionInParent: (parent: { x: number; y: number }, local: { x: number; y: number }) => void; setRotationInParent?: (angle: number, point: { x: number; y: number }) => void; centerPointLocal?: { x: number; y: number }; topLeftLocal?: { x: number; y: number } }, element: LayoutElement) {
    node.setPositionInParent({ x: element.x, y: element.y }, node.topLeftLocal ?? { x: 0, y: 0 });
    if (element.rotation && node.setRotationInParent && node.centerPointLocal) node.setRotationInParent(element.rotation, node.centerPointLocal);
}

async function applyLayout(payload: ApplyLayoutPayload): Promise<string> {
    const { layout, elementAssets } = payload;
    if (!layout?.canvas?.width || !layout?.canvas?.height || !Array.isArray(layout.elements)) throw new Error("The selected layout is missing canvas geometry or elements.");

    const ordered = [...layout.elements].sort((left, right) => Number(left.z_index ?? 0) - Number(right.z_index ?? 0));
    const warnings: string[] = [];
    let appliedImageCount = 0;

    // These resource loaders are asynchronous document operations themselves,
    // so finish them before capturing any page or node references.
    // Start each mutating image-resource load before the first await. Express
    // rejects starting a document mutation after an unrelated async boundary.
    const imageLoads: Array<[string, Promise<Awaited<ReturnType<typeof editor.loadBitmapImage>>>]> = [];
    for (const element of ordered.filter((item) => item.type === "image")) {
        const data = elementAssets[element.id];
        if (!data) {
            warnings.push(`Skipped image “${element.id}”: image data was unavailable.`);
            continue;
        }
        imageLoads.push([element.id, editor.loadBitmapImage(decodePng(data))]);
    }
    const imageBitmaps: Array<[string, Awaited<ReturnType<typeof editor.loadBitmapImage>>]> = [];
    const imageResults = await Promise.allSettled(imageLoads.map(([, promise]) => promise));
    for (let index = 0; index < imageResults.length; index++) {
        const result = imageResults[index];
        if (result.status === "fulfilled") {
            imageBitmaps.push([imageLoads[index][0], result.value]);
        } else {
            const caught = result.reason;
            const detail = caught instanceof Error ? ` ${caught.message}` : "";
            warnings.push(`Skipped image “${imageLoads[index][0]}”: Adobe Express could not load this asset.${detail}`);
        }
    }

    const textElements = layout.elements.filter((element) => element.type === "text");
    const availableFonts: Array<[string, Awaited<ReturnType<typeof findAvailableFont>>]> = [];
    for (const element of textElements) availableFonts.push([element.id, await findAvailableFont(element)]);

    // No document or node work happens between capturing the active page and
    // entering the guarded callback. All edits happen synchronously there.
    const targetPage = editor.context.currentPage;
    await editor.keepContentActiveDuringAsync(targetPage, async () => ({ availableFonts, imageBitmaps }), ({ availableFonts, imageBitmaps }) => {
        const page = editor.documentRoot.pages.addPage({ width: layout.canvas.width, height: layout.canvas.height });
        const artboard = page.artboards.first;
        for (const element of ordered) {
            if (element.type === "image") {
                const bitmap = imageBitmaps.find(([id]) => id === element.id)?.[1];
                if (!bitmap) continue;
                const node = editor.createImageContainer(bitmap, { initialSize: { width: element.width, height: element.height } });
                setNodePosition(node, element);
                artboard.children.append(node);
                appliedImageCount++;
                continue;
            }

            if (element.type === "shape") {
                const shape = editor.createRectangle();
                shape.width = element.width;
                shape.height = element.height;
                shape.fill = editor.makeColorFill(parseColor(element.fill_color));
                setNodePosition(shape, element);
                artboard.children.append(shape);
                continue;
            }

            if (element.type === "text") {
                const text = editor.createText(String(element.content ?? ""));
                text.layout = { type: constants.TextLayout.autoHeight, width: element.width };
                text.textAlignment = textAlignment(element.text_align) as unknown as typeof text.textAlignment;
                const style = {
                    fontSize: Math.max(1, Number(element.font_size ?? 16) * 0.75),
                    color: parseColor(element.color),
                    ...(availableFonts.find(([id]) => id === element.id)?.[1] ? { font: availableFonts.find(([id]) => id === element.id)?.[1] } : {}),
                };
                text.fullContent.applyCharacterStyles(style, { start: 0, length: String(element.content ?? "").length });
                setNodePosition(text, element);
                artboard.children.append(text);
            }
        }
    });

    const textCount = ordered.filter((element) => element.type === "text").length;
    const shapeCount = ordered.filter((element) => element.type === "shape").length;
    const summary = `Added ${payload.title} as a new ${layout.canvas.width} × ${layout.canvas.height} page with ${textCount} text, ${shapeCount} shape, and ${appliedImageCount} image elements.`;
    return warnings.length ? `${summary} ${warnings.join(" ")}` : summary;
}

const sandboxApi: DocumentSandboxApi = { applyLayout };
runtime.exposeApi(sandboxApi);
