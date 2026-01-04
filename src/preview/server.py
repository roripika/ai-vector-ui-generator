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
