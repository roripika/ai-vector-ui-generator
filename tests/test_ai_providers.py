"""AI Providerのユニットテスト"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.ai.base import AIProviderError, BaseAIProvider
from src.ai.factory import create_provider
from src.ai.openai_provider import OpenAIProvider
from src.ai.gemini_provider import GeminiProvider


class TestBaseAIProvider:
    """BaseAIProviderのテスト"""

    def test_validate_json_structure_valid(self):
        """有効なJSON構造の検証"""
        provider = OpenAIProvider(api_key="test-key")
        
        valid_data = {
            "assetType": "button",
            "viewBox": [0, 0, 100, 100],
            "layers": []
        }
        
        assert provider._validate_json_structure(valid_data) is True

    def test_validate_json_structure_invalid(self):
        """無効なJSON構造の検証"""
        provider = OpenAIProvider(api_key="test-key")
        
        invalid_data = {
            "assetType": "button"
            # viewBoxが欠けている
        }
        
        assert provider._validate_json_structure(invalid_data) is False


class TestOpenAIProvider:
    """OpenAIProviderのテスト"""

    def test_initialization(self):
        """初期化のテスト"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
        
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4o"

    def test_default_model(self):
        """デフォルトモデルのテスト"""
        provider = OpenAIProvider(api_key="test-key")
        
        assert provider.model == OpenAIProvider.DEFAULT_MODEL

    @patch('openai.OpenAI')
    def test_generate_from_prompt_success(self, mock_openai_class):
        """プロンプトからの生成成功テスト"""
        # モックレスポンスを設定
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "assetType": "button",
            "viewBox": [0, 0, 100, 100],
            "layers": []
        })
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(api_key="test-key")
        result = provider.generate_from_prompt("神殿風のボタン")
        
        assert result["assetType"] == "button"
        assert "metadata" in result
        assert result["metadata"]["generated_from_prompt"] == "神殿風のボタン"
        assert result["metadata"]["ai_provider"] == "openai"

    @patch('openai.OpenAI')
    def test_refine_asset_success(self, mock_openai_class):
        """差分修正成功テスト"""
        # モックレスポンスを設定
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "assetType": "button",
            "viewBox": [0, 0, 100, 100],
            "layers": []
        })
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(api_key="test-key")
        asset = {
            "assetType": "button",
            "viewBox": [0, 0, 100, 100],
            "layers": []
        }
        
        result = provider.refine_asset(asset, "もっと強調して")
        
        assert result["assetType"] == "button"
        assert "metadata" in result
        assert "refinement_history" in result["metadata"]


class TestGeminiProvider:
    """GeminiProviderのテスト"""

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_initialization(self, mock_model, mock_configure):
        """初期化のテスト"""
        provider = GeminiProvider(api_key="test-key", model="gemini-1.5-pro")
        
        assert provider.api_key == "test-key"
        assert provider.model == "gemini-1.5-pro"
        mock_configure.assert_called_once_with(api_key="test-key")

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_default_model(self, mock_model, mock_configure):
        """デフォルトモデルのテスト"""
        provider = GeminiProvider(api_key="test-key")
        
        assert provider.model == GeminiProvider.DEFAULT_MODEL


class TestFactory:
    """ファクトリーのテスト"""

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-openai-key'})
    def test_create_openai_provider(self):
        """OpenAIプロバイダー作成のテスト"""
        provider = create_provider("openai")
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-openai-key"

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-gemini-key'})
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_create_gemini_provider(self, mock_model, mock_configure):
        """Geminiプロバイダー作成のテスト"""
        provider = create_provider("gemini")
        
        assert isinstance(provider, GeminiProvider)
        assert provider.api_key == "test-gemini-key"

    def test_create_provider_invalid(self):
        """無効なプロバイダー名のテスト"""
        with pytest.raises(AIProviderError):
            create_provider("invalid-provider", api_key="test-key")

    def test_create_provider_missing_api_key(self):
        """APIキー未設定のテスト"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(AIProviderError):
                create_provider("openai")
