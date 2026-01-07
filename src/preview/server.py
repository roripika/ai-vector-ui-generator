"""Local preview server for JSON → SVG."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from src.compiler import compile_svg
from src.validator import ValidationError, validate_asset

ROOT_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT_DIR / "preview"
STUDIO_VERSION = "0.1.0"
GENERATOR_LIBRARY = [
    {
        "id": "button_sf",
        "path": "examples/button_sf.json",
        "keywords": ["button", "cta", "ボタン", "アクション"],
    },
    {
        "id": "primary_action_states",
        "path": "examples/primary_action_states.json",
        "keywords": ["pressed", "disabled", "状態", "primary"],
    },
    {
        "id": "modal_overlay",
        "path": "examples/modal_overlay.json",
        "keywords": ["modal", "dialog", "モーダル", "ダイアログ", "overlay"],
    },
    {
        "id": "tab_bar",
        "path": "examples/tab_bar.json",
        "keywords": ["tab", "tabs", "タブ", "navigation", "ナビ"],
    },
    {
        "id": "info_panel",
        "path": "examples/info_panel.json",
        "keywords": ["info", "panel", "stats", "データ", "パネル"],
    },
    {
        "id": "toast",
        "path": "examples/toast_feedback.json",
        "keywords": ["toast", "トースト", "feedback", "通知"],
    },
    {
        "id": "hud_basic",
        "path": "examples/hud_basic.mock.json",
        "keywords": ["hud", "ゲージ", "progress", "toggle", "cooldown"],
    },
    {
        "id": "custom_fx_glow",
        "path": "examples/custom_fx_glow.json",
        "keywords": ["fx", "glow", "エフェクト", "発光"],
    },
]


class PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path or "/"
        if path == "/":
            path = "/index.html"

        file_path = (STATIC_DIR / path.lstrip("/")).resolve()
        if not _is_safe_path(file_path):
            self._send_error(404, "Not found")
            return

        if not file_path.is_file():
            self._send_error(404, "Not found")
            return

        content_type = _content_type(file_path)
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/compile":
            if parsed.path == "/api/generate":
                self._handle_generate()
                return
            self._send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        asset = payload.get("asset")
        path = payload.get("path")

        if asset is None and path:
            try:
                asset = _load_json_from_path(str(path))
            except OSError:
                self._send_error(400, "Failed to read file")
                return
            except json.JSONDecodeError:
                self._send_error(400, "Invalid JSON file")
                return

        if not isinstance(asset, dict):
            self._send_error(400, "Asset must be an object")
            return

        try:
            validate_asset(asset)
        except ValidationError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        svg = compile_svg(asset)
        self._send_json(200, {"svg": svg, "asset": asset})

    def _handle_generate(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        prompt = payload.get("prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            self._send_error(400, "Prompt is required")
            return

        selection = _select_template(prompt)
        template_id = selection["selected"]
        asset = selection["asset"]
        if asset is None:
            self._send_error(500, "Template selection failed")
            return

        _apply_generation_metadata(asset, prompt, template_id)

        try:
            validate_asset(asset)
        except ValidationError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        svg = compile_svg(asset)
        self._send_json(
            200,
            {
                "templateId": template_id,
                "svg": svg,
                "asset": asset,
                "selection": selection,
            },
        )

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message})


def _load_json_from_path(path_text: str) -> Dict[str, Any]:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = (ROOT_DIR / path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _select_template(prompt: str) -> Dict[str, Any]:
    lowered = prompt.lower()
    scored: list[dict[str, Any]] = []
    for entry in GENERATOR_LIBRARY:
        matches = [kw for kw in entry["keywords"] if kw.lower() in lowered]
        scored.append(
            {
                "id": entry["id"],
                "path": entry["path"],
                "matches": matches,
                "score": len(matches),
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    if scored and scored[0]["score"] > 0:
        selected = scored[0]
        reason = "keyword_match"
    else:
        selected = {"id": GENERATOR_LIBRARY[0]["id"], "path": GENERATOR_LIBRARY[0]["path"]}
        reason = "fallback"

    asset = _load_json_from_path(selected["path"])
    return {
        "selected": selected["id"],
        "reason": reason,
        "candidates": scored,
        "asset": asset,
    }


def _apply_generation_metadata(asset: Dict[str, Any], prompt: str, template_id: str) -> None:
    metadata = dict(asset.get("metadata") or {})
    metadata["generated_from_prompt"] = prompt
    metadata["selected_templates"] = [template_id]
    metadata["generator_version"] = {
        "schema": asset.get("version", "0.0.0"),
        "studio": STUDIO_VERSION,
    }
    asset["metadata"] = metadata


def _content_type(path: Path) -> str:
    if path.suffix == ".html":
        return "text/html; charset=utf-8"
    if path.suffix == ".css":
        return "text/css; charset=utf-8"
    if path.suffix == ".js":
        return "text/javascript; charset=utf-8"
    if path.suffix == ".svg":
        return "image/svg+xml"
    return "application/octet-stream"


def _is_safe_path(path: Path) -> bool:
    try:
        path.relative_to(STATIC_DIR)
    except ValueError:
        return False
    return True


def run(host: str, port: int) -> None:
    server = HTTPServer((host, port), PreviewHandler)
    print(f"Preview server running at http://{host}:{port}")
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    run(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
