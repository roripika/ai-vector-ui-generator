# AGENT_GUIDE

AIエージェントが本リポジトリを操作する際の必須ルールを以下にまとめます。

> **重要**: 実装着手前に必ず [`docs/ARCHITECTURE_PIPELINE.md`](ARCHITECTURE_PIPELINE.md) を読んでください。
> 本システムが「AI画像生成」「UIエディター」「ゲームエンジン統合」の3レイヤーに分離されている理由と
> それぞれの責任境界が記載されています。

## 基本原則
1. **AIはSVGを直接生成しない** – すべてのUIアセットは独自JSONスキーマで表現し、`src/compiler`でのみSVGを構築します。
2. **JSONスキーマを唯一の契約とする** – スキーマを更新せずにJSON構造を変えることは禁止です。変更が必要な場合は`schema/ui_asset.schema.json`を最初に更新し、Validator→Compiler→Rendererの順で反映します。
3. **CLIファースト** – 追加機能や検証は必ずCLI経由で実行可能な形にします。GUIは後回しにしてください。
4. **決定論的な生成** – 同一JSONから常に同じSVG/PDF/PNGが得られるよう、乱数や時刻依存処理は禁止です。

## 実装フロー
1. **Schema確定**: 仕様を拡張する際はまずSchemaを更新し、必須/範囲/列挙値を明示します。
2. **Validator更新**: Schema変更後は`src/validator`を更新し、異常値チェックや追加検証を実装します。
3. **Compiler実装**: 新しいレイヤーやエフェクトをサポートするときは`src/compiler`と`src/compiler/tokens.py`を更新し、トークン駆動でSVGを生成します。
4. **Renderer拡張**: 書き出し形式が増える場合は`src/renderer`にバックエンドを追加し、CLIサブコマンドへ統合します。
5. **CLIテスト**: `python -m src.cli ...`での操作を必ず確認し、READMEやドキュメントへ手順を追記します。

## コーディング指針
- スタイル値はトークン名（例: `ui.primaryGradient`）で参照し、リテラルカラーやSVGタグをJSON内へ直接記述しない。
- 数値は有限値かつ小数2桁まで。viewBox基準の座標を守り、範囲逸脱時はValidatorで検知させる。
- 追加ファイルはASCIIを基本とし、コメントは必要最小限で明瞭に記載する。

## エディター（viewer/）の拡張ルール

### IPC追加パターン
Electron エディターに新機能を追加する場合は、以下の3ファイルをセットで変更する。  
単独で変更してもレンダラーからアクセスできない。

| ファイル | 役割 | 変更内容 |
|---|---|---|
| `viewer/main.js` | Node.js メインプロセス | `ipcMain.handle('channel-name', handler)` を追加 |
| `viewer/preload.js` | セキュリティブリッジ | `contextBridge.exposeInMainWorld` に `window.api.methodName` を追加 |
| `viewer/renderer.js` | UIロジック | `await window.api.methodName(...)` で呼び出す |

### `readJsonFile` の戻り値形式
`window.api.readJsonFile(filePath)` は `{ success: boolean, data?: object, error?: string }` を返す。  
レンダラー側では必ず `result.success` を確認してから `result.data` を使うこと。

```js
// ✓ 正しい
const result = await window.api.readJsonFile(path);
if (!result || !result.success) return;
await Editor.loadJSON(result.data);

// ✗ 誤り: result自体をJSONとして渡してしまう
Editor.loadJSON(await window.api.readJsonFile(path));
```

### `loadJSON` は async
`editor.js` の `loadJSON(data)` は Prefab の非同期展開のため `async function` になっている。  
呼び出し元は必ず `await Editor.loadJSON(data)` とすること。

### アセットブラウザの動作
ワークスペースを開いたとき、または「↻ 更新」ボタンを押したとき、  
`workspaceDir/` と `workspaceDir/out/` の画像ファイル（`.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`）を一覧表示する。  
サムネイルをクリックすると選択中コンポーネントの種別に応じてアタッチ先を選ぶメニューが出る。

## 運用ルール
- 依存追加は`requirements.txt`へ記載し、仮想環境でインストールする。
- ビルド成果物や仮想環境は`.gitignore`で無視し、コミット対象にしない。
- レンダラーはInkscape/resvgに限定し、新規ツールを導入する場合は理由と手順をドキュメント化する。

## ナレッジ更新
- 新しい運用手順や既知の制約が生じた場合は、READMEと本ガイドの該当箇所を必ず更新してください。

## 禁止事項
- SVG文字列・SVGタグをAI出力やJSON内に直接記述すること。
- Schema未定義の構造をCompilerで黙って吸収すること。
- 既存ディレクトリ構成を理由なく変更すること。
- `style.fill` にリテラルカラー（`"#RRGGBB"`、`"rgba(...)"`）を直接書くこと（トークン名を使うこと）。
- `loadJSON()` を `await` なしで呼び出すこと（Prefab展開が完了する前に描画が走る）。