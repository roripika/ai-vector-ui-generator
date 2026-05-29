"""OpenAI API連携プロバイダー"""

import json
import time
from typing import Any, Dict, Optional

from .base import AIProviderError, BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    """OpenAI APIを使用したプロバイダー
    
    GPT-4o, GPT-4o-miniなどのモデルをサポート。
    JSON modeで確実な構造化出力を実現。
    """
    
    DEFAULT_MODEL = "gpt-4o-mini"
    
    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        super().__init__(api_key, model or self.DEFAULT_MODEL, **kwargs)
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise AIProviderError(
                "openaiライブラリがインストールされていません。"
                "pip install openai を実行してください。"
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
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                if not content:
                    raise AIProviderError("空のレスポンスが返されました")
                
                # JSONをパース
                data = json.loads(content)
                
                # 基本構造を検証
                if not self._validate_json_structure(data):
                    raise AIProviderError(
                        "生成されたJSONが必須フィールドを含んでいません"
                    )
                
                # メタデータを追加
                if "metadata" not in data:
                    data["metadata"] = {}
                data["metadata"]["generated_from_prompt"] = prompt
                data["metadata"]["ai_provider"] = "openai"
                data["metadata"]["ai_model"] = self.model
                
                return data
                
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise AIProviderError(f"JSONのパースに失敗しました: {e}")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
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
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                if not content:
                    raise AIProviderError("空のレスポンスが返されました")
                
                # JSONをパース
                data = json.loads(content)
                
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
                    "ai_provider": "openai",
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
                    time.sleep(1)
                    continue
                raise AIProviderError(f"修正に失敗しました: {e}")
        
        raise AIProviderError(f"{max_retries}回のリトライ後も修正に失敗しました")

    def generate_image(self, prompt: str, output_path: str) -> str:
        """プロンプトから画像を生成して保存 (DALL-E 3)"""
        import urllib.request
        from pathlib import Path
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            if not image_url:
                raise AIProviderError("画像のURLが取得できませんでした")
                
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            
            urllib.request.urlretrieve(image_url, str(out_file))
            
            return f"file://{out_file.resolve()}"
        except Exception as e:
            raise AIProviderError(f"画像生成に失敗しました: {e}")
