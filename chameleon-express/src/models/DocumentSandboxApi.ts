export type LayoutElement = {
    id: string;
    type: string;
    x: number;
    y: number;
    width: number;
    height: number;
    z_index?: number;
    rotation?: number;
    content?: string;
    font_family?: string;
    font_size?: number;
    font_weight?: string;
    text_align?: string;
    color?: string;
    fill_color?: string;
    shape_type?: string;
};

export type LayoutPayload = {
    canvas: { width: number; height: number };
    elements: LayoutElement[];
};

export type ApplyLayoutPayload = {
    layout: LayoutPayload;
    elementAssets: Record<string, string>;
    title: string;
};

// The panel calls this proxy through Adobe's document-sandbox bridge.
export interface DocumentSandboxApi {
    applyLayout(payload: ApplyLayoutPayload): Promise<string>;
}
