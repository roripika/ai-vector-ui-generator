# アーキテクチャ設計思想 — AI画像生成 × UIエディター × ゲームエンジン統合

本ドキュメントは、ai-vector-ui-generator の**全体設計思想と各レイヤーの役割分担**を定義する。
AIエージェントや開発者が実装判断を行う際は、本文書を最初に参照すること。

---

## 1. 設計の核心思想

本システムは**3つのレイヤー**で役割を完全に分離する。

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: AI ビジュアル生成パイプライン（Python CLI）      │
│  「見た目」を作る責任を持つ                                │
│                                                         │
│  JSON Schema → Validator → SVG Compiler → Renderer      │
│                                     ↓                   │
│                            PNG / SVG / PDF               │
└─────────────────────────────────────────────────────────┘
          ↓ 生成された画像ファイルを渡す
┌─────────────────────────────────────────────────────────┐
│  Layer 2: UIエディター（Electron / viewer/）              │
│  「構造・配置・インタラクション」を管理する責任を持つ        │
│                                                         │
│  CocosStudio 相当の WYSIWYG エディター                    │
│  ・階層ツリー（親子関係）                                  │
│  ・相対座標 / アンカー固定                                 │
│  ・AI生成PNGを各コンポーネントにアタッチ                   │
│  ・JSONレイアウトから別のJSONレイアウトを参照（Prefab）     │
│                    ↓                                    │
│              レイアウトJSON（画面定義）                    │
└─────────────────────────────────────────────────────────┘
          ↓ レイアウトJSONを渡す
┌─────────────────────────────────────────────────────────┐
│  Layer 3: ゲームエンジン統合（Axmol / sdks/axmol/）       │
│  「実行時のUI生成」を管理する責任を持つ                     │
│                                                         │
│  UIJsonBuilder がレイアウトJSONを解釈して                  │
│  ゲームエンジン上にUIノードツリーを構築する                  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 各レイヤーの具体的な役割

### Layer 1: AI ビジュアル生成パイプライン

**何をするか**
- AIは `schema/ui_asset.schema.json` に従ったJSONのみを出力する
- JSONの内容に基づいて、Pythonコードが**決定論的に**SVGを生成する
- InkscapeまたはresvgでPNG/PDFに変換する

**AIは何をしてはいけないか**
- SVGタグ・path文字列を直接出力してはならない
- 乱数・時刻依存の値を使ってはならない（同一JSONから常に同じ画像を生成する）

**生成物の例**
```
out/button_normal.png        ← ボタン通常状態
out/button_pressed.png       ← ボタン押下状態
out/button_disabled.png      ← ボタン無効状態
out/window_frame.png         ← ウィンドウ背景
out/scrollbar_thumb.png      ← スクロールバーつまみ
out/hp_bar_fill.png          ← HPゲージ塗り
out/hp_bar_track.png         ← HPゲージ背景
```

**設計上の利点**
- 見た目の変更はJSONだけで完結する（エンジンコード不要）
- 同じコンポーネントで複数の世界観テーマを差し替えられる
- AIがデザインした内容が「数値・構造」として残るため、後から修正可能

---

### Layer 2: UIエディター（viewer/）

**何をするか**

エディターは「どのコンポーネントをどこに、どの親子関係で配置するか」を管理する。  
コンポーネントの**ビジュアルはAI生成PNGを参照するだけ**で、エディター自身は見た目を生成しない。

**コンポーネントの種類と画像アタッチ**

| コンポーネント | アタッチするAI生成画像 | 役割 |
|---|---|---|
| Sprite Button | `imageNormal`, `imagePressed`, `imageDisabled` | タップ可能なボタン |
| Image View | `imagePath` | 静的画像表示 |
| Window Panel | `imageBackground` | ウィンドウの背景枠 |
| Scroll Bar | `imageThumb`, `imageTrack` | スクロールバー |
| Slider | `imageTrack`, `imageThumb` | 値調整スライダー |
| Tab Bar Item | `imageNormal`, `imageSelected` | タブ切り替えUI |

**階層構造（CocosStudio相当）**

```
Screen (1280×720)
└── ModalPanel (600×380)  ← Window Panel: window_frame.png をアタッチ
    ├── TitleLabel         ← テキスト
    ├── ContentVBox        ← 縦並びレイアウトコンテナ
    │   ├── ListCell [0]   ← List Cell: list_cell_bg.png をアタッチ
    │   ├── ListCell [1]
    │   └── ListCell [2]
    └── FooterHBox         ← 横並びレイアウトコンテナ
        ├── CancelButton   ← Sprite Button: button_secondary.png をアタッチ
        └── OKButton       ← Sprite Button: button_primary.png をアタッチ
```

**アンカーシステム**

各コンポーネントは親コンテナまたはキャンバスに対して以下の方法で位置を決定する。

- `alignX: left | center | right | stretch` — 水平方向のアンカー
- `alignY: top | center | bottom | stretch` — 垂直方向のアンカー
- `x, y` — アンカー基点からのオフセット（ピクセル）

`stretch` を使うと親サイズに自動追従する（SafeArea対応などに使用）。

**Prefab（JSONレイアウトの再利用）**

`prefab` コンポーネントは `refPath` に別のレイアウトJSONのパスを指定することで、  
**レイアウトJSON内に別のレイアウトJSON全体を展開**できる。

```
// 例: 複数画面で共通の「ショップ購入確認モーダル」を再利用
{
  "componentId": "prefab",
  "props": { "refPath": "layouts/confirm_modal.json" },
  "offset": { "x": 340, "y": 200 }
}
```

これにより、同じUIパーツを複数画面で管理せず、1箇所の変更で全体に反映される。

**エクスポートするJSON形式**

```json
{
  "version": "0.4.0",
  "assetType": "screen",
  "canvas": { "width": 1280, "height": 720 },
  "components": [
    {
      "id": "primary-button",
      "viewBox": [0, 0, 240, 64],
      "visualType": "sprite_button"
    }
  ],
  "instances": [
    {
      "id": "ok-btn",
      "componentId": "primary-button",
      "offset": { "x": 800, "y": 600 },
      "size": { "width": 240, "height": 64 },
      "props": {
        "imageNormal": "out/button_primary_normal.png",
        "imagePressed": "out/button_primary_pressed.png",
        "text": "決定"
      },
      "zIndex": 10
    }
  ]
}
```

---

### Layer 3: ゲームエンジン統合（sdks/axmol/）

**何をするか**

`UIJsonBuilder.cpp / .h` がレイアウトJSONを読み込み、  
Axmolエンジン（Cocos2d-x互換）のUIノードツリーを動的に構築する。

```cpp
auto screen = UIJsonBuilder::buildFromFile("layouts/shop_screen.json");
this->addChild(screen);
```

- `sprite_button` → `ui::Button` にPNG9スライスを適用
- `image-view` → `ui::ImageView`
- `scroll-view` → `ui::ScrollView`
- `v-box / h-box` → 子ノードを自動整列
- `prefab` → 参照JSONを再帰的にロード

---

## 3. 典型的なワークフロー

```
Step 1: ボタンのビジュアルデザイン
  AI → button_primary.json（JSONスキーマ）
  CLI → python -m src.cli render --in button_primary.json --out out/
  出力 → out/button_primary.png, out/button_primary.svg

Step 2: 状態違いのバリエーション生成
  AI → button_primary_pressed.json, button_primary_disabled.json
  CLI → 同様にレンダリング

Step 3: ウィンドウ背景の生成
  AI → window_frame.json（グラジエント・角丸・装飾など）
  CLI → out/window_frame.png

Step 4: エディターで画面を組む
  Electron Editor を起動
  Window Panel を配置 → imageBackground = "out/window_frame.png" をアタッチ
  Sprite Button × 2 を配置 → imageNormal / imagePressed をアタッチ
  VBox でコンテンツ領域を整列
  アンカーでSafeArea内に固定

Step 5: レイアウトJSONをエクスポート
  File → Export JSON → layouts/confirm_modal.json

Step 6: ゲームエンジンに組み込む
  UIJsonBuilder::buildFromFile("layouts/confirm_modal.json")
  → Axmol が実行時にUIノードを構築
```

---

## 4. 責任分離の原則

| 関心事 | 担当レイヤー | 担当しないレイヤー |
|---|---|---|
| グラジエント・装飾・色 | Layer 1 (AI + Python) | Layer 2, 3 |
| ボタンの押下エフェクト画像 | Layer 1 | Layer 2, 3 |
| コンポーネントの位置・サイズ | Layer 2 (Editor) | Layer 1, 3 |
| 親子関係・アンカー | Layer 2 | Layer 1, 3 |
| タッチイベント・状態遷移ロジック | Layer 3 (Engine) | Layer 1, 2 |
| アニメーション再生 | Layer 3 | Layer 1, 2 |

---

## 5. テーマ（世界観）の差し替え

同じレイアウトJSONを保ちつつ、ビジュアルだけを差し替えることで**複数テーマ**に対応できる。

```
layouts/shop_screen.json   ← 構造（変えない）

themes/fantasy/
  button_primary_normal.png
  window_frame.png

themes/sci-fi/
  button_primary_normal.png
  window_frame.png
```

エディターまたはUIJsonBuilderのロード時にテーマディレクトリを切り替えるだけで、  
全画面のビジュアルが一括変更される。

---

## 6. 未実装・今後の課題

| 課題 | 優先度 | 状態 | 説明 |
|---|---|---|---|
| エディター内アセットブラウザ | 高 | ✅ 実装済み | `out/` フォルダのPNGを一覧表示、クリックでコンポーネントにアタッチ |
| Prefab実ロード | 高 | ✅ 実装済み | エディター上で `refPath` のJSONを再帰的に展開して表示 |
| テーマ切り替えUI | 中 | 未着手 | エディター上でテーマディレクトリを選択してプレビュー |
| 9スライス（9-patch）対応 | 中 | 未着手 | ウィンドウ・ボタンの伸縮品質向上のためスライス情報をJSONに付加 |
| AIからエディターへの直接トリガー | 中 | 未着手 | エディター上で「このコンポーネントのビジュアルを生成」ボタン |
| Prefab循環参照の検出 | 低 | 未着手 | `refPath` が自己参照・循環する場合のエラー処理 |

---

## 7. 実装済み機能の設計記録

### 7-1. アセットブラウザ（Asset Browser）

**目的**: Layer 1 で生成したPNGをLayer 2 エディターに橋渡しする。

**実装方針**

Electron の IPC（Inter-Process Communication）を使い、Node.js メインプロセスのファイルシステム操作をレンダラーに安全に公開する。

```
Node.js main (main.js)
  ipcMain.handle('list-image-assets', handler)
      ↓ contextBridge (preload.js)
  window.api.listImageAssets(dir)
      ↓
  renderer.js — _refreshAssetBrowser()
      → サムネイルグリッドとして左パネル「アセット」タブに表示
```

**スキャン対象**
- `workspaceDir/` 直下の画像ファイル（`.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`）
- `workspaceDir/out/` — CLI出力の標準ディレクトリ

**アタッチUX設計**

単純なドラッグ&ドロップではなく、**クリック→コンテキストメニュー方式**を採用した。理由：
- コンポーネント種別によってアタッチ先プロパティが異なる（`imageNormal` / `imagePressed` / `imageDisabled` vs `imagePath`）
- どのプロパティに入れるかをユーザーが明示的に選択する必要がある

```
サムネイルクリック
  └── sprite-button が選択中 → [Normal] [Pressed] [Disabled] の選択肢
  └── image-view が選択中   → imagePath に直接アタッチ
  └── 未選択 / 非対応        → エラーメッセージ
```

**セキュリティ考慮**
- `contextBridge.exposeInMainWorld` 経由のみで Node.js API を公開（preload サンドボックス維持）
- ファイルパスはワークスペースディレクトリ配下のみを対象にし、任意パスへのアクセスを防ぐ

---

### 7-2. Prefab実ロード

**目的**: `componentId: "prefab"` のインスタンスを、参照先JSONの内容で透過的に展開する。

**実装方針**

`loadJSON()` → `flatten()` 内で `componentId === "prefab"` を検出したとき：

1. `inst.props.refPath` を `workspaceDir` からの相対パスとして解釈
2. `window.api.readJsonFile(absPath)` で参照JSONを非同期取得
3. 参照先の `components` を一時的に `TEMPLATES` に登録
4. 参照先の `instances` を再帰的に `flatten()`、親IDは呼び出し元の parentId を引き継ぐ
5. 参照インスタンス自身はエレメントとして追加せず、内容物だけを展開する

**非同期化の影響**

`flatten()` がファイルI/Oを伴うため `async/await` 化が必要になった。  
`loadJSON()` 全体を `async function` に変更し、呼び出し元の `_openWorkspaceFile()`、`btn-new-file` ハンドラも `await` で呼ぶよう修正した。

**IPC構成**

```
ipcMain.handle('read-json-file', async (_e, filePath) => {
  return { success: boolean, data?: object, error?: string }
})
```

戻り値は `{success, data}` オブジェクト。レンダラー側では `result.data` を取り出す。

**循環参照への対処（現状）**

現時点では循環参照の検出は未実装。  
A → B → A のような参照が発生するとスタックオーバーフローになる可能性があるため、  
将来的に「展開中のパスセット」で重複チェックを追加する。

---

### 7-3. UIサンプルの設計指針（examples/）

`examples/` 配下のJSONは動作確認・デザインリファレンス双方の役割を兼ねる。  
以下のルールに従い「実際のゲームUIに近い見た目」を維持すること。

**トークン使用の強制**

`style.fill` / `style.stroke` にはトークン名のみを使用する。  
リテラルカラー（`"#FF0000"`、`"rgba(0,0,0,0.5)"`）は `_resolve_fill()` が `"currentColor"` （黒）にフォールバックするため、意図した色が出ない。

```json
// ✗ 誤り: 結果は黒になる
"style": { "fill": "#1B1D2F" }

// ✓ 正しい
"style": { "fill": "ui.surface" }
```

**暗い背景の原則**

ゲームUIは基本的に暗いテーマ。キャンバス背景は `ui.surface`（`#1B1D2F`）を使う。  
白背景（`"fill": ""`など）のサンプルはレビュー対象外と見なす。

**テキストと背景のペア**

| 背景 | テキスト色 |
|---|---|
| `ui.surface` / ダーク系 | `ui.textPrimary` / `ui.textSecondary` |
| `ui.primaryGradient` | `ui.textPrimary` |
| `ui.accent`（オレンジ） | `ui.textDark` |

**layoutRow でのタブラベル問題**

`_append_layout_items` はアイテムごとのテキスト上書きをサポートしない。  
タブ・セルなど**アイテムごとにラベルが異なる**場合は、`layoutRow` を使わず  
**コンポーネントを個別定義して別 instance で配置**する。

```json
// ✗ 誤り: layoutRowで4タブを1コンポーネントから生成 → 全て同じラベルになる
// ✓ 正しい: tab-home / tab-quest / tab-battle / tab-shop を個別コンポーネントで定義
```
