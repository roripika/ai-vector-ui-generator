# AIベクターUIジェネレーター

AIが出力したJSON設計書を、決定論的にSVG/PDFおよび透過PNGへ変換するCLIファーストのツールチェーンです。`docs/REQUIREMENTS.md` に準拠し、AIはJSONのみを書き、SVG生成は `src/compiler` が担当します。

## 特徴

- **AI連携**: OpenAI/Geminiを使って自然言語プロンプトからUI素材を生成
- **アセンブラ機能**: ベクター形状（金型）とAI生成画像（ペンキ）をSVGのクリッピングパスで合成可能に。
- **決定論的レンダリング**: 同じJSON → 同じSVG → 同じPNG
- **編集可能**: IllustratorやInkscapeで開いて編集可能なSVG出力
- **デザイナーフレンドリー**: ブラウザベースのUI Studio
- **テンプレートライブラリ**: ゲームUI向けの豊富なテンプレート

## セットアップ

簡易セットアップ（推奨）:
```bash
./setup.command
```
※ Homebrewが未導入の場合はインストールを試みます（管理者パスワードが必要になる場合があります）。

手動セットアップ:
1. Python 3.11+ を用意し、仮想環境を作成します。
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Inkscape をインストールします（PNG/PDF出力に必須）。

### AI連携のセットアップ

AI生成機能を使用する場合は、APIキーを設定します。

1. `.env.example` をコピーして `.env` を作成:
   ```bash
   cp .env.example .env
   ```

2. `.env` にAPIキーを設定:
   ```bash
   # OpenAIを使用する場合
   AI_PROVIDER=openai
   OPENAI_API_KEY=your-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   
   # Geminiを使用する場合
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your-api-key-here
   GEMINI_MODEL=gemini-2.0-flash-exp
   ```

3. または、UI Studioで直接設定することもできます（ブラウザのlocalStorageに保存されます）。

## 使い方

### UI Studio（推奨）

デザイナー向けのブラウザベースUI:

```bash
./Start\ Studio.command
```

または:

```bash
python -m src.preview
```

ブラウザで `http://127.0.0.1:8000/studio.html` を開きます。

**主な機能**:
- プロンプト入力でUI素材を生成
- AI設定（OpenAI/Gemini）
- 差分修正（生成後に自然言語で修正指示）
- プレビュー・保存・再読み込み

### CLI（従来の方法）

以下のコマンドで `examples/button_sf.json` を検証し、SVGとPNGを出力します。

```bash
python -m src.cli render --in examples/button_sf.json --out out/
```

出力されるファイル:
- `out/button_sf.svg`
- `out/button_sf.png`

オプション:
- `--only svg|png|pdf` : 単一形式のみ出力
- `--size WIDTHxHEIGHT` : PNG出力サイズを指定（例: `512x128`）
- `--backend inkscape|resvg` : PNG出力のバックエンド（resvgはPNGのみ対応）

## ディレクトリ構成

- `docs/` – 要件定義と運用ルール
- `schema/` – JSON Schema（Single Source of Truth）
- `src/ai/` – AI連携モジュール（OpenAI/Gemini）
- `src/validator/` – JSON検証ロジック
- `src/compiler/` – JSON → SVG コンパイラ
- `src/renderer/` – Inkscapeラッパー
- `src/preview/` – UI Studioサーバー
- `src/cli.py` – CLIエントリーポイント
- `ui-templates/` – テンプレートライブラリ
- `examples/` – サンプルJSON
- `generated/` – UI Studioで生成したファイル（git管理外）
- `out/` – CLI出力先（git管理外）

## テスト

```bash
python -m pytest
```

## ドキュメント

- [REQUIREMENTS.md](docs/REQUIREMENTS.md) - 設計思想と要件定義
- [MVP_2_0_SPEC.md](docs/MVP_2_0_SPEC.md) - UI Studio仕様
- [PREVIEW_GUI.md](docs/PREVIEW_GUI.md) - UI Studioの使い方
- [SCHEMA_FIELD_RULES.md](docs/SCHEMA_FIELD_RULES.md) - JSON仕様

## トラブルシュート

- `inkscape` コマンドが応答しない場合は、GUIを一度起動して初回セットアップを完了してください。
- `--backend resvg` を使う場合は `resvg` がPATHにあることを確認してください（PDF出力は非対応）。
- AI生成が失敗する場合は、APIキーが正しく設定されているか確認してください。
- AI生成が有効でない場合は、テンプレート選択にフォールバックします。
