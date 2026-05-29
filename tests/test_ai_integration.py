"""AI統合テスト

実際のAPI呼び出しを行うテスト。
環境変数にAPIキーが設定されている場合のみ実行されます。
"""

import os
import json
import pytest

from src.ai import create_provider
from src.ai.base import AIProviderError
from src.validator import validate_asset
from src.constraints import normalize_asset_constraints
# server.pyの実装をテストでも利用する
from src.preview.server import _clean_top_level_fields

def validate_generated_asset(asset, stage="generation"):
    """生成されたアセットがサーバーロジックを通してバリデーションを通るか検証"""
    print(f"\n--- Raw AI Output ({stage}) ---")
    print(json.dumps(asset, indent=2, ensure_ascii=False))
    
    # サーバー側ロジックの再現
    _clean_top_level_fields(asset)
    normalize_asset_constraints(asset)
    
    print(f"\n--- Normalized Asset ({stage}) ---")
    print(json.dumps(asset, indent=2, ensure_ascii=False))

    try:
        validate_asset(asset)
    except Exception as e:
        print(f"\n!!! VALIDATION ERROR DETAILS !!!\n{e}\n")
        pytest.fail(f"Validation failed during {stage}: {e}")
    return asset


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY環境変数が設定されていません"
)
class TestOpenAIIntegration:
    """OpenAI統合テスト"""

    def test_generate_from_prompt(self):
        """実際のプロンプトからの生成テスト"""
        provider = create_provider("openai")
        
        result = provider.generate_from_prompt(
            "シンプルな青いボタン",
            temperature=0.3
        )
        
        validate_generated_asset(result, "generation")
        
        # メタデータの確認
        assert "metadata" in result
        assert result["metadata"]["ai_provider"] == "openai"

    def test_refine_asset(self):
        """実際の差分修正テスト"""
        provider = create_provider("openai")
        
        # まず素材を生成
        asset = provider.generate_from_prompt(
            "赤いボタン",
            temperature=0.3
        )
        validate_generated_asset(asset, "generation")
        
        # 差分修正
        refined = provider.refine_asset(
            asset,
            "色を青に変更して",
            temperature=0.3
        )
        validate_generated_asset(refined, "refinement")
        
        # 修正履歴の確認
        assert "refinement_history" in refined["metadata"]


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY環境変数が設定されていません"
)
class TestGeminiIntegration:
    """Gemini統合テスト"""

    def test_generate_from_prompt(self):
        """実際のプロンプトからの生成テスト"""
        provider = create_provider("gemini")
        
        result = provider.generate_from_prompt(
            "シンプルな緑のボタン",
            temperature=0.3
        )
        validate_generated_asset(result, "generation")

    def test_refine_asset(self):
        """実際の差分修正テスト"""
        provider = create_provider("gemini")
        
        # まず素材を生成
        asset = provider.generate_from_prompt(
            "黄色いボタン",
            temperature=0.3
        )
        validate_generated_asset(asset, "generation")
        
        # 差分修正
        refined = provider.refine_asset(
            asset,
            "色をオレンジに変更して",
            temperature=0.3
        )
        validate_generated_asset(refined, "refinement")
