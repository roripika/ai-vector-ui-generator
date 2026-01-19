"""AIプロバイダーの基底クラス"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIProviderError(Exception):
    """AI処理中のエラー"""
    pass


class BaseAIProvider(ABC):
    """AIプロバイダーの基底クラス
    
    すべてのAIプロバイダー(OpenAI, Gemini等)はこのインターフェースを実装する。
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        """初期化
        
        Args:
            api_key: APIキー
            model: 使用するモデル名(省略時はデフォルト)
            **kwargs: プロバイダー固有の設定
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs
    
    @abstractmethod
    def generate_from_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """プロンプトからUI素材のJSONを生成
        
        Args:
            prompt: ユーザーのプロンプト(世界観・意図)
            context: テンプレートカタログ等のコンテキスト情報
            temperature: 生成の多様性(0.0-1.0)
            max_retries: 失敗時のリトライ回数
            
        Returns:
            生成されたUI素材のJSON
            
        Raises:
            AIProviderError: 生成に失敗した場合
        """
        pass
    
    @abstractmethod
    def refine_asset(
        self,
        asset: Dict[str, Any],
        instruction: str,
        temperature: float = 0.5,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """既存のUI素材を修正指示に基づいて改善
        
        Args:
            asset: 既存のUI素材JSON
            instruction: 修正指示(自然言語)
            temperature: 生成の多様性(0.0-1.0)
            max_retries: 失敗時のリトライ回数
            
        Returns:
            修正後のUI素材JSON
            
        Raises:
            AIProviderError: 修正に失敗した場合
        """
        pass
    
    def _validate_json_structure(self, data: Dict[str, Any]) -> bool:
        """生成されたJSONの基本構造を検証
        
        Args:
            data: 検証するJSON
            
        Returns:
            有効な場合True
        """
        # 最低限の必須フィールドをチェック
        required_fields = ["assetType", "viewBox"]
        return all(field in data for field in required_fields)
    
    def _build_system_prompt(self) -> str:
        """システムプロンプトを構築
        
        Returns:
            システムプロンプト文字列
        """
        from .prompts import SYSTEM_PROMPT
        return SYSTEM_PROMPT
    
    def _build_generation_prompt(
        self,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成用プロンプトを構築
        
        Args:
            user_prompt: ユーザーのプロンプト
            context: コンテキスト情報
            
        Returns:
            完全なプロンプト文字列
        """
        from .prompts import build_generation_prompt
        return build_generation_prompt(user_prompt, context)
    
    def _build_refinement_prompt(
        self,
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
        from .prompts import build_refinement_prompt
        return build_refinement_prompt(asset, instruction)
