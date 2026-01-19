"""AIプロバイダーのファクトリー"""

import os
from typing import Optional

from .base import AIProviderError, BaseAIProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider


def create_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> BaseAIProvider:
    """AIプロバイダーのインスタンスを生成
    
    Args:
        provider_name: プロバイダー名 ("openai" | "gemini")
                      省略時は環境変数AI_PROVIDERまたはデフォルト
        api_key: APIキー(省略時は環境変数から取得)
        model: モデル名(省略時は各プロバイダーのデフォルト)
        **kwargs: プロバイダー固有の設定
        
    Returns:
        AIプロバイダーのインスタンス
        
    Raises:
        AIProviderError: プロバイダーの生成に失敗した場合
        
    Examples:
        >>> # 環境変数から自動設定
        >>> provider = create_provider()
        
        >>> # OpenAIを明示的に指定
        >>> provider = create_provider("openai", api_key="sk-...")
        
        >>> # Geminiを使用
        >>> provider = create_provider("gemini", api_key="...", model="gemini-1.5-pro")
    """
    # プロバイダー名の決定
    if provider_name is None:
        provider_name = os.getenv("AI_PROVIDER", "openai")
    
    provider_name = provider_name.lower()
    
    # OpenAIプロバイダー
    if provider_name == "openai":
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIProviderError(
                "OpenAI APIキーが設定されていません。"
                "環境変数OPENAI_API_KEYを設定するか、api_key引数で指定してください。"
            )
        
        if model is None:
            model = os.getenv("OPENAI_MODEL")
        
        return OpenAIProvider(api_key=api_key, model=model, **kwargs)
    
    # Geminiプロバイダー
    elif provider_name == "gemini":
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AIProviderError(
                "Gemini APIキーが設定されていません。"
                "環境変数GEMINI_API_KEYを設定するか、api_key引数で指定してください。"
            )
        
        if model is None:
            model = os.getenv("GEMINI_MODEL")
        
        return GeminiProvider(api_key=api_key, model=model, **kwargs)
    
    else:
        raise AIProviderError(
            f"未対応のプロバイダー: {provider_name}\n"
            f"対応プロバイダー: openai, gemini"
        )


def list_available_providers() -> list:
    """利用可能なプロバイダーの一覧を取得
    
    Returns:
        プロバイダー名のリスト
    """
    return ["openai", "gemini"]


def get_provider_info(provider_name: str) -> dict:
    """プロバイダーの情報を取得
    
    Args:
        provider_name: プロバイダー名
        
    Returns:
        プロバイダー情報の辞書
    """
    info = {
        "openai": {
            "name": "OpenAI",
            "default_model": OpenAIProvider.DEFAULT_MODEL,
            "supported_models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo"
            ],
            "env_vars": {
                "api_key": "OPENAI_API_KEY",
                "model": "OPENAI_MODEL"
            }
        },
        "gemini": {
            "name": "Google Gemini",
            "default_model": GeminiProvider.DEFAULT_MODEL,
            "supported_models": [
                "gemini-2.0-flash-exp",
                "gemini-1.5-pro",
                "gemini-1.5-flash"
            ],
            "env_vars": {
                "api_key": "GEMINI_API_KEY",
                "model": "GEMINI_MODEL"
            }
        }
    }
    
    return info.get(provider_name.lower(), {})
