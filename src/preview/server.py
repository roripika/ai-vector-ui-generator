"""Local preview server for JSON → SVG."""
from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from dotenv import load_dotenv

from src.compiler import compile_svg
from src.constraints import normalize_asset_constraints
from src.validator import ValidationError, validate_asset

# 環境変数を読み込み
load_dotenv()

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
    {
        "id": "linear_gauge_base",
        "path": "examples/linear_gauge_base.json",
        "keywords": ["linear", "gauge", "bar", "progress", "直線", "バー", "ゲージ"],
        "tags": ["data_display", "progress", "gauge", "linear"],
        "intent": "直線ゲージで進捗を表示する",
        "when": ["横長エリアで進捗を見せたい"],
    },
    {
        "id": "hp_bar_linear",
        "path": "examples/hp_bar_linear.json",
        "keywords": ["hp", "health", "bar", "ヘルス", "体力", "HP", "バー"],
        "tags": ["data_display", "progress", "gauge", "linear", "hp"],
        "intent": "HPバーで体力を表示する",
        "when": ["キャラクターの体力を見せたい"],
    },
    {
        "id": "xp_bar_segmented",
        "path": "examples/xp_bar_segmented.json",
        "keywords": ["xp", "experience", "level", "segmented", "経験値", "レベル", "段階"],
        "tags": ["data_display", "progress", "gauge", "linear", "xp", "segmented"],
        "intent": "段階式XPバーでレベル進捗を表示する",
        "when": ["レベルアップまでの段階を見せたい"],
    },
    {
        "id": "stamina_bar_linear",
        "path": "examples/stamina_bar_linear.json",
        "keywords": ["stamina", "energy", "bar", "スタミナ", "エネルギー", "行動力"],
        "tags": ["data_display", "progress", "gauge", "linear", "stamina"],
        "intent": "スタミナバーで行動力を表示する",
        "when": ["スタミナ/エネルギーの残量を見せたい"],
    },
    {
        "id": "list_cell_base",
        "path": "examples/list_cell_base.json",
        "keywords": ["list", "cell", "item", "リスト", "セル", "一覧"],
        "tags": ["container", "list", "cell"],
        "intent": "リストセルで情報を整理して表示する",
        "when": ["一覧表示でアイテムを並べたい"],
    },
    {
        "id": "list_cell_shop_item",
        "path": "examples/list_cell_shop_item.json",
        "keywords": ["shop", "store", "item", "price", "ショップ", "商品", "価格"],
        "tags": ["container", "list", "cell", "shop", "price"],
        "intent": "ショップアイテムセルで商品情報を表示する",
        "when": ["ショップで商品を一覧表示したい"],
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
        if path == "/api/templates":
            self._handle_templates()
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
        if parsed.path == "/api/generate_texture":
            self._handle_generate_texture()
            return
        if parsed.path == "/api/refine":
            self._handle_refine()
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

        # AI設定を取得(フロントエンドまたは環境変数)
        ai_config = payload.get("ai_config", {})
        use_ai = ai_config.get("enabled", False)
        
        asset = None
        template_id = None
        selection = None
        
        # AI生成を試行
        if use_ai:
            try:
                asset, template_id = _generate_with_ai(prompt, ai_config)
            except Exception as e:
                # AI生成失敗時はログに記録してフォールバック
                print(f"AI generation failed: {e}")
        
        # AI生成失敗またはAI未使用の場合はテンプレート選択
        if asset is None:
            selection = _select_template(prompt)
            template_id = selection["selected"]
            asset = selection["asset"]
            if asset is None:
                self._send_error(500, "Template selection failed")
                return

        _apply_generation_metadata(asset, prompt, template_id)
        # AIが誤ってトップレベルに不要なフィールドを出力した場合のクリーニング
        _clean_top_level_fields(asset)
        normalize_asset_constraints(asset)

        try:
            validate_asset(asset)
        except ValidationError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        svg = compile_svg(asset)
        
        response_data = {
            "templateId": template_id,
            "svg": svg,
            "asset": asset,
        }
        
        if selection:
            response_data["selection"] = selection
        
        self._send_json(200, response_data)

    def _handle_generate_texture(self) -> None:
        """指定されたプロンプトからテクスチャ画像を生成する"""
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        prompt = payload.get("prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            self._send_error(400, "Prompt is required for texture")
            return

        ai_config = payload.get("ai_config", {})
        
        try:
            from src.ai import create_provider
            import os
            import time
            from pathlib import Path

            provider_name = ai_config.get("provider") or os.getenv("AI_PROVIDER", "openai")
            api_key = ai_config.get("api_key") or None
            
            provider = create_provider(provider_name=provider_name, api_key=api_key, model=None)
            
            generated_dir = ROOT_DIR / "generated" / "textures"
            generated_dir.mkdir(parents=True, exist_ok=True)
            filename = f"tex_{int(time.time())}.png"
            output_path = generated_dir / filename
            
            image_uri = provider.generate_image(prompt, str(output_path))
            
            self._send_json(200, {
                "ok": True,
                "texture_uri": image_uri,
                "texture_path": str(Path("generated") / "textures" / filename)
            })
        except Exception as e:
            self._send_json(400, {"error": f"Texture generation failed: {e}"})

    def _handle_refine(self) -> None:
        """AI差分修正エンドポイント"""
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return

        asset = payload.get("asset")
        instruction = payload.get("instruction", "")
        ai_config = payload.get("ai_config", {})

        if not isinstance(asset, dict):
            self._send_error(400, "Asset must be an object")
            return

        if not isinstance(instruction, str) or not instruction.strip():
            self._send_error(400, "Instruction is required")
            return

        # AI差分修正を試行
        try:
            refined_asset = _refine_with_ai(asset, instruction, ai_config)
        except Exception as e:
            self._send_json(400, {"error": f"Refinement failed: {e}"})
            return

        # AIが誤ってトップレベルに不要なフィールドを出力した場合のクリーニング
        _clean_top_level_fields(refined_asset)
        normalize_asset_constraints(refined_asset)

        try:
            validate_asset(refined_asset)
        except ValidationError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        svg = compile_svg(refined_asset)
        self._send_json(
            200,
            {
                "svg": svg,
                "asset": refined_asset,
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

    def _handle_templates(self) -> None:
        """テンプレート一覧を返す"""
        templates = [
            {
                "id": entry["id"],
                "intent": entry.get("intent", ""),
                "when": entry.get("when", []),
                "tags": entry.get("tags", []),
                "keywords": entry.get("keywords", [])
            }
            for entry in GENERATOR_LIBRARY
        ]
        self._send_json(200, {"templates": templates})

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


def _generate_with_ai(prompt: str, ai_config: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """AIを使用してUI素材を生成
    
    Args:
        prompt: ユーザーのプロンプト
        ai_config: AI設定(provider, api_key, model等)
        
    Returns:
        (生成されたasset, template_id)のタプル
        
    Raises:
        Exception: AI生成に失敗した場合
    """
    from src.ai import create_provider
    
    # プロバイダー設定を取得
    provider_name = ai_config.get("provider") or os.getenv("AI_PROVIDER", "openai")
    api_key = ai_config.get("api_key") or None  # Noneの場合は環境変数から取得
    model = ai_config.get("model") or None
    
    # テンプレートカタログをコンテキストとして渡す
    context = {
        "templates": [
            {
                "id": entry["id"],
                "intent": entry.get("intent", ""),
                "when": entry.get("when", []),
                "tags": entry.get("tags", [])
            }
            for entry in GENERATOR_LIBRARY[:10]  # 最大10件
        ],
        "tags": list(_allowed_tags(_load_tags_vocab()))[:20]  # 最大20件
    }
    
    # プロバイダーを作成
    provider = create_provider(
        provider_name=provider_name,
        api_key=api_key,
        model=model
    )
    
    # AI生成
    asset = provider.generate_from_prompt(prompt, context=context)
    
    # template_idを取得(metadataから)
    template_id = "ai_generated"
    if "metadata" in asset and "selected_templates" in asset["metadata"]:
        templates = asset["metadata"]["selected_templates"]
        if templates and isinstance(templates, list):
            template_id = templates[0]
    
    return asset, template_id


def _refine_with_ai(
    asset: Dict[str, Any],
    instruction: str,
    ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """AIを使用してUI素材を差分修正
    
    Args:
        asset: 既存のUI素材
        instruction: 修正指示
        ai_config: AI設定
        
    Returns:
        修正後のasset
        
    Raises:
        Exception: AI修正に失敗した場合
    """
    from src.ai import create_provider
    
    # プロバイダー設定を取得
    provider_name = ai_config.get("provider") or os.getenv("AI_PROVIDER", "openai")
    api_key = ai_config.get("api_key") or None
    model = ai_config.get("model") or None
    
    # プロバイダーを作成
    provider = create_provider(
        provider_name=provider_name,
        api_key=api_key,
        model=model
    )
    
    # AI差分修正
    refined_asset = provider.refine_asset(asset, instruction)
    
    return refined_asset


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


def _clean_top_level_fields(asset: Dict[str, Any]) -> None:
    """AI生成物のフィールドを正規化・クリーニングする"""
    if not isinstance(asset, dict):
        return

    # 再帰的に正規化
    _normalize_dict_fields(asset)
    
    # buttonAsset/screenAssetのスキーマに含まれない不要なトップレベルフィールドを削除
    invalid_fields = {
        "role", "importance", "state", 
        "constraints", "constraint_flags", "constraint_params",
        "layout_ref", "shape_profile", "shape_params", "value_model"
    }
    
    for field in invalid_fields:
        if field in asset:
            del asset[field]

    # viewBox内への収まりを強制
    _enforce_viewbox_bounds(asset)
    
    # metadataの正規化
    _clean_metadata(asset)
    
    # トークン(style, font等)の正規化
    _normalize_tokens(asset)


def _normalize_tokens(asset: Dict[str, Any]) -> None:
    """トークン(fill, stroke, font等)がドットを含まない場合、prefixを付与して正規化する"""
    
    def normalize_color(val: Any) -> Any:
        if not isinstance(val, str): return val
        if "." in val: return val
        if val.startswith("#"): return f"colors.hex_{val[1:].lower()}"
        return f"colors.{val}"

    def normalize_font(val: Any) -> Any:
        if not isinstance(val, str): return val
        if "." in val: return val
        return f"fonts.{val}"

    def process_layer(layer):
        # styleオブジェクトの処理
        if "style" in layer and isinstance(layer["style"], dict):
            style = layer["style"]
            for key in ["fill", "stroke", "glow", "track", "knobFill"]:
                if key in style:
                    style[key] = normalize_color(style[key])
        
        # text.fontの処理
        if "text" in layer and isinstance(layer["text"], dict):
            text = layer["text"]
            if "font" in text:
                text["font"] = normalize_font(text["font"])

        # 子要素があれば再帰
        if "layers" in layer and isinstance(layer["layers"], list):
            for sub in layer["layers"]:
                process_layer(sub)
    
    if "layers" in asset and isinstance(asset["layers"], list):
        for layer in asset["layers"]:
            process_layer(layer)


def _clean_metadata(asset: Dict[str, Any]) -> None:
    """metadata内のスキーマ外フィールドをtagsに移動する"""
    if "metadata" not in asset or not isinstance(asset["metadata"], dict):
        return
        
    meta = asset["metadata"]
    allowed_keys = {
        "name", "description", "tags", 
        "generated_from_prompt", "selected_templates", "generator_version",
        "refinement_history"
    }
    
    if "tags" not in meta:
        meta["tags"] = []
    elif not isinstance(meta["tags"], list):
        meta["tags"] = [] # tagsがリストでなければ初期化
    
    keys_to_move = []
    for k in list(meta.keys()):
        if k not in allowed_keys:
            keys_to_move.append(k)
            
    for k in keys_to_move:
        val = meta.pop(k)
        # tagsに追加 (値が単純な型で、空でない場合)
        if isinstance(val, (str, int, float, bool)) and str(val):
            # 既存のタグと重複しないようにチェックしてもいいが、単純に追加
            meta["tags"].append(f"{k}:{val}")


def _enforce_viewbox_bounds(asset: Dict[str, Any]) -> None:
    """各レイヤーがviewBoxからはみ出さないように補正する"""
    if "viewBox" not in asset or not isinstance(asset["viewBox"], list) or len(asset["viewBox"]) != 4:
        return
        
    vx, vy, vw, vh = asset["viewBox"]
    # viewBox自体が異常値なら無視
    if not (isinstance(vw, (int, float)) and isinstance(vh, (int, float)) and vw > 0 and vh > 0):
        return

    # 再帰的にチェックする関数
    def clamp_layer(layer):
        if "rect" in layer and isinstance(layer["rect"], dict):
            r = layer["rect"]
            if all(k in r for k in ("x", "y", "width", "height")):
                x, y, w, h = r["x"], r["y"], r["width"], r["height"]
                
                # 左上のはみ出し補正
                if x < 0:
                    w += x  # wを減らす
                    x = 0
                if y < 0:
                    h += y
                    y = 0
                
                # 右下によるはみ出し補正
                if x + w > vw:
                    w = max(0, vw - x)
                if y + h > vh:
                    h = max(0, vh - y)
                
                # 更新
                r["x"], r["y"], r["width"], r["height"] = x, y, w, h

        # 子要素があれば再帰
        if "layers" in layer and isinstance(layer["layers"], list):
            for sub in layer["layers"]:
                clamp_layer(sub)
    
    if "layers" in asset and isinstance(asset["layers"], list):
        for layer in asset["layers"]:
            clamp_layer(layer)


def _normalize_dict_fields(data: Dict[str, Any]) -> None:
    """辞書内の独自フィールド（position, size, type, attributesなど）をスキーマに合わせて変換する"""
    # 1. attributes / properties の展開
    for attr_key in ("attributes", "properties"):
        if attr_key in data:
            attrs = data.pop(attr_key)
            if isinstance(attrs, dict):
                # 親にマージ (既にあるキーは上書きしない)
                for k, v in attrs.items():
                    data.setdefault(k, v)

    # 2. type -> shape の変換
    if "type" in data and "shape" not in data:
        data["shape"] = data.pop("type")

    # 3. shapeエイリアスの解決
    if "shape" in data:
        shape_val = data["shape"]
        # 一般的な名称をシステム定義のshapeにマッピング
        shape_map = {
            "rectangle": "roundedRect",
            "rect": "roundedRect",
            "box": "roundedRect",
            "background": "roundedRect",  # 背景は矩形扱い
            "circle": "gauge",            # 円形はとりあえずgaugeにしておく等の救済策(完全ではない)
            "label": "text",
            "glowEffect": "roundedRect"   # 救済: エフェクトも矩形として処理
        }
        if shape_val in shape_map:
            data["shape"] = shape_map[shape_val]
            
        # background等の場合、IDも設定しておく
        if shape_val == "background" and "id" not in data:
            data["id"] = "background"

    # 4. position [x, y] -> x, y
    if "position" in data:
        pos = data["position"]
        if isinstance(pos, list) and len(pos) >= 2:
            data.pop("position")
            data.setdefault("x", pos[0])
            data.setdefault("y", pos[1])
            
    # 5. size [w, h] -> width, height
    if "size" in data:
        size = data["size"]
        if isinstance(size, list) and len(size) >= 2:
            data.pop("size")
            data.setdefault("width", size[0])
            data.setdefault("height", size[1])
        elif isinstance(size, dict):
            data.pop("size")
            if "width" in size: data.setdefault("width", size["width"])
            if "height" in size: data.setdefault("height", size["height"])
            
    # 6. assetType の修正
    if "assetType" in data:
        # button_sf などIDが入っていたら button に戻す
        val = data["assetType"]
        if val != "button" and val != "screen":
            # 簡易判定: layersがあればbutton、componentsがあればscreen、わからなければbutton
            if "components" in data:
                data["assetType"] = "screen"
            else:
                data["assetType"] = "button"

    # 再帰処理 (layers, components, rect 等) -- values() をコピーしてイテレートしないと変更中にエラーになるかも
    for key, value in list(data.items()):
        if isinstance(value, dict):
            _normalize_dict_fields(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _normalize_dict_fields(item)


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
