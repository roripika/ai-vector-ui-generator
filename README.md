# AIベクターUIジェネレーター

AIが出力したJSON設計書を、決定論的にSVG/PDFおよび透過PNGへ変換するCLIファーストのツールチェーンです。`docs/REQUIREMENTS.md`に定義された制約を順守し、AIはJSONのみを書き、SVG生成はプログラム側で制御します。

## 主要コンセプト
- **単一情報源としてのJSON**: `schema/ui_asset.schema.json`が座標・スタイル・効果の契約を定義し、有限数値レンジやトークン参照を強制します。
- **Validator → Compiler → Renderer**: `JSON → SVG → PNG`のパイプラインを固定し、再現性と監査可能性を担保します。
- **トークン駆動スタイル**: 色/グラデーション/グローはトークンで参照し、コンパイラが実際のSVG定義に展開します。

## セットアップ手順
1. Python 3.11+ を用意し、仮想環境を構築します。
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. （任意）レンダラーバックエンドとして [Inkscape](https://inkscape.org) または [resvg](https://github.com/RazrFalcon/resvg) をインストールします。
3. サンプルアセットの検証:
   ```bash
   python -m src.cli validate examples/button_sf.json
   ```
4. JSONをSVGへコンパイル:
   ```bash
   python -m src.cli compile examples/button_sf.json --svg build/button.svg
   ```
5. SVGをPNG/PDFへレンダリング:
   ```bash
   python -m src.cli render --svg build/button.svg --png build/button.png --backend inkscape
   ```

## ディレクトリ構成
- `docs/` – 要件定義およびエージェントガイド。
- `schema/` – バリデータが利用する正式なJSON Schema。
- `src/validator/` – SchemaローダーとJSONバリデーションユーティリティ。
- `src/compiler/` – JSONから決定論的にSVGを組み立てるコンパイラとトークンレジストリ。
- `src/renderer/` – Inkscape / resvg CLIラッパー。
- `src/cli.py` – Validator → Compiler → Renderer を統括するエントリーポイント。
- `examples/` – 回帰テストおよび検証用のJSONアセット。

## 次のアクション例
- pytestを導入し、`src/validator`やコンパイラの異常系テストを追加する。
- トークン辞書とスキーマを拡張し、新たなボタン状態やアセット種別に対応する。
- Inkscape/resvgレンダリングをCIパイプラインに組み込み、PNGハッシュで回帰検知する。
