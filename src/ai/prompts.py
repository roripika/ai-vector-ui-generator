"""プロンプトテンプレート管理"""

import json
from typing import Any, Dict, Optional


SYSTEM_PROMPT = """あなたはゲームUIデザイン専門のアシスタントです。

## ツールの設計思想

このツールは「AIベクターUIジェネレーター」で、以下の原則に従います:

1. **AIはSVGを直接書かない** - AIの出力はJSONのみ
2. **SVGはプログラムが決定論的に生成** - 同じJSON→同じSVG
3. **編集可能なベクター素材** - IllustratorやInkscapeで編集可能
4. **意味ベースの設計** - role/importance/state等のメタ情報を重視

## あなたの役割

ユーザーのプロンプト(世界観・意図)を解釈し、適切なテンプレートを選択して、
JSON形式のUI素材定義を生成してください。

## JSON仕様の重要ポイント

- `assetType`: button/modal/tab/gauge等の素材種別
- `viewBox`: [x, y, width, height] の配列
- `layers` または `components`: UI要素の構造
- `metadata`: 生成情報やタグ
- `role`: action/navigation/container/data_display/feedback等
- `importance`: primary/secondary/info等
- `state`: default/hover/pressed/disabled等
- `constraint_flags`: ["safe_area", "min_tap"]等の制約フラグ
- `constraint_params`: {"min_tap": {"width": 44, "height": 44}}等の制約パラメータ

## 出力形式

必ずJSON形式で出力してください。マークダウンのコードブロックは不要です。
"""


def build_generation_prompt(
    user_prompt: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """生成用プロンプトを構築
    
    Args:
        user_prompt: ユーザーのプロンプト
        context: テンプレートカタログ等のコンテキスト
        
    Returns:
        完全なプロンプト文字列
    """
    parts = [
        "以下のプロンプトに基づいて、UI素材のJSON定義を生成してください。\n",
        f"## ユーザーのプロンプト\n{user_prompt}\n"
    ]
    
    # コンテキスト情報があれば追加
    if context:
        if "templates" in context:
            templates = context["templates"]
            if templates:
                parts.append("\n## 利用可能なテンプレート\n")
                for template in templates[:10]:  # 最大10件
                    template_id = template.get("id", "unknown")
                    intent = template.get("intent", "")
                    when = template.get("when", [])
                    parts.append(f"- {template_id}: {intent}")
                    if when:
                        parts.append(f" (使用例: {', '.join(when[:3])})")
                    parts.append("\n")
        
        if "tags" in context:
            tags = context["tags"]
            if tags:
                parts.append(f"\n## 推奨タグ\n{', '.join(tags[:20])}\n")
    
    parts.append("\n## 出力要件\n")
    parts.append("- JSON形式で出力(マークダウン不要)\n")
    parts.append("- assetType, viewBox, layers/componentsは必須\n")
    parts.append("- metadata.tagsに適切なタグを設定\n")
    parts.append("- role, importance, stateを適切に設定\n")
    
    return "".join(parts)


def build_refinement_prompt(
    asset: Dict[str, Any],
    instruction: str
) -> str:
    """差分修正用プロンプトを構築
    
    Args:
        asset: 既存のUI素材
        instruction: 修正指示
        
    Returns:
        完全なプロンプト文字列
    """
    asset_json = json.dumps(asset, ensure_ascii=False, indent=2)
    
    parts = [
        "以下のUI素材JSONを、指示に従って修正してください。\n",
        f"\n## 現在のJSON\n```json\n{asset_json}\n```\n",
        f"\n## 修正指示\n{instruction}\n",
        "\n## 出力要件\n",
        "- 修正後の完全なJSONを出力(マークダウン不要)\n",
        "- 指示された部分のみを変更し、他は保持\n",
        "- 構造の一貫性を維持\n"
    ]
    
    return "".join(parts)


def build_template_selection_prompt(
    user_prompt: str,
    templates: list
) -> str:
    """テンプレート選択用プロンプトを構築
    
    Args:
        user_prompt: ユーザーのプロンプト
        templates: テンプレート一覧
        
    Returns:
        プロンプト文字列
    """
    parts = [
        "以下のプロンプトに最適なテンプレートを選択してください。\n",
        f"\n## ユーザーのプロンプト\n{user_prompt}\n",
        "\n## テンプレート候補\n"
    ]
    
    for i, template in enumerate(templates[:20], 1):
        template_id = template.get("id", "unknown")
        intent = template.get("intent", "")
        when = template.get("when", [])
        avoid = template.get("avoid", [])
        
        parts.append(f"{i}. {template_id}\n")
        parts.append(f"   - 目的: {intent}\n")
        if when:
            parts.append(f"   - 使用例: {', '.join(when[:3])}\n")
        if avoid:
            parts.append(f"   - 避けるべき: {', '.join(avoid[:2])}\n")
    
    parts.append("\n## 出力形式\n")
    parts.append('{"selected": "template_id", "reason": "選択理由"}\n')
    
    return "".join(parts)
