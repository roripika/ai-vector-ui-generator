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

    def generate_image(self, prompt: str, output_path: str) -> str:
        """プロンプトから画像を生成して保存"""
        from pathlib import Path
        try:
            # 最新の画像生成モデルを利用(環境やライブラリ更新による可用性に注意)
            try:
                # パッケージが対応している場合の標準イメージAPI
                model = self.genai.ImageGenerationModel("imagen-3.0-generate-001")
                result = model.generate_images(
                    prompt=prompt,
                    number_of_images=1,
                    aspect_ratio="1:1"
                )
                if not result.images:
                    raise AIProviderError("画像が生成されませんでした")
                image = result.images[0]
                
                # output_pathのディレクトリを準備
                out_file = Path(output_path)
                out_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 画像の保存 (PIL Image オブジェクトと想定)
                image.save(str(out_file))
                
                return f"file://{out_file.resolve()}"
            except AttributeError:
                # google.generativeai バージョンによって ImageGenerationModel が存在しない場合へのフォールバック等があればここに追加
                raise AIProviderError("APIクライアントが画像生成をサポートしていません。SDKをアップデートしてください")
        except Exception as e:
            raise AIProviderError(f"画像生成に失敗しました: {e}")
