"""Google Gemini API連携プロバイダー"""

import json
import time
from typing import Any, Dict, Optional

from .base import AIProviderError, BaseAIProvider


class GeminiProvider(BaseAIProvider):
    """Google Gemini APIを使用したプロバイダー
    
    Gemini 2.0 Flash, Gemini 1.5 Proなどのモデルをサポート。
    JSON schemaによる構造化出力を実現。
    """
    
    DEFAULT_MODEL = "gemini-2.0-flash-exp"
    
    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        super().__init__(api_key, model or self.DEFAULT_MODEL, **kwargs)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
            self.model_instance = genai.GenerativeModel(self.model)
        except ImportError:
            raise AIProviderError(
                "google-generativeaiライブラリがインストールされていません。"
                "pip install google-generativeai を実行してください。"
            )
    
    def generate_from_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """プロンプトからUI素材のJSONを生成"""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_generation_prompt(prompt, context)
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        generation_config = {
            "temperature": temperature,
            "response_mime_type": "application/json"
        }
        
        for attempt in range(max_retries):
            try:
                response = self.model_instance.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                if not response.text:
                    raise AIProviderError("空のレスポンスが返されました")
                
                # JSONをパース
                data = json.loads(response.text)
                
                # 基本構造を検証
                if not self._validate_json_structure(data):
                    raise AIProviderError(
                        "生成されたJSONが必須フィールドを含んでいません"
                    )
                
                # メタデータを追加
                if "metadata" not in data:
                    data["metadata"] = {}
                data["metadata"]["generated_from_prompt"] = prompt
                data["metadata"]["ai_provider"] = "gemini"
                data["metadata"]["ai_model"] = self.model
                
                return data
                
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise AIProviderError(f"JSONのパースに失敗しました: {e}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)  # Geminiはレート制限が厳しいため少し長めに待つ
                    continue
                raise AIProviderError(f"生成に失敗しました: {e}")
        
        raise AIProviderError(f"{max_retries}回のリトライ後も生成に失敗しました")
    
    def refine_asset(
        self,
        asset: Dict[str, Any],
        instruction: str,
        temperature: float = 0.5,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """既存のUI素材を修正指示に基づいて改善"""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_refinement_prompt(asset, instruction)
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        generation_config = {
            "temperature": temperature,
            "response_mime_type": "application/json"
        }
        
        for attempt in range(max_retries):
            try:
                response = self.model_instance.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                if not response.text:
                    raise AIProviderError("空のレスポンスが返されました")
                
                # JSONをパース
                data = json.loads(response.text)
                
                # 基本構造を検証
                if not self._validate_json_structure(data):
                    raise AIProviderError(
                        "修正されたJSONが必須フィールドを含んでいません"
                    )
                
                # メタデータを更新
                if "metadata" not in data:
                    data["metadata"] = {}
                if "refinement_history" not in data["metadata"]:
                    data["metadata"]["refinement_history"] = []
                data["metadata"]["refinement_history"].append({
                    "instruction": instruction,
                    "ai_provider": "gemini",
                    "ai_model": self.model
                })
                
                return data
                
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise AIProviderError(f"JSONのパースに失敗しました: {e}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise AIProviderError(f"修正に失敗しました: {e}")
        
        raise AIProviderError(f"{max_retries}回のリトライ後も修正に失敗しました")
