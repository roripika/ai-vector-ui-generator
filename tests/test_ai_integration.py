"""AI統合テスト

実際のAPI呼び出しを行うテスト。
環境変数にAPIキーが設定されている場合のみ実行されます。
"""

import os

import pytest

from src.ai import create_provider
from src.ai.base import AIProviderError


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
        
        # 基本構造の確認
        assert "assetType" in result
        assert "viewBox" in result
        assert isinstance(result["viewBox"], list)
        assert len(result["viewBox"]) == 4
        
        # メタデータの確認
        assert "metadata" in result
        assert result["metadata"]["generated_from_prompt"] == "シンプルな青いボタン"
        assert result["metadata"]["ai_provider"] == "openai"

    def test_refine_asset(self):
        """実際の差分修正テスト"""
        provider = create_provider("openai")
        
        # まず素材を生成
        asset = provider.generate_from_prompt(
            "赤いボタン",
            temperature=0.3
        )
        
        # 差分修正
        refined = provider.refine_asset(
            asset,
            "色を青に変更して",
            temperature=0.3
        )
        
        # 基本構造の確認
        assert "assetType" in refined
        assert "viewBox" in refined
        
        # 修正履歴の確認
        assert "metadata" in refined
        assert "refinement_history" in refined["metadata"]
        assert len(refined["metadata"]["refinement_history"]) > 0


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
        
        # 基本構造の確認
        assert "assetType" in result
        assert "viewBox" in result
        assert isinstance(result["viewBox"], list)
        assert len(result["viewBox"]) == 4
        
        # メタデータの確認
        assert "metadata" in result
        assert result["metadata"]["generated_from_prompt"] == "シンプルな緑のボタン"
        assert result["metadata"]["ai_provider"] == "gemini"

    def test_refine_asset(self):
        """実際の差分修正テスト"""
        provider = create_provider("gemini")
        
        # まず素材を生成
        asset = provider.generate_from_prompt(
            "黄色いボタン",
            temperature=0.3
        )
        
        # 差分修正
        refined = provider.refine_asset(
            asset,
            "色をオレンジに変更して",
            temperature=0.3
        )
        
        # 基本構造の確認
        assert "assetType" in refined
        assert "viewBox" in refined
        
        # 修正履歴の確認
        assert "metadata" in refined
        assert "refinement_history" in refined["metadata"]
        assert len(refined["metadata"]["refinement_history"]) > 0


class TestProviderFallback:
    """プロバイダーフォールバックのテスト"""

    def test_invalid_api_key(self):
        """無効なAPIキーのテスト"""
        with pytest.raises(Exception):
            provider = create_provider("openai", api_key="invalid-key")
            provider.generate_from_prompt("テスト")
