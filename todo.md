# TODO - ai-vector-ui-generator

このファイルは、プロジェクトの残作業を優先度順に整理したものです。

---

## 🎯 現在のフェーズ: MVP 2.0 - Phase 4（非戦闘UIパターンカタログ拡充）

---

## 📋 優先度: 高（短期 1-2週間）

### 1. 画面パターンテンプレート追加（Phase 4 継続）

#### 主要画面パターン（未実装）
- [ ] `home.yaml` - ホーム画面（上部バー＋中央コンテンツ＋下ナビ）
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成（`examples/home.json`）
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `shop.yaml` - ショップ画面
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成（`examples/shop.json`）
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `gacha.yaml` - ガチャ画面
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成（`examples/gacha.json`）
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `inventory.yaml` - 所持品画面
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成（`examples/inventory.json`）
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `quest_select.yaml` - クエスト選択画面
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成（`examples/quest_select.json`）
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `character_detail.yaml` - キャラクター詳細画面
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成（`examples/character_detail.json`）
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `party_edit.yaml` - パーティ編成画面
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成（`examples/party_edit.json`）
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `profile.yaml` - プロフィール画面
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成（`examples/profile.json`）
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `list_detail.yaml` - 一覧＋詳細画面
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成（`examples/list_detail.json`）
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

### 2. 操作系UIコンポーネント追加

- [ ] `range_slider_horizontal.yaml` - 水平スライダー
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `range_slider_vertical.yaml` - 垂直スライダー
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

### 3. ボタンバリエーション追加

- [ ] `secondary_button.yaml` - セカンダリボタン
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `ghost_button.yaml` - ゴーストボタン（枠線のみ）
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `toggle_button.yaml` - トグルボタン
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `checkbox.yaml` - チェックボックス
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `radio_button.yaml` - ラジオボタン
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `stepper.yaml` - ±ステッパー（数量調整）
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

---

## 📋 優先度: 中（中期 1ヶ月）

### 4. Studio Phase 2: AI差分修正ループ実装

- [ ] 修正指示入力UI実装
  - [ ] 自然言語入力フォーム追加
  - [ ] 対象コンポーネント選択UI
  - [ ] 修正タイプ選択（強調/弱める/変更等）

- [ ] JSON Patch生成機能
  - [ ] AIによる差分提案ロジック実装
  - [ ] JSON Patch形式での出力
  - [ ] 変更範囲の限定（安全性確保）

- [ ] パッチ適用・再レンダリング
  - [ ] パッチ適用エンドポイント実装
  - [ ] 適用後の自動再レンダリング
  - [ ] エラーハンドリング

- [ ] Before/After比較UI
  - [ ] 2ペイン比較表示の改善
  - [ ] 差分ハイライト機能
  - [ ] 変更箇所の視覚的強調

- [ ] 変更履歴管理
  - [ ] 履歴保存機能
  - [ ] Undo/Redo機能
  - [ ] 履歴一覧表示

### 5. メタ情報可視化機能

- [ ] component/role/importance表示
  - [ ] クリック選択時のメタ情報パネル
  - [ ] role別の色分け表示
  - [ ] importance別のバッジ表示

- [ ] コンポーネントツリー表示
  - [ ] 階層構造の可視化
  - [ ] ツリーからの選択機能
  - [ ] 折りたたみ/展開機能

- [ ] レイヤー構造の可視化
  - [ ] zIndex順の表示
  - [ ] レイヤーの表示/非表示切り替え
  - [ ] レイヤー順の確認

### 6. 通知・演出系コンポーネント追加

- [ ] `label_new.yaml` - NEWラベル
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `label_star.yaml` - ★強調ラベル
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `tutorial_highlight.yaml` - チュートリアル用ハイライト
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

- [ ] `reward_frame.yaml` - 報酬演出フレーム
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

### 7. リストアイテムバリエーション

- [ ] `list_cell_friend.yaml` - フレンド一覧セル
  - [ ] テンプレートYAML作成
  - [ ] example JSON作成
  - [ ] ゴールデンテスト追加
  - [ ] `index.yaml`に登録

---

## 📋 優先度: 低（長期 2-3ヶ月）

### 8. テンプレートライブラリ運用自動化

- [ ] AI分類スクリプト実装
  - [ ] テンプレート→tags.yaml語彙への自動マッピング
  - [ ] 同義語検出・統合ロジック
  - [ ] index.yaml自動生成スクリプト

- [ ] レビューワークフロー構築
  - [ ] 人間による分類確認UI
  - [ ] タグ語彙の追加提案フロー
  - [ ] 承認/却下プロセス

### 9. ドキュメント整備

- [ ] Studio使用ガイド（デザイナー向け）
  - [ ] 基本操作マニュアル
  - [ ] テンプレート選択ガイド
  - [ ] トラブルシューティング

- [ ] テンプレート作成ガイド（コントリビューター向け）
  - [ ] YAMLフォーマット説明
  - [ ] ベストプラクティス
  - [ ] レビュー基準

- [ ] API仕様書
  - [ ] `/api/compile`エンドポイント詳細
  - [ ] JSON Schema完全版
  - [ ] エラーコード一覧

### 10. テスト強化

- [ ] エッジケーステスト追加
  - [ ] viewBox逸脱ケース
  - [ ] 数値精度限界ケース
  - [ ] 複雑なネスト構造ケース

- [ ] パフォーマンステスト
  - [ ] 大量コンポーネント描画
  - [ ] バッチ処理性能測定
  - [ ] メモリ使用量測定

- [ ] 統合テスト
  - [ ] Studio全体フロー
  - [ ] CLI→Studio連携
  - [ ] エクスポート品質検証

### 11. 全画面パターン網羅（Phase 4完全達成）

- [ ] 実ゲームでの検証
  - [ ] 実際のソシャゲUI再現テスト
  - [ ] デザイナーフィードバック収集
  - [ ] 不足パターンの洗い出し

- [ ] パターンカタログ完成
  - [ ] 全主要画面パターン実装完了
  - [ ] ドキュメント化
  - [ ] サンプルギャラリー作成

---

## 📋 将来フェーズ（Phase 8以降 - スコープ外）

### 12. 解像度対応

- [ ] 解像度プリセット実装（FHD/QHD/4K）
- [ ] レスポンシブ対応
- [ ] DPI対応

### 13. ゲームエンジン連携

- [ ] Unity向け変換レイヤー
- [ ] Godot向け変換レイヤー
- [ ] Unreal Engine向け変換レイヤー

### 14. GUI高度編集機能

- [ ] ピクセル単位のドラッグ編集
- [ ] ビジュアルレイアウトエディタ
- [ ] リアルタイムプレビュー

### 15. アニメーション対応

- [ ] アニメーションタイムライン
- [ ] トランジション定義
- [ ] モーション書き出し

### 16. 高度なエクスポート

- [ ] PSD/AIネイティブ書き出し
- [ ] Lottie形式対応
- [ ] スプライトシート生成

---

## 📝 メモ

### 完了済みマイルストーン
- ✅ Phase 0: MVP基盤（button UI）
- ✅ Phase 1: 画面レイアウト土台（screen/instances）
- ✅ Phase 2: Text表示
- ✅ Phase 3: レイアウトプリミティブ（row/column/grid）
- ✅ Phase 5: 戦闘HUD対応（binding/progressBar）
- ✅ Phase 6: 決定論保証（ゴールデンテスト）
- ✅ Phase 7: 運用・拡張（theme切り替え）
- ✅ Studio Phase 1: 基本生成・プレビュー機能

### 現在のテンプレート数
- **23テンプレート**（2026-01-19時点）

### 次の重要マイルストーン
1. **Phase 4完了**: 全主要画面パターン実装（目標: 35-40テンプレート）
2. **Studio Phase 2完了**: AI差分修正ループ実装
3. **MVP 2.0完了**: デザイン業務が回る状態の実現

---

## 🔄 更新履歴

- 2026-01-19: 初版作成（Phase 4進行中の状態を反映）
