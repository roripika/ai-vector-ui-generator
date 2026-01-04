# UIテンプレートライブラリ（最小構成）

目的: AIが「意味・制約・layout_refの意図」を参照できる思考素材を提供する。
テンプレ本文は **プロンプトへ直貼りしない**。

## ディレクトリ構成
- `_catalog/tags.yaml`: 固定語彙（role/importance/state/constraints/layout_ref）
- `_catalog/index.yaml`: テンプレ目録（summary + path）
- `patterns/`: 意味中心テンプレ

## 使い方（将来RAG運用の前提）
1. `index.yaml` で候補を絞る
2. 必要なテンプレだけ読み込む
3. `tags.yaml` の語彙に従って補正する

## 運用ルール
- 語彙は `docs/SCHEMA_FIELD_RULES.md` を準拠
- 追加語彙が必要な場合は `custom:<token>` を使う
- テンプレは「正解例」として更新する
