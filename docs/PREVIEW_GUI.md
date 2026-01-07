# GUIプレビュー（MVP 2.0 最小構成）

## 技術選定（最小で動く構成）
- サーバー: Python標準ライブラリ（`http.server`）
- 変換: 既存の `compiler.compile_svg()` をそのまま使用
- フロント: 素のHTML/CSS/JS（ビルド不要）
- 依存: 追加なし（既存のPython環境のみ）

選定理由:
- 既存のJSON→SVGパイプラインを崩さずに流用できる
- 追加依存が不要で、即起動できる
- GUIは「確認と比較」に集中し、編集機能は後回しにできる

## 最小要件の実装範囲
- JSON読み込み→即プレビュー（SVG表示）
- クリック選択でID表示（screenはinstance→componentの対応も表示）
- A/B比較（2ペイン表示）
- ExportはCLIに委譲（UIにCLIコマンド表示）
- JSON Patch入力→適用→再レンダ（最小ループ）

## 起動方法
```bash
python -m src.preview
```
- デフォルトURL: `http://127.0.0.1:8000`
- ポート変更: `python -m src.preview --port 8080`

## Studio（Phase 1）
- `http://127.0.0.1:8000/studio.html`
- プロンプト入力 → テンプレ選択 → JSON/SVG 出力
- 生成JSONを `generated/` に保存し、再読み込み可能

### Studioの保存機能
- 保存名: `{assetType}_{templateId}_{yyyyMMdd_HHmmss}.json`
- tags入力: `ui-templates/_catalog/tags.yaml` の語彙に準拠
- 未登録タグは警告表示（保存は可能）

## 画面の使い方
- Panel A/BでJSONファイルを読み込む
  - ファイル選択 または パス入力（例: `examples/screen_dialog.json`）
- クリックした要素のIDを表示
- Split Viewで2ペインの表示を切り替え
- Patch欄にJSON Patchを入力して適用
  - `Apply Patch → A`: Aに適用
  - `Apply Patch → B (from A)`: Aをベースにパッチを当ててBへ描画
  - `Save Patch`: パッチJSONを保存
- 語彙ガイドは `docs/SCHEMA_FIELD_RULES.md` を参照

## API（内部）
- `POST /api/compile`
  - 入力: `{ "asset": <json> }` または `{ "path": "path/to/file.json" }`
  - 出力: `{ "svg": "...", "asset": { ... } }`

## 既知の制限
- GUI上の編集は未対応
- component id は instance id から推定（screenのみに対応）
- ExportはCLI実行が前提
- JSON Patchは add/replace/remove のみ対応

## 次の拡張候補
- component/role/importanceの可視化
- Before/Afterの差分ハイライト
- 画面内検索（id/role）
- JSON patch適用と履歴
