# 要件定義書（実装前確定版）
## AI駆動型ベクターUIアセット生成システム

---

## 0. 本書の目的（Codex向け明示）

本書は、
**「AIが生成したUIデザインを、編集可能なベクター素材（SVG/PDF）および高品質な透過PNGとして安定生成するCLI中心ツール」**
を実装するための要件定義である。

本ツールは **実験用プロトタイプではなく、再現性・拡張性・自動化を前提とした実用ソフトウェア** を目指す。

---

## 1. 設計思想（最重要）

### 1.1 基本原則（絶対に崩さない）
1. **AIはSVGを直接書かない**
2. **AIの出力は JSON のみ**
3. **SVGはプログラムが決定論的に生成**
4. **編集用フォーマットと使用用フォーマットを分離**
5. **CLIファースト（GUIは後付け可能）**

---

## 2. 全体アーキテクチャ

```
[AI (LLM)]
   ↓ JSON
[Validator]
   ↓ OK
[SVG Compiler]
   ↓ SVG
[Renderer]
   ├─ SVG / PDF（編集用）
   └─ PNG（透過・使用用）
```

---

## 3. コンポーネント定義

### 3.1 AI（設計者）

**責務**
- UIアセットを **独自JSONスキーマ** に従って設計する
- 座標・色・サイズ・装飾を論理的に記述する

**禁止事項**
- SVGタグの出力
- path文字列の直接生成
- filter / gradient の生SVG記述

---

### 3.2 JSON中間表現（Single Source of Truth）

#### 必須要件
- 数値は **有限値（NaN/Inf禁止）**
- 小数は **最大2桁**
- 全座標は viewBox 基準
- スタイルは **トークン参照**

#### 役割
- AIと実装コードの **唯一の契約**
- 将来の差し替え（別LLM・別レンダラー）を可能にする

---

### 3.3 Validator（Python）

**チェック項目**
- JSON Schema 準拠
- 数値範囲チェック
- viewBox 外逸脱チェック
- 最小サイズ・線幅チェック
- フィルタ安全領域チェック（Glow切れ防止）

**エラー設計**
- 機械可読なエラーJSONを返す
- AIへのリトライ入力として再利用可能

---

### 3.4 SVG Compiler（Python / TS）

**責務**
- JSON → SVG を決定論的に変換
- 以下を自動付与：
  - `filterUnits="userSpaceOnUse"`
  - 余白を含む filter 範囲
  - 整理された `<g>` レイヤー構造
  - ID・命名規則

**品質目標**
- Illustratorで開いたときに「編集可能」
- 人間が読めるSVG構造

---

### 3.5 Renderer（CLI）

#### MVP対応レンダラー
- **Inkscape CLI**
- **resvg（SVG→PNG高速変換）**

#### 出力種別
| 種別 | 用途 |
|----|----|
| SVG | 編集・再利用 |
| PDF | Illustrator受け渡し |
| PNG（RGBA） | 実利用アセット |

#### 要件
- 完全透過
- アンチエイリアス保持
- Glow / Blur 切れなし

---

## 4. MVPスコープ（最初に作るもの）

### 4.1 対応アセット種別（1つに絞る）
- **UIボタン（角丸＋グラデーション＋Glow）**

### 4.2 MVPで「やらないこと」
- PSD/AIネイティブ書き出し
- GUI（React）
- 複雑な自由曲線（最初は矩形＋円弧）

---

## 5. JSONスキーマ設計方針（概要）

```json
{
  "assetType": "button",
  "viewBox": [0, 0, 256, 64],
  "layers": [
    {
      "id": "base",
      "shape": "roundedRect",
      "rect": { "x": 8, "y": 8, "w": 240, "h": 48, "r": 12 },
      "style": {
        "fill": "ui.primaryGradient",
        "glow": "ui.softGlow"
      }
    }
  ]
}
```

※ 実際のスキーマは別途 `schema.json` として定義

---

## 6. 非機能要件

### 6.1 再現性
- 同一JSON → 同一SVG → 同一PNG

### 6.2 パフォーマンス
- バッチ処理前提
- Inkscapeは可能なら shell mode
- 1 SVG 複数ID書き出し対応

### 6.3 拡張性
- Renderer差し替え可能
- 新アセット種別を JSON 拡張で対応

---

## 7. Codexへの明示指示（重要）

Codexには以下を守らせる：

- **JSONスキーマを最初に定義**
- **Validator → Compiler → Renderer の順で実装**
- SVG文字列をAI生成ロジックに含めない
- CLIツールとして動作確認する

---

## 8. 初期ディレクトリ構成（提案）

```
vector-ui-generator/
├─ docs/
│  └─ REQUIREMENTS.md
├─ schema/
│  └─ ui_asset.schema.json
├─ src/
│  ├─ validator/
│  ├─ compiler/
│  ├─ renderer/
│  └─ cli.py
├─ examples/
│  └─ button_sf.json
└─ README.md
```

---

## 次の一手（おすすめ）

次はこの順が最短です：

1. **JSON Schema確定**
2. Validator実装（pytestで異常JSONを潰す）
3. SVG Compiler（固定テンプレ）
4. Inkscape CLIでPNG生成
5. resvg比較

---

### 次にできること
- ✅ **Codex用「最初のタスク分解プロンプト」作成**
- ✅ **MVP用JSONスキーマ完全版**
- ✅ **Validatorのテストケース雛形**
- ✅ **Inkscape / resvg 両対応Renderer設計**

どれからいきますか？  
個人的には **「① JSONスキーマ完全版 → Codex投入」** が一番きれいに進みます。
