"""AI連携モジュール

複数のAIプロバイダー(OpenAI, Gemini等)を統一インターフェースで扱う。
"""

from .base import BaseAIProvider, AIProviderError
from .factory import create_provider, list_available_providers, get_provider_info

__all__ = [
    "BaseAIProvider",
    "AIProviderError",
    "create_provider",
    "list_available_providers",
    "get_provider_info"
]
