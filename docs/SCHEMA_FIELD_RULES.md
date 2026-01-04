# 追加フィールド運用ルール（MVP 2.0）

目的: `role` / `importance` / `state` / `constraints` / `layout_ref` を
自由記述ではなく管理された語彙で運用し、AI差分修正とテンプレ検索の安定性を高める。

---

## 共通ルール
- 文字列は **lower_snake_case** を基本とする
- 既存語彙に当てはまらない場合は `custom:<token>` を使う
  - 例: `custom:special_offer`, `custom:boss_phase`
- 意味が不明確なときは `unknown` を許容する

---

## role（UIの役割）
**許容値（基本語彙）**
- `action`: 主要アクション（CTA、決定ボタンなど）
- `navigation`: 画面遷移・タブ・ナビ
- `container`: パネル、カード、枠
- `data_display`: 数値/一覧など情報表示
- `feedback`: 通知・結果・状態変化の表示
- `decoration`: 装飾専用
- `text`: テキスト表示
- `icon`: アイコン表示
- `media`: 画像/サムネイル
- `control`: スライダー/トグルなど操作UI
- `status`: HP/MP/状態など
- `modal`: モーダル・ダイアログ
- `overlay`: 画面上の重ね要素
- `header`: ヘッダー領域
- `footer`: フッター領域
- `list`: リスト
- `grid`: グリッド
- `tab`: タブ
- `badge`: バッジ
- `progress`: プログレス/ゲージ
- `toggle`: トグル
- `input`: 入力UI

**例**
- `role: "action"`
- `role: "custom:promo_banner"`

---

## importance（重要度）
**許容値（基本語彙）**
- `primary`: 最重要
- `secondary`: 準重要
- `tertiary`: 補助
- `emphasis`: 強調
- `muted`: 目立たせない
- `info`: 情報提示
- `warning`: 注意
- `critical`: 危険/重大
- `decorative`: 装飾寄り

**例**
- `importance: "primary"`
- `importance: "custom:cta_level_2"`

---

## state（状態）
**許容値（基本語彙）**
- `default`
- `hover`
- `pressed`
- `disabled`
- `selected`
- `active`
- `focused`
- `loading`
- `success`
- `error`
- `warning`
- `cooldown`
- `locked`
- `expanded`
- `collapsed`
- `on`
- `off`

**例**
- `state: "disabled"`
- `state: "custom:rage"`

---

## constraints（制約）
`constraints` は **配列** または **オブジェクト** を許容。

### 配列（タグ式）
**標準キー例**
- `min_tap`: 最小タップ領域
- `safe_area`: セーフエリア内に収める
- `overlap`: 重なり許可/禁止
- `padding`: パディングあり
- `spacing`: 余白管理
- `nine_slice`: 9-slice前提
- `aspect_ratio`: 縦横比固定
- `hit_area`: 当たり判定拡張
- `baseline`: ベースライン整列
- `snap`: スナップ整列
- `max_lines`: 行数制限

**例**
- `constraints: ["min_tap", "safe_area"]`

### オブジェクト（詳細指定）
- 例: `{ "min_tap": { "width": 44, "height": 44 }, "safe_area": "inside" }`
- 詳細設計は次フェーズで拡張

---

## layout_ref（レイアウト参照）
座標を捨てず、**補助情報**として使う。
レイアウトエンジンがある場合のみ解釈する。

**最小仕様（文字列）**
- `slot:<id>`: slot基準
- `grid:<id>`: grid基準
- `flow:<id>`: flow/stack基準
- `stack:<id>`: 連続配置
- `list:<id>`: リスト項目基準

**例**
- `layout_ref: "slot:dialog_title"`
- `layout_ref: "grid:inventory_items"`
- `layout_ref: "custom:timeline"`

---

## 運用ガイド
- 迷ったら `unknown` を使い、後で整理する
- `custom:*` はチーム内で共有し、使い捨てにしない
- `role/importance/state` は AIパッチで一貫性を保つ

