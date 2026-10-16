"""Local HTTP integration checks for the Adobe Express prototype API."""

from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from http.server import ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "chameleon-express" / "server.py"
SPEC = importlib.util.spec_from_file_location("chameleon_prototype_server", SERVER_PATH)
assert SPEC is not None and SPEC.loader is not None
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class FinaleApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)

    def _get_json(self, route: str) -> dict:
        with urlopen(f"{self.base_url}{route}", timeout=30) as response:
            self.assertEqual(response.status, 200)
            return json.load(response)

    def _post_json(self, route: str, payload: dict) -> dict:
        request = Request(
            f"{self.base_url}{route}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=120) as response:
            self.assertEqual(response.status, 200)
            return json.load(response)

    def test_campaign_generation_previews_assets_and_locking(self) -> None:
        catalog = self._get_json("/api/catalog")
        self.assertEqual(len(catalog["samples"]), 3)
        formats = [item["id"] for item in catalog["formats"]]
        self.assertEqual(len(formats), 6)
        source_preview = self._get_json(
            "/api/source-preview?id=chameleon_sample_level3_advanced"
        )
        self.assertEqual(
            base64.b64decode(source_preview["preview"][:32])[:8],
            b"\x89PNG\r\n\x1a\n",
        )

        server.LOCKED_RECTS.clear()
        payload = {
            "sample_id": "chameleon_sample_level3_advanced",
            "format_ids": formats,
            "locked_ids": [],
            "locked_rects": {},
        }
        generated = self._post_json("/api/generate", payload)
        self.assertEqual(len(generated["layouts"]), 6)
        self.assertEqual(len(generated["source"]["elements"]), 17)

        for layout in generated["layouts"]:
            with self.subTest(format=layout["format"]["id"]):
                self.assertEqual(len(layout["design"]["elements"]), 17)
                self.assertTrue(layout["placements"] or layout["family"] == "identity")
                self.assertEqual(
                    base64.b64decode(layout["preview"][:32])[:8],
                    b"\x89PNG\r\n\x1a\n",
                )
                self.assertTrue(layout["elementAssets"])

        banner = next(item for item in generated["layouts"] if item["format"]["id"] == "banner")
        headline = next(item for item in banner["design"]["elements"] if item["id"] == "headline")
        rect = {key: headline[key] for key in ("x", "y", "width", "height")}
        locked = self._post_json("/api/generate", {
            "sample_id": payload["sample_id"],
            "format_ids": ["banner"],
            "locked_ids": ["headline"],
            "locked_rects": {"banner": {"headline": rect}},
        })
        locked_headline = next(
            item for item in locked["layouts"][0]["design"]["elements"]
            if item["id"] == "headline"
        )
        self.assertEqual(
            {key: locked_headline[key] for key in rect}, rect,
        )

    def test_unknown_source_returns_a_clear_client_error(self) -> None:
        request = Request(
            f"{self.base_url}/api/generate",
            data=json.dumps({"sample_id": "not-a-source", "format_ids": ["banner"]}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=30)
        self.assertEqual(caught.exception.code, 400)
        self.assertIn("provided source designs", caught.exception.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
