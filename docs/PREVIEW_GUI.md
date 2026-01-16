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

## ダブルクリック起動（Mac）
- `Start Studio.command` をダブルクリックで起動
  - `.venv/bin/python` を優先して起動（なければ `python3`）
  - ブラウザで `http://127.0.0.1:8000/studio.html` を自動で開く
  - ログは `studio_server.log` に出力
- 停止は `Stop Studio.command` をダブルクリック

### 初回のみ必要なこと（権限/隔離）
- 実行許可が外れている場合:
  - `chmod +x "Start Studio.command" "Stop Studio.command"`
- macOSの隔離属性で起動できない場合:
  - `xattr -dr com.apple.quarantine "Start Studio.command" "Stop Studio.command"`
  - または Finder で右クリック → 開く

## Studio（Phase 1）
- `http://127.0.0.1:8000/studio.html`
- プロンプト入力 → テンプレ選択 → JSON/SVG 出力
- 生成JSONを `generated/` に保存し、再読み込み可能
- constraints は `constraint_flags` / `constraint_params` を編集可能（旧 `constraints` は読み込み時に正規化）

### Studioの保存機能
- 保存名: `{assetType}_{templateId}_{yyyyMMdd_HHmmss}.json`
- tags入力: `ui-templates/_catalog/tags.yaml` の語彙に準拠
- 未登録タグは警告表示（保存は可能）

## 動作確認チェックリスト（デザイナー向け）

### 0) 事前準備（初回のみ）
- [ ] `Start Studio.command` をダブルクリックできる（実行権限が付いている）
- [ ] 起動できない場合は隔離解除を実施（案内通り `xattr`）

### 1) 起動確認（CLI不要）
- [ ] `Start Studio.command` をダブルクリック
- [ ] ブラウザが開き、`Studio` 画面（`/studio.html`）が表示される
- [ ] すでに起動中の場合、再度ダブルクリックしても新規起動せずURLが開く

### 2) 生成フロー確認（Phase1）
- [ ] プロンプト欄に世界観/意図を入力して「Generate」
- [ ] テンプレ候補（選定理由・一致キーワード）が表示される
- [ ] 生成結果に 素材種別（例：button/modal/tab 等）が表示される
- [ ] 生成JSONに `generated_from_prompt / selected_templates / generator_version` が含まれる
- [ ] constraint_flags / constraint_params を編集して再レンダできる

### 3) 保存フロー確認（資産化）
- [ ] 保存名が自動提案される（編集できる）
- [ ] tags を入力でき、未登録タグは警告される
- [ ] 「Save」で保存できる（成功表示が出る）
- [ ] `generated/`（または保存先）にJSONが作成される

### 4) 再読み込み確認（運用の継続）
- [ ] 生成物一覧に保存したJSONが表示される
- [ ] 一覧から選んで再読み込みできる
- [ ] 再読み込み後もプレビュー/メタ情報表示が崩れない

### 5) ログとトラブルシュート（困ったらここ）
- [ ] ログは `studio_server.log` に出力される
- 動作確認で作られた `generated/` のファイルやログはコミットしない
- よくある原因：
  - ポート8000が他で使用中 → 先に `Stop Studio.command` を実行
  - Python環境がない/壊れている → `.venv` を作り直す、または `python3` を導入
  - 保存できない → 保存先ディレクトリ権限を確認

### 6) 停止確認
- [ ] `Stop Studio.command` をダブルクリック
- [ ] 「停止しました」ダイアログが出る
- [ ] `Start Studio.command` で再起動できる

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
