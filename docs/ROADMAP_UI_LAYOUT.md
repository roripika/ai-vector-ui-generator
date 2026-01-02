# AI Vector UI Generator – UIレイアウト完全対応ロードマップ（Bルート）

最終ゴール：
- ソーシャルゲームで使われる **全画面パターン** を
- AIが **JSONのみでレイアウト設計**
- compiler が **決定論的に SVG / PNG / PDF を生成**
- 非戦闘UI + 戦闘HUDまでカバーする

---

## Phase 0: 現在地（完了済み）
- [x] button UI のMVP実装
- [x] JSON Schema を唯一の契約にする設計
- [x] validator / compiler / renderer / CLI 分離
- [x] Inkscape による PNG / PDF 出力
- [x] 決定論的SVG生成（※テスト強化は今後）

---

## Phase 1: 画面レイアウトの土台（最優先）

### 1. screen アセットの導入
- [x] `assetType: "screen"` を schema に追加
- [x] `canvas { w, h, safeArea? }` を定義
- [x] 画面全体を1つのSVGとして生成できるようにする
- [x] 既存 button/panel を複数配置可能にする

### 2. instances による配置モデル
- [x] `components`（部品定義）と `instances`（配置）を分離
- [x] `anchorTo`（親参照）を実装
- [x] `anchor: topLeft | center | bottomRight ...` を enum 化
- [x] `offset {x,y}` と `size {w,h}` で最終rectを決定
- [x] 描画順を決定論的に固定（zIndex → id順）

### 3. examples
- [x] `examples/screen_dialog.json`
  - ウィンドウ
  - OK / Cancel ボタン
- [x] `python -m src.cli render --in examples/screen_dialog.json --out out/`

---

## Phase 2: Text 表示（ゲームUI必須）

### 4. text widget（制約付き）
- [x] `shape: "text"` を schema に追加
- [x] フォントは token 固定（生フォント名禁止）
- [x] 以下のみ許可：
  - `maxLines`
  - `overflow: ellipsis | clip`
  - `fit: none | shrink`
- [x] 自動折り返しはルール固定 or 禁止
- [x] SVG text / textLength による決定論的描画

### 5. text を含む examples
- [x] ボタンラベル
- [x] ダイアログタイトル
- [x] 注意文 / 説明文

---

## Phase 3: レイアウトプリミティブ拡張（画面量産の鍵）

### 6. Layout primitives
- [x] `layoutRow`
  - padding / gap / align
- [x] `layoutColumn`
  - padding / gap / align
- [x] `layoutGrid`
  - cols / rowGap / colGap
- [x] ネスト可能にする

### 7. 一覧・グリッド画面
- [x] items 配列による反復描画
- [x] `examples/list_screen.json`
- [x] `examples/grid_screen.json`

---

## Phase 4: 非戦闘UI パターンカタログ

### 8. Pattern（テンプレ）設計
- [x] `patternId` を screen に追加
- [x] slots 方式（枠に何を入れるか）を定義

### 9. 最低限カバーするパターン
- [ ] home（上部バー＋中央＋下ナビ）
- [ ] tabs（上 or 下）
- [ ] list
- [ ] grid
- [ ] list_detail（一覧＋詳細）
- [ ] shop
- [ ] gacha
- [ ] quest_select
- [ ] character_detail
- [ ] party_edit
- [ ] inventory
- [ ] profile
- [x] dialogs（確認／報酬／エラー）

---

## Phase 5: 戦闘HUD対応（Bルート本丸）

### 10. Binding（状態バインド）
- [ ] widget に `bind` を追加
  - `bind.value`
  - `bind.visibleWhen`
  - `bind.enabledWhen`
- [ ] 条件式は最小限（gt / lt / eq / and / or）
- [ ] `mockState` を screen に定義可能にする

### 11. HUD向け widgets
- [ ] `progressBar`（HP / MP）
- [ ] cooldown overlay（矩形 or 円）
- [ ] toggle（auto / 倍速）
- [ ] badge（残り回数 / 通知）

### 12. HUD examples
- [ ] `examples/hud_basic.json`
- [ ] `examples/hud_basic.mock.json`
  - HP減少
  - スキルCD中
  - 無効状態

---

## Phase 6: 決定論保証と品質固定

### 13. ゴールデンテスト
- [ ] screen 全体の SVG ハッシュ固定
- [ ] 同一JSON → 同一SVG を pytest で保証
- [ ] layout / text / binding を含むケースを網羅

### 14. CI
- [ ] GitHub Actions で pytest 実行
- [ ] Inkscape 非依存テストと分離

---

## Phase 7: 運用・拡張（任意）

- [ ] theme 切り替え（色・余白・フォント差分）
- [ ] 解像度プリセット（FHD / QHD / 4K）
- [ ] Unity / Godot 向け変換レイヤー（将来）

---

## 最終定義（Done）
- [ ] ソシャゲで使われる主要画面パターンをすべて JSON で表現できる
- [ ] AIが「画面レイアウト設計」を担当できる
- [ ] 出力は常に決定論的
- [ ] ゲームUIとして実運用可能
