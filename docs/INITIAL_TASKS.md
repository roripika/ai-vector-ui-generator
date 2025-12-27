# INITIAL_TASKS.md
## AI Vector UI Generator - Initial Tasks (MVP)

このドキュメントは、AIエージェント（Codex）が本リポジトリで最初に行う実装タスクを、順序付きで定義するものです。
必ず `docs/REQUIREMENTS.md` と `AGENT_GUIDE.md` のルールに従って作業してください。

---

## 0. ゴール（MVPの定義）

MVPでは、以下がローカル環境で動作すること：

- **入力**: `examples/button_sf.json`（独自JSON）
- **処理**: JSON → (validate) → SVG生成 → PNG書き出し
- **出力**:
  - `out/button_sf.svg`
  - `out/button_sf.png`（RGBA透過）
  - （任意）`out/button_sf.pdf`

**注意**: AI（エージェント）はSVGを直接生成しない。SVGは `src/compiler` が決定論的に組み立てる。

---

## 1. リポジトリ初期整備（安全に着手するための下準備）

### 1.1 ディレクトリ作成
以下のディレクトリが存在しなければ作成する：

- `docs/`
- `schema/`
- `src/`
  - `src/validator/`
  - `src/compiler/`
  - `src/renderer/`
- `examples/`
- `out/`（git管理外にする）
- `tests/`

### 1.2 .gitignore
`.gitignore` を作成し、少なくとも以下を無視する：

- `out/`
- `__pycache__/`
- `.venv/`, `venv/`
- `.pytest_cache/`
- `*.png`, `*.pdf`（※必要なら `out/` のみに限定でも可）

---

## 2. JSON Schema の確定（Single Source of Truth）

### 2.1 `schema/ui_asset.schema.json` を作成
MVPの対象は **ボタン** のみ。以下を最低限サポートする：

- `assetType`: `"button"` 固定（enum）
- `viewBox`: `[x, y, w, h]`（int）
- `layers`: 配列
  - `id`: string
  - `shape`: `"roundedRect"`（enum）
  - `rect`: `{x,y,w,h,r}`（number）
  - `style`:
    - `fill`: token string（例 `ui.primaryGradient`）
    - `stroke`（任意）: token string
    - `strokeWidth`（任意）: number
    - `glow`（任意）: token string（例 `ui.softGlow`）

**数値制約（必須）**
- すべて有限値（NaN/Inf禁止）
- 小数は最大2桁（Validatorでチェック）
- `w,h > 0`
- `r >= 0`

---

## 3. Validator 実装（Schema + 追加検証）

### 3.1 依存
- `jsonschema` を使用してよい（`requirements.txt` に追加）
- 追加依存は最小限にする

### 3.2 実装
- `src/validator/validate.py` を作成し、以下を提供：
  - `validate_asset(json_obj) -> None`（例外を投げる）
  - `ValidationError`（独自例外でも可）

### 3.3 追加検証（Schema外）
- 小数桁数（2桁まで）
- viewBox範囲の逸脱（rectが大幅に外に飛んでいないか）
- `strokeWidth >= 0`
- `rect.w/h` が小さすぎない（例: 1未満ならエラー）

### 3.4 テスト
- `tests/test_validator.py`
  - 正常JSONが通る
  - 破損JSON・異常値が落ちる（NaN、負の幅、過剰小数など）

---

## 4. Tokens 定義（スタイルを固定化してAIミスを防ぐ）

### 4.1 `src/compiler/tokens.py`
最低限、以下のトークンを定義（SVGのdefs生成で使用）：

- `ui.primaryGradient`
- `ui.softGlow`
- （任意）`ui.strokeLight`

**方針**
- トークン→SVG `<defs>` のテンプレを決定論的に生成する
- JSONに生のSVGタグや色値を入れない

---

## 5. SVG Compiler 実装（JSON → SVG）

### 5.1 生成物
- `src/compiler/compile.py` を作成し、以下を提供：
  - `compile_svg(json_obj) -> str`

### 5.2 SVG要件（MVP）
- `<svg>` は `viewBox` を正しく設定
- レイヤーは `<g id="...">` で分ける
- `roundedRect` は `<rect rx ry>` を使う（pathにしない）
- `glow` トークンが指定されていれば filter を適用

### 5.3 Glow切れ対策（必須）
- filter は `filterUnits="userSpaceOnUse"` を付与
- filter領域は十分な余白を取る（例: -20〜+20px相当）
- ぼかしが端で切れないことを最優先

---

## 6. Renderer 実装（SVG → PNG/PDF）

### 6.1 MVPレンダラー
まずは **Inkscape CLI** を優先（resvgは後段でも良い）

- `src/renderer/inkscape.py` を作成
  - `export_png(svg_path, png_path, width=None, height=None) -> None`
  - `export_pdf(svg_path, pdf_path) -> None`（任意）

**注意**
- Inkscapeが未インストールの場合に備え、エラーメッセージを分かりやすくする

---

## 7. CLI 実装（ユーザー操作点）

### 7.1 `src/cli.py`
以下のコマンドを提供：

- `python -m src.cli render --in examples/button_sf.json --out out/`
  - validate → svg → png（→pdf任意）

オプション（任意）
- `--only svg|png|pdf`
- `--size 512x128`（png出力サイズ）

---

## 8. examples を作る（MVP入力）

### 8.1 `examples/button_sf.json`
SF風のボタンとして最低限以下を含む：

- baseレイヤー（roundedRect）
- primaryGradient fill
- softGlow

---

## 9. READMEの最低限更新（嘘を書かない）

READMEは「現時点で動く内容のみ」記載する：

- MVPの目的
- renderコマンド
- 生成物の場所
- Inkscape依存

---

## 10. 完了条件（Definition of Done）

以下が満たされればMVP完了：

- `pytest` が通る
- `python -m src.cli render --in examples/button_sf.json --out out/` が成功
- `out/button_sf.svg` が生成される
- `out/button_sf.png` が透過付きで生成される（背景が透明）
- 同じJSONで再実行しても出力が同一（決定論的）

---

## 11. 禁止事項（再掲）

- AIがSVGを直接生成すること
- JSONに生SVGタグ/生パス/生色値を埋め込むこと
- Schema未定義の構造をCompilerで黙って処理すること
- 実装されていない機能をREADMEに書くこと
