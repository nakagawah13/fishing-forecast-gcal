# <type>: <description>

<!--
例: feat: add data validation for input CSV files
例: model: improve defect detection with lag features
-->

## 変更概要

<!-- 何を変更したかを3-5項目で簡潔に記述 -->

- 
- 
- 

## 変更理由

<!-- なぜこの変更が必要か、背景や課題を記述 -->



関連Issue: #

## タスク対応

<!-- implementation_plan.md のタスク進捗を記載 -->

| Task ID | Epic | 状態 (Before → After) | 概要 |
|---------|------|----------------------|------|
| T-XXX |  | ⚪ → 🔵 or ✅ |  |

**更新対象ファイル**: `docs/implementation_plan.md`

**状態アイコン**: ⚪ Not Started / 🔵 In Progress / ✅ Done / ⏸️ Blocked / ❌ Cancelled

## 影響範囲

### 変更ファイル
- `path/to/file.py` - 
- 

### 依存モジュール
- `` - 動作確認済み / 影響あり

### 設定変更
- 

## テスト / 検証

| 種別 | 対象 | 結果 |
|------|------|------|
| ユニットテスト |  | ✅ Pass / ❌ Fail / N/A |
| 統合テスト |  | ✅ Pass / ❌ Fail / N/A |
| Lint | ruff check | ✅ Pass / ❌ Fail |
| 型チェック | pyright | ✅ Pass / ❌ Fail / N/A |

<!-- 失敗がある場合は詳細を記載 -->

## リスク / 互換性

| 項目 | 状態 |
|------|------|
| 破壊的変更 | なし / **あり** |
| 後方互換性 | 維持 / 非互換 |
| API変更 | なし / あり |
| 設定ファイル変更 | なし / あり |

<!-- 破壊的変更がある場合は詳細と移行方法を記載 -->

## 関連Issue / PR

- Closes #
- Refs #

---

## 実験結果（ML/AI PRのみ）

<!-- model/train/eval/data タイプのPRの場合は記載 -->

### 目的


### 評価指標

| モデル | Accuracy | Precision | Recall | F1 |
|--------|----------|-----------|--------|-----|
| Baseline |  |  |  |  |
| **Proposed** |  |  |  |  |
| 改善幅 |  |  |  |  |

### 考察

- 
- 

### 再現性情報

- **Random Seed**: 
- **Dataset**: 
- **Train/Test Split**: 
- **Git Tag**: `exp-xxx-v1`

---

## チェックリスト

- [ ] コミット漏れがないか確認 (`git status`)
- [ ] Lint/テストが通過 (`ruff check .`, `pytest`)
- [ ] 必須セクションをすべて記載
- [ ] ML/AI PRの場合、実験結果を記載
- [ ] `implementation_plan.md` のタスク状態を更新
- [ ] コミットメッセージがConventional Commits準拠
