# Shape Reference

JSON spec の `layers[].shape` に指定できる shape タイプの一覧です。

---

## roundedRect

角丸矩形を描画します。ボタン背景・パネル・カードに使用。

```json
{
  "id": "my-rect",
  "shape": "roundedRect",
  "rect": { "x": 2, "y": 2, "width": 124, "height": 32, "radius": 10 },
  "style": {
    "fill": "ui.primaryGradient",
    "stroke": "ui.strokeLight",
    "strokeWidth": 1.5,
    "glow": "ui.softGlow"
  }
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `rect.x` | number | ✅ | 左上 X |
| `rect.y` | number | ✅ | 左上 Y |
| `rect.width` | number | ✅ | 幅 |
| `rect.height` | number | ✅ | 高さ |
| `rect.radius` | number | ✅ | 角丸半径 |
| `style.fill` | 定数名 | — | 塗り色（スタイル定数名） |
| `style.stroke` | 定数名 | — | 枠線色 |
| `style.strokeWidth` | number | — | 枠線の太さ |
| `style.glow` | 定数名 | — | グローエフェクト |

---

## text

テキストを描画します。ボタンラベル・スコア表示・UI 文字列に使用。

```json
{
  "id": "my-label",
  "shape": "text",
  "rect": { "x": 2, "y": 14, "width": 124, "height": 20 },
  "style": { "fill": "ui.textDark" },
  "text": {
    "value": "START",
    "font": "ui.fontPrimary",
    "size": 20,
    "maxLines": 1,
    "overflow": "clip",
    "fit": "none",
    "align": "center",
    "clipPadding": 2
  }
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `text.value` | string | ✅ | 表示するテキスト |
| `text.font` | 定数名 | ✅ | フォントの定数名 |
| `text.size` | number | ✅ | フォントサイズ (px) |
| `text.maxLines` | integer 1–6 | ✅ | 最大行数 |
| `text.overflow` | `"clip"` / `"ellipsis"` | ✅ | はみ出し処理 |
| `text.fit` | `"none"` / `"shrink"` | ✅ | 幅に合わせた縮小 |
| `text.align` | `"left"` / `"center"` / `"right"` | — | 横揃え（デフォルト: left） |
| `text.clipPadding` | number 0–20 | — | clipPath 上端の余裕 px（デフォルト: 2）。フォントの ascender が切れる場合に増やす |

> **注意**: テキストは `dominant-baseline="hanging"` で配置されます。`rect.y` がテキスト上端の基準になります。背景のハイライトレイヤーと重ならないよう `rect.y` を調整してください。

---

## gauge

ゲージ（HP バー・スタミナ・進捗）を描画します。

```json
{
  "id": "hp-gauge",
  "shape": "gauge",
  "rect": { "x": 10, "y": 10, "width": 60, "height": 60 },
  "style": { "fill": "ui.accent" },
  "track": "ui.surface",
  "shape_profile": "radial",
  "shape_params": {
    "thickness": 8,
    "start_angle": -90,
    "sweep": 360
  },
  "value": 0.75
}
```

| `shape_profile` | 説明 |
|-----------------|------|
| `radial`（デフォルト） | 円弧ゲージ |
| `segmented` | セグメント分割ゲージ |
| `polygon` | 多角形ゲージ |

---

## progressBar

横長の進捗バーを描画します。ローディング・ダウンロード進捗に使用。

```json
{
  "id": "loading-bar",
  "shape": "progressBar",
  "rect": { "x": 10, "y": 20, "width": 200, "height": 12 },
  "style": { "fill": "ui.primaryGradient" },
  "track": "ui.surface",
  "value": 0.6
}
```

---

## toggle

ON/OFF スイッチを描画します。設定画面のトグルに使用。

```json
{
  "id": "bgm-toggle",
  "shape": "toggle",
  "rect": { "x": 10, "y": 10, "width": 48, "height": 24 },
  "style": { "fill": "ui.accent" },
  "track": "ui.surface",
  "value": true
}
```

---

## badge

バッジ（数値・ラベル付き小アイコン）を描画します。通知数・ランクに使用。

---

## cooldownOverlay

クールダウン表示（扇形マスク）を描画します。スキルアイコンに重ねて使用。

---

## layoutRow / layoutColumn / layoutGrid

複数のコンポーネントを整列配置します（複合レイアウト用）。

---

## 共通フィールド

全ての shape に指定できるフィールドです。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `id` | string | レイヤー識別子（一意） |
| `name` | string | 表示名（任意） |
| `zIndex` | integer | 描画順（大きいほど手前） |
| `enabled` | boolean | false で非表示（デフォルト: true） |
