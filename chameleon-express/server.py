"""Local prototype API: runs the real Chameleon engine and renderer."""

from __future__ import annotations

import base64
import json
import ssl
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.main import render_to_png  # noqa: E402
from engine.resize import get_last_diagnostics, resize  # noqa: E402

INPUT_DIR = ROOT / "input"
ASSETS_DIR = ROOT / "brand_kit" / "assets"
FORMATS = [
    {"id": "poster", "name": "Portrait poster", "detail": "1080 × 1350 px · 4:5", "width": 1080, "height": 1350},
    {"id": "square", "name": "Square social", "detail": "1080 × 1080 px · Social", "width": 1080, "height": 1080},
    {"id": "story", "name": "Story", "detail": "1080 × 1920 px · Mobile", "width": 1080, "height": 1920},
    {"id": "landscape", "name": "Landscape", "detail": "1200 × 628 px · Social", "width": 1200, "height": 628},
    {"id": "event", "name": "Event header", "detail": "1920 × 1080 px · Event", "width": 1920, "height": 1080},
    {"id": "banner", "name": "Wide banner", "detail": "3000 × 600 px · Web", "width": 3000, "height": 600},
]
LOCKED_RECTS: dict[tuple[str, str, str], dict[str, float]] = {}


def _catalog() -> list[dict]:
    items = []
    for path in sorted(INPUT_DIR.glob("*.json")):
        task = json.loads(path.read_text(encoding="utf-8"))
        source = task["source"]
        items.append({
            "id": path.stem,
            "name": task.get("difficulty", path.stem).replace("_", " ").title(),
            "canvas": source["canvas"],
            "element_count": len(source.get("elements", [])),
            "source": source,
        })
    return items


CATALOG = _catalog()


def _png_data(design: dict) -> str:
    with tempfile.TemporaryDirectory(prefix="chameleon-preview-") as temp:
        path = Path(temp) / "preview.png"
        render_to_png(design, ASSETS_DIR, path)
        return base64.b64encode(path.read_bytes()).decode("ascii")


def _element_images(source: dict, output: dict) -> dict[str, str]:
    """Prepare exact-size, transparent PNG assets for editable Express objects."""
    original = {str(element.get("id")): element for element in source.get("elements", [])}
    prepared: dict[str, str] = {}
    for element in output.get("elements", []):
        if element.get("type") != "image":
            continue
        source_element = original.get(str(element.get("id")), {})
        asset_name = Path(str(source_element.get("asset_id", ""))).name
        source_path = (ASSETS_DIR / asset_name).resolve()
        if source_path.parent != ASSETS_DIR.resolve() or not source_path.is_file():
            continue
        width, height = max(1, round(float(element["width"]))), max(1, round(float(element["height"])))
        with Image.open(source_path) as asset:
            image = asset.convert("RGBA")
            if source_element.get("fit", "contain") == "cover":
                image = ImageOps.fit(image, (width, height), centering=(0.5, 0.5))
            else:
                fitted = ImageOps.contain(image, (width, height))
                image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                image.alpha_composite(fitted, ((width - fitted.width) // 2, (height - fitted.height) // 2))
            import io

            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            prepared[str(element["id"])] = base64.b64encode(buffer.getvalue()).decode("ascii")
    return prepared


class Handler(BaseHTTPRequestHandler):
    server_version = "ChameleonPrototype/0.1"

    def _headers(self, status: int, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "https://localhost:5241")
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._headers(204)

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/catalog":
            self._json({"samples": [{k: v for k, v in item.items() if k != "source"} for item in CATALOG], "formats": FORMATS})
            return
        if route == "/api/source-preview":
            sample_id = urlparse(self.path).query.split("=", 1)[-1]
            sample = next((item for item in CATALOG if item["id"] == sample_id), None)
            if not sample:
                self._json({"error": "Unknown source design."}, 404)
                return
            self._json({"preview": _png_data(sample["source"])})
            return
        self._json({"error": "Route not found."}, 404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/generate":
            self._json({"error": "Route not found."}, 404)
            return
        try:
            request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            sample = next((item for item in CATALOG if item["id"] == request.get("sample_id")), None)
            if not sample:
                self._json({"error": "Select one of the provided source designs."}, 400)
                return
            selected = {str(value) for value in request.get("format_ids", [])}
            formats = [fmt for fmt in FORMATS if fmt["id"] in selected]
            if not formats:
                self._json({"error": "Choose at least one format."}, 400)
                return
            lock_ids = {str(value) for value in request.get("locked_ids", [])}
            supplied_locks = request.get("locked_rects", {})
            layouts = []
            for fmt in formats:
                result = resize(sample["source"], {"width": fmt["width"], "height": fmt["height"]})
                for element in result["elements"]:
                    key = (sample["id"], fmt["id"], str(element.get("id", "")))
                    candidate_rect = supplied_locks.get(fmt["id"], {}).get(str(element.get("id", "")))
                    rect = candidate_rect or LOCKED_RECTS.get(key)
                    if rect and str(element.get("id", "")) in lock_ids:
                        if rect["x"] >= 0 and rect["y"] >= 0 and rect["x"] + rect["width"] <= fmt["width"] and rect["y"] + rect["height"] <= fmt["height"]:
                            element.update(rect)
                diagnostics = get_last_diagnostics()
                for element in result["elements"]:
                    if str(element.get("id", "")) in lock_ids:
                        key = (sample["id"], fmt["id"], str(element["id"]))
                        LOCKED_RECTS[key] = {k: float(element[k]) for k in ("x", "y", "width", "height")}
                placements = diagnostics.get("placements", [])
                layouts.append({
                    "format": fmt,
                    "design": result,
                    "preview": _png_data(result),
                    "elementAssets": _element_images(sample["source"], result),
                    "family": diagnostics.get("layout_family", "adaptive layout"),
                    "placements": placements,
                })
            self._json({"layouts": layouts, "source": sample["source"]})
        except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
            self._json({"error": f"Generation failed: {error}"}, 400)
        except Exception as error:  # Keep diagnostics in server logs, but return a useful UI state.
            self.log_error("Generation failed: %s", error)
            self._json({"error": "The layout engine could not complete this request. Try a smaller format set."}, 500)

    def _json(self, body: dict, status: int = 200) -> None:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self._headers(status)
        self.wfile.write(encoded)

    def log_error(self, message: str, *args: object) -> None:
        print(message % args, file=sys.stderr, flush=True)

    def log_message(self, message: str, *args: object) -> None:
        print(message % args, file=sys.stderr, flush=True)


def main() -> None:
    import os

    host = os.environ.get("CHAMELEON_HOST", "127.0.0.1")
    port = int(os.environ.get("CHAMELEON_PORT", "18765"))
    cert = Path(os.environ.get("CHAMELEON_CERT", "chameleon-express/.local-dev/localhost.crt"))
    key = Path(os.environ.get("CHAMELEON_KEY", "chameleon-express/.local-dev/localhost.key"))
    server = ThreadingHTTPServer((host, port), Handler)
    if cert.is_file() and key.is_file():
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=cert, keyfile=key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        print(f"Chameleon API ready at https://localhost:{port}", flush=True)
    else:
        print(f"Chameleon API ready at http://{host}:{port} (demo mode only)", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
