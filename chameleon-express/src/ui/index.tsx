import React from "react";
import { createRoot } from "react-dom/client";
import App from "./components/App";

const root = createRoot(document.getElementById("root")!);

async function boot() {
    // The same UI runs as an honest, engine-backed browser demo and as an Express add-on.
    // Only the embedded Express panel loads the Adobe SDK and document sandbox proxy.
    if (window.parent === window) {
        root.render(<App />);
        return;
    }
    try {
        const { default: addOnUISdk, RuntimeType } = await import("https://new.express.adobe.com/static/add-on-sdk/sdk.js");
        await addOnUISdk.ready;
        const sandboxProxy = await addOnUISdk.instance.runtime.apiProxy(RuntimeType.documentSandbox) as unknown as import("../models/DocumentSandboxApi").DocumentSandboxApi;
        root.render(<App addOnUISdk={addOnUISdk} sandboxProxy={sandboxProxy} />);
    } catch (error) {
        console.error("Adobe Express initialization failed.", error);
        root.render(<App sdkError="Adobe Express initialization failed." />);
    }
}

void boot();
