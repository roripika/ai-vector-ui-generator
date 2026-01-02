# GitHub Copilot 指示書

このプロジェクトでGitHub Copilotを使用する際の重要なガイドラインです。

## プロジェクト概要
AIベクトルUI生成ツール - JSONスキーマからSVG/PNG/PDFを生成するシステム

## 必須ルール

### 1. AIはSVGを直接生成しない
- すべてのUIアセットは`schema/ui_asset.schema.json`で定義されたJSONスキーマで表現
- SVG生成は`src/compiler`でのみ実行
- JSON内にSVGタグやSVG文字列を直接記述することは禁止

### 2. 仮想環境の使用
- **重要**: コマンド実行前に必ず仮想環境をアクティベート
  ```bash
  source .venv/bin/activate
  ```
- または、ワンライナーで実行:
  ```bash
  source .venv/bin/activate && python3 -m src.cli [command]
  ```

### 3. スキーマファースト開発
- 機能追加・変更時は必ず`schema/ui_asset.schema.json`を最初に更新
- 更新順序: Schema → Validator → Compiler → Renderer

### 4. 実装フロー
1. Schema更新（仕様追加時）
2. Validator更新（`src/validator/validate.py`）
3. Compiler実装（`src/compiler/compile.py`, `src/compiler/tokens.py`）
4. Renderer拡張（`src/renderer/`）
5. CLIテスト（`python -m src.cli`）

### 5. コーディング規約
- スタイル値はトークン名で参照（例: `ui.primaryGradient`）
- リテラルカラーをJSON内に直接記述しない
- 数値は有限値で小数2桁まで
- 決定論的な生成（乱数・時刻依存処理禁止）

## 参照ドキュメント
- `docs/REQUIREMENTS.md`: 詳細仕様
- `docs/AGENT_GUIDE.md`: AIエージェント向けガイド
- `docs/INITIAL_TASKS.md`: 初期タスク定義

## CLIコマンド例
```bash
# バリデーション
python -m src.cli validate --file examples/button_sf.json

# レンダリング
python -m src.cli render --in examples/button_sf.json --out out/
```

## 禁止事項
- SVG文字列を直接生成・記述
- Schema未定義の構造を暗黙的に処理
- 仮想環境外でのコマンド実行
- 既存ディレクトリ構成の無断変更
