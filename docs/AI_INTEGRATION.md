# AI連携ドキュメント

このドキュメントでは、ai-vector-ui-generatorのAI連携機能について説明します。

## 概要

AI連携機能により、デザイナーは自然言語プロンプトからUI素材を生成し、差分修正を行うことができます。

### サポートされているプロバイダー

- **OpenAI** (GPT-4o, GPT-4o-mini)
- **Google Gemini** (Gemini 2.0 Flash, Gemini 1.5 Pro)

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、APIキーを設定します：

```bash
# AI Provider設定
AI_PROVIDER=openai  # openai | gemini

# OpenAI設定
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini  # gpt-4o | gpt-4o-mini | gpt-4-turbo

# Gemini設定
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp  # gemini-2.0-flash-exp | gemini-1.5-pro | gemini-1.5-flash
```

`.env.example`をコピーして使用することもできます：

```bash
cp .env.example .env
```

### 3. Studio UIでの設定

Studio UIを起動後、AI設定パネルで以下を設定できます：

- AI生成の有効化/無効化
- プロバイダーの選択（OpenAI / Gemini）
- APIキーの入力（ブラウザのlocalStorageに保存）
- モデルの選択

## 使い方

### プロンプトからの生成

1. Studio UIを起動：`./Start\ Studio.command`
2. AI設定パネルでAI生成を有効化
3. プロンプト入力欄に世界観や意図を記述
4. 「素材を生成」ボタンをクリック

**プロンプト例：**
- "神殿風の発光ボタン"
- "タブバー、未読バッジ付き"
- "モーダルで確認ダイアログ"
- "トースト通知、成功表示"

### 差分修正

生成後、差分修正パネルで修正指示を入力できます：

1. 修正指示入力欄に自然言語で指示を記述
2. 「修正を適用」ボタンをクリック

**修正指示例：**
- "ボタンをもっと強調して"
- "色を暗くして"
- "サイズを大きくして"

## プログラムからの使用

### 基本的な使い方

```python
from src.ai import create_provider

# プロバイダーを作成（環境変数から自動設定）
provider = create_provider()

# プロンプトから生成
asset = provider.generate_from_prompt("神殿風のボタン")

# 差分修正
refined_asset = provider.refine_asset(asset, "色を青に変更して")
```

### プロバイダーの明示的な指定

```python
from src.ai import create_provider

# OpenAIを使用
provider = create_provider(
    provider_name="openai",
    api_key="sk-...",
    model="gpt-4o-mini"
)

# Geminiを使用
provider = create_provider(
    provider_name="gemini",
    api_key="...",
    model="gemini-2.0-flash-exp"
)
```

### コンテキストの提供

テンプレートカタログやタグ情報をコンテキストとして提供できます：

```python
context = {
    "templates": [
        {
            "id": "button_sf",
            "intent": "主要アクションを強調するボタン",
            "when": ["CTAを目立たせたい"],
            "tags": ["action", "primary"]
        }
    ],
    "tags": ["action", "primary", "navigation"]
}

asset = provider.generate_from_prompt("ボタン", context=context)
```

## アーキテクチャ

### プロバイダー抽象レイヤー

```
src/ai/
├── base.py              # BaseAIProvider（基底クラス）
├── openai_provider.py   # OpenAIProvider
├── gemini_provider.py   # GeminiProvider
├── factory.py           # create_provider()
└── prompts.py           # プロンプトテンプレート
```

### API統合

Studio APIサーバー（`src/preview/server.py`）は以下のエンドポイントを提供：

- `POST /api/generate` - プロンプトからUI素材を生成
- `POST /api/refine` - 既存のUI素材を差分修正

### フォールバック機能

AI生成が失敗した場合、自動的にテンプレート選択にフォールバックします。

## プロンプトエンジニアリング

### 効果的なプロンプトの書き方

1. **具体的な世界観を記述**
   - ❌ "ボタン"
   - ✅ "神殿風の発光ボタン"

2. **意図を明確に**
   - ❌ "何か通知"
   - ✅ "非ブロッキング通知、成功表示"

3. **既存のテンプレートを参考に**
   - Studio UIの「選定結果」を確認
   - テンプレートの`intent`や`when`を参考にする

### システムプロンプト

AIには以下の設計思想が伝えられています：

1. **AIはSVGを直接書かない** - AIの出力はJSONのみ
2. **SVGはプログラムが決定論的に生成** - 同じJSON→同じSVG
3. **編集可能なベクター素材** - IllustratorやInkscapeで編集可能
4. **意味ベースの設計** - role/importance/state等のメタ情報を重視

## トラブルシューティング

### AI生成が失敗する

**原因：**
- APIキーが未設定または無効
- レート制限に達している
- プロンプトが不適切

**解決策：**
1. 環境変数またはUI設定でAPIキーを確認
2. しばらく待ってから再試行
3. プロンプトをより具体的に記述

### 生成されたJSONが無効

**原因：**
- AIが必須フィールドを含めていない
- JSON構造が不正

**解決策：**
1. 温度パラメータを下げる（0.3-0.5）
2. プロンプトをより明確に記述
3. コンテキスト情報を提供

### 差分修正が期待通りに動作しない

**原因：**
- 修正指示が曖昧
- AIが意図を誤解

**解決策：**
1. 修正指示をより具体的に記述
2. 複数回に分けて修正
3. 温度パラメータを調整

## セキュリティ

### APIキーの取り扱い

- APIキーは`.env`ファイルで管理（`.gitignore`に含まれる）
- Studio UIではlocalStorageに保存（ブラウザローカルのみ）
- 本番環境では環境変数のみを使用することを推奨

### ベストプラクティス

1. APIキーをコードに直接記述しない
2. `.env`ファイルをバージョン管理に含めない
3. 定期的にAPIキーをローテーション
4. レート制限を監視

## パフォーマンス

### トークン数の最適化

- テンプレートカタログは最大10件に制限
- タグ情報は最大20件に制限
- 不要なコンテキスト情報は省略

### レート制限対応

- リトライロジックを実装（最大3回）
- Geminiは待機時間を長めに設定（2秒）
- エラーハンドリングで適切にフォールバック

## 新しいプロバイダーの追加

1. `src/ai/`に新しいプロバイダークラスを作成
2. `BaseAIProvider`を継承
3. `generate_from_prompt`と`refine_asset`を実装
4. `factory.py`に登録

**例：**

```python
from .base import BaseAIProvider

class ClaudeProvider(BaseAIProvider):
    DEFAULT_MODEL = "claude-3-opus"
    
    def generate_from_prompt(self, prompt, context=None, temperature=0.7, max_retries=3):
        # 実装
        pass
    
    def refine_asset(self, asset, instruction, temperature=0.5, max_retries=3):
        # 実装
        pass
```

## 参考リンク

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [プロジェクトREADME](../README.md)
- [デザイナー向けワークフロー](DESIGNER_WORKFLOW.md)
