"""Local preview server for JSON → SVG."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from src.compiler import compile_svg
from src.constraints import normalize_asset_constraints
from src.validator import ValidationError, validate_asset

ROOT_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT_DIR / "preview"
STUDIO_VERSION = "0.1.0"
GENERATOR_LIBRARY = [
    {
        "id": "button_sf",
        "path": "examples/button_sf.json",
        "keywords": ["button", "cta", "ボタン", "アクション"],
        "tags": ["action", "primary"],
        "intent": "主要アクションを強調するボタン",
        "when": ["CTAを目立たせたい", "最重要の操作を配置したい"],
    },
    {
        "id": "primary_action_states",
        "path": "examples/primary_action_states.json",
        "keywords": ["pressed", "disabled", "状態", "primary"],
        "tags": ["action", "primary", "state"],
        "intent": "主要ボタンの状態差分を示す",
        "when": ["押下/無効状態を確認したい"],
    },
    {
        "id": "modal_overlay",
        "path": "examples/modal_overlay.json",
        "keywords": ["modal", "dialog", "モーダル", "ダイアログ", "overlay"],
        "tags": ["modal", "overlay"],
        "intent": "モーダルで確認や入力を促す",
        "when": ["画面をブロックして注意喚起したい"],
    },
    {
        "id": "tab_bar",
        "path": "examples/tab_bar.json",
        "keywords": ["tab", "tabs", "タブ", "navigation", "ナビ"],
        "tags": ["navigation", "tab", "badge"],
        "intent": "主要画面の切り替えを提供する",
        "when": ["複数セクションの移動が必要"],
    },
    {
        "id": "info_panel",
        "path": "examples/info_panel.json",
        "keywords": ["info", "panel", "stats", "データ", "パネル"],
        "tags": ["data_display", "info"],
        "intent": "情報をパネルで読みやすくまとめる",
        "when": ["複数の数値や説明を並べたい"],
    },
    {
        "id": "toast",
        "path": "examples/toast_feedback.json",
        "keywords": ["toast", "トースト", "feedback", "通知"],
        "tags": ["feedback"],
        "intent": "非ブロッキング通知を表示する",
        "when": ["操作の結果を軽く伝えたい"],
    },
    {
        "id": "hud_basic",
        "path": "examples/hud_basic.mock.json",
        "keywords": ["hud", "ゲージ", "progress", "toggle", "cooldown"],
        "tags": ["progress", "cooldown", "toggle"],
        "intent": "HUD上の状態と操作をまとめて表示する",
        "when": ["戦闘中に複数情報を出したい"],
    },
    {
        "id": "custom_fx_glow",
        "path": "examples/custom_fx_glow.json",
        "keywords": ["fx", "glow", "エフェクト", "発光"],
        "tags": ["decoration", "fx_glow"],
        "intent": "発光演出で注目を集める",
        "when": ["演出効果を追加したい"],
    },
    {
        "id": "gauge_radial_polygon",
        "path": "examples/gauge_radial_polygon.json",
        "keywords": ["gauge", "meter", "progress", "radial", "polygon", "ゲージ", "進捗", "円形"],
        "tags": ["data_display", "progress", "gauge", "radial"],
        "intent": "円形ゲージで進捗を示す",
        "when": ["HUDで進捗を目立たせたい"],
    },
    {
        "id": "gauge_segmented",
        "path": "examples/gauge_segmented.json",
        "keywords": ["gauge", "segmented", "step", "cooldown", "ゲージ", "段階", "クールダウン"],
        "tags": ["data_display", "progress", "cooldown"],
        "intent": "段階的な進捗を表示する",
        "when": ["ステップ数が決まっている"],
    },
    {
        "id": "dial_knob",
        "path": "examples/dial_knob.json",
        "keywords": ["dial", "knob", "adjust", "回転", "ダイヤル", "ノブ"],
        "tags": ["control", "dial", "knob", "radial"],
        "intent": "回転ダイヤルで値を微調整する",
        "when": ["細かな値調整が必要"],
    },
    {
        "id": "radial_slider",
        "path": "examples/radial_slider.json",
        "keywords": ["radial", "slider", "dial", "円形", "スライダー"],
        "tags": ["control", "dial", "radial"],
        "intent": "円形スライダーで範囲を調整する",
        "when": ["連続値の調整が必要"],
    },
    {
        "id": "radial_gauge",
        "path": "examples/radial_gauge.json",
        "keywords": ["radial", "gauge", "progress", "円形", "ゲージ"],
        "tags": ["data_display", "progress", "gauge", "radial"],
        "intent": "円形ゲージで進捗を可視化する",
        "when": ["進捗を直感的に見せたい"],
    },
    {
        "id": "cooldown_wheel",
        "path": "examples/cooldown_wheel.json",
        "keywords": ["cooldown", "wheel", "radial", "クールダウン", "円形"],
        "tags": ["data_display", "cooldown", "radial"],
        "intent": "クールダウン残量を円形で示す",
        "when": ["再使用待ち時間を見せたい"],
    },
    {
        "id": "badge_count",
        "path": "examples/badge_count.json",
        "keywords": ["badge", "count", "notification", "バッジ", "通知"],
        "tags": ["badge", "feedback"],
        "intent": "未読数などのカウントを通知する",
        "when": ["通知数を小さく表示したい"],
    },
    {
        "id": "card_frame_rarity",
        "path": "examples/card_frame_rarity.json",
        "keywords": ["card", "frame", "rarity", "カード", "枠", "レア"],
        "tags": ["container", "card", "rarity", "decoration"],
        "intent": "カード枠でレアリティを強調する",
        "when": ["カードの希少度を枠で表現する"],
    },
]


class PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path or "/"
        if path == "/api/list_generated":
            self._handle_list_generated()
            return
        if path == "/api/tags":
            self._handle_tags()
            return
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
        if parsed.path == "/api/compile":
            self._handle_compile()
            return
        if parsed.path == "/api/generate":
            self._handle_generate()
            return
        if parsed.path == "/api/save":
            self._handle_save()
            return
        self._send_error(404, "Not found")
        return

    def _handle_compile(self) -> None:
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

        normalize_asset_constraints(asset)

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
        normalize_asset_constraints(asset)

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

    def _handle_save(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        asset = payload.get("asset")
        filename = payload.get("filename")
        tags = payload.get("tags")

        if not isinstance(asset, dict):
            self._send_error(400, "Asset must be an object")
            return

        normalize_asset_constraints(asset)

        tag_list = _coerce_tags(tags)
        warnings = _warn_unknown_tags(tag_list)

        metadata = dict(asset.get("metadata") or {})
        existing_tags = metadata.get("tags")
        if not isinstance(existing_tags, list):
            existing_tags = []
        merged = _merge_tags(existing_tags, tag_list)
        if merged:
            metadata["tags"] = merged
        asset["metadata"] = metadata

        try:
            validate_asset(asset)
        except ValidationError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        safe_name = _sanitize_filename(filename)
        if not safe_name:
            self._send_error(400, "Filename is required")
            return

        generated_dir = ROOT_DIR / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        final_name = _ensure_unique_filename(generated_dir, safe_name)
        file_path = generated_dir / final_name
        file_path.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")

        self._send_json(
            200,
            {
                "ok": True,
                "path": str(Path("generated") / final_name),
                "name": final_name,
                "warnings": warnings,
            },
        )

    def _handle_list_generated(self) -> None:
        generated_dir = ROOT_DIR / "generated"
        if not generated_dir.exists():
            self._send_json(200, {"files": []})
            return

        files = []
        for path in sorted(generated_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            files.append(
                {
                    "name": path.name,
                    "path": str(Path("generated") / path.name),
                    "modified": path.stat().st_mtime,
                }
            )
        self._send_json(200, {"files": files})

    def _handle_tags(self) -> None:
        vocab = _load_tags_vocab()
        allowed = sorted(_allowed_tags(vocab))
        self._send_json(200, {"tags": allowed, "vocab": vocab})

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


def _load_tags_vocab() -> Dict[str, list[str]]:
    tags_path = ROOT_DIR / "ui-templates" / "_catalog" / "tags.yaml"
    if not tags_path.exists():
        return {}
    vocab: Dict[str, list[str]] = {}
    current_key: str | None = None
    for line in tags_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" "):
            current_key = stripped.rstrip(":")
            vocab.setdefault(current_key, [])
            continue
        if current_key and stripped.startswith("- "):
            value = stripped[2:].strip()
            if value:
                vocab[current_key].append(value)
    return vocab


def _allowed_tags(vocab: Dict[str, list[str]]) -> set[str]:
    allowed: set[str] = set()
    for key in ("roles", "importance", "states", "constraints", "fx_tags"):
        allowed.update(vocab.get(key, []))
    return allowed


def _coerce_tags(tags: Any) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, list):
        return [str(tag).strip() for tag in tags if str(tag).strip()]
    if isinstance(tags, str):
        return [value.strip() for value in tags.split(",") if value.strip()]
    return []


def _warn_unknown_tags(tags: list[str]) -> list[str]:
    vocab = _load_tags_vocab()
    allowed = _allowed_tags(vocab)
    return [tag for tag in tags if tag not in allowed]


def _merge_tags(existing: list[str], extra: list[str]) -> list[str]:
    merged: list[str] = []
    seen = set()
    for tag in existing + extra:
        if tag in seen:
            continue
        seen.add(tag)
        merged.append(tag)
    return merged


def _sanitize_filename(filename: Any) -> str:
    if not isinstance(filename, str):
        return ""
    trimmed = filename.strip()
    if not trimmed:
        return ""
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".",) else "_" for ch in trimmed)
    if not safe.endswith(".json"):
        safe = f"{safe}.json"
    return safe


def _ensure_unique_filename(base_dir: Path, filename: str) -> str:
    candidate = filename
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while (base_dir / candidate).exists():
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def _select_template(prompt: str) -> Dict[str, Any]:
    lowered = prompt.lower()
    scored: list[dict[str, Any]] = []
    for entry in GENERATOR_LIBRARY:
        matches = [kw for kw in entry["keywords"] if kw.lower() in lowered]
        tags = entry.get("tags", [])
        tag_matches = [tag for tag in tags if isinstance(tag, str) and tag.lower() in lowered]
        scored.append(
            {
                "id": entry["id"],
                "path": entry["path"],
                "matches": matches,
                "tag_matches": tag_matches,
                "tags": tags,
                "intent": entry.get("intent"),
                "when": entry.get("when"),
                "score": len(matches),
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    if scored and scored[0]["score"] > 0:
        selected = scored[0]
        reason = "keyword_match"
    else:
        selected = scored[0] if scored else {"id": "", "path": ""}
        reason = "fallback"

    asset = _load_json_from_path(selected["path"])
    return {
        "selected": selected["id"],
        "reason": reason,
        "candidates": scored,
        "rationale": {
            "matched_tags": selected.get("tag_matches", []),
            "intent": selected.get("intent"),
            "when": selected.get("when", []),
        },
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
