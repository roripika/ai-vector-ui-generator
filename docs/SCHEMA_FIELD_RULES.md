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
`constraint_flags`（配列）と `constraint_params`（オブジェクト）を基本とする。

### constraint_flags（タグ式）
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
- `snap_steps`: スナップ段数（ダイヤル/スライダー）
- `drag_angle_range`: ドラッグ角度範囲
- `max_lines`: 行数制限

**例**
- `constraint_flags: ["min_tap", "safe_area"]`

### constraint_params（詳細指定）
- 例: `{ "min_tap": { "width": 44, "height": 44 }, "safe_area": "inside" }`
- 詳細設計は次フェーズで拡張

### 旧 constraints（互換運用）
- `constraints` は **配列/オブジェクト** として引き続き受理するが **非推奨**。
- 旧形式は読み込み時に `constraint_flags` / `constraint_params` に正規化して扱う。
- 新規作成では `constraint_flags` / `constraint_params` のみを使用する。

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

---

## タグ運用ルール（decoration / fx_*）
- `tag: decoration` は **role=decoration 専用** とする
- ボタン等の「装飾付き」は `fx_*` タグで表現する
  - 例: `fx_glow`, `fx_shine`
- `fx_*` は `ui-templates/_catalog/tags.yaml` の `fx_tags` に追加して管理する

### 簡易lint
- `python scripts/lint_templates.py`
  - `tag: decoration` と `role` の不一致を警告する

---

## 語彙メンテ手順（tags/indexの運用）

### 1. 語彙追加の条件（ポリシー）
- 既存語彙で表現できない **明確な新概念** があるときのみ追加
- 追加前に **既存の近似語彙との差分** を説明できること
- UIテンプレやサンプルで **実際に使う見込み** があること

### 2. 追加手順（必須フロー）
1. 追加提案（目的・差分・利用例を記載）
2. レビュー（最低1名。語彙ブレの有無を確認）
3. `ui-templates/_catalog/tags.yaml` を更新
4. `ui-templates/_catalog/index.yaml` と関連テンプレを更新
5. 例を **examples/ または ui-templates/patterns/** に反映
6. テスト実行（`python -m pytest`）

### 3. 禁止事項
- 同義語の追加（例: `primary` と `main` を両方追加）
- 自由タグの増殖（思いつきで語彙を増やさない）
- `custom:*` の乱用（恒常利用は語彙へ昇格させる）

### 4. バージョニング方針
- 既存語彙の **破壊的変更は禁止**
- 変更が必要な場合は `deprecated:<old>` で移行期間を設ける
- `index.yaml` の summary は **互換性に影響しない** ため自由に更新可

---

## custom:* / unknown の運用

### 使用条件
- `custom:*` は **標準語彙に存在しない新概念** の暫定記述に限る
- `unknown` は **レビュー前の一時的な空欄埋め** に限る
- 期限を決めて **見直し対象** にする（例: 次のレビューで精査）

### 禁止事項
- `custom:*` をデフォルトにしない
- 同義語の乱立を避ける（既存語彙に寄せる）
- `unknown` を恒常運用しない

### 昇格ルール
1. `custom:*` が継続利用される場合、語彙として採用するか判断
2. 採用する場合は `tags.yaml` / `index.yaml` / schema を更新
3. 採用しない場合は **削除または既存語彙へ置換**
4. 変更後に **サンプル/テンプレ/テストを更新**
