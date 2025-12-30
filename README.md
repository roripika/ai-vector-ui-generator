# AIベクターUIジェネレーター

AIが出力したJSON設計書を、決定論的にSVG/PDFおよび透過PNGへ変換するCLIファーストのツールチェーンです。`docs/REQUIREMENTS.md` に準拠し、AIはJSONのみを書き、SVG生成は `src/compiler` が担当します。

## セットアップ
1. Python 3.11+ を用意し、仮想環境を作成します。
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Inkscape をインストールします（PNG/PDF出力に必須）。

## 使い方（MVP）
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

## ディレクトリ構成
- `docs/` – 要件定義と運用ルール
- `schema/` – JSON Schema（Single Source of Truth）
- `src/validator/` – JSON検証ロジック
- `src/compiler/` – JSON → SVG コンパイラ
- `src/renderer/` – Inkscapeラッパー
- `src/cli.py` – CLIエントリーポイント
- `examples/` – MVP入力例
- `out/` – 生成物出力先（git管理外）

## テスト
```bash
python -m pytest
```
