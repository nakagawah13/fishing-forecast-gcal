# Issue #69: JMA推算テキストパーサーをscripts/からテスト支援モジュールに分離

## ステータス
⚪ In Progress

## 概要
`scripts/fetch_jma_suisan_tide_data.py` は気象庁推算テキストのダウンロード用臨時スクリプトだが、統合テスト (`tests/integration/infrastructure/test_tide_prediction_against_jma_suisan.py`) が `parse_jma_suisan_text` 関数を直接インポートしており、テストインフラがパッケージ外の臨時スクリプトに依存している。

## 問題点
1. **テストコードがscripts/に直接依存**: `from scripts.fetch_jma_suisan_tide_data import parse_jma_suisan_text` というインポートにより、臨時スクリプトがテストインフラの構成要素になっている
2. **責務の混在**: `parse_jma_suisan_text` (パースロジック) と `fetch_suisan_text` (HTTPダウンロード) が同一ファイルに同居
3. **パッケージ外依存**: `scripts/` は `src/fishing_forecast_gcal/` の外にあり、インポートパスの安定性が低い
4. **テストの脆弱性**: スクリプトのリファクタリングや削除でテストが壊れるリスク

## 影響範囲
- `scripts/fetch_jma_suisan_tide_data.py` (パースロジックの分離)
- `tests/integration/infrastructure/test_tide_prediction_against_jma_suisan.py` (インポートパスの変更)

## 実装方針

### 採用案: テスト支援モジュールとして `tests/` 配下に移動
`parse_jma_suisan_text` と `JMASuisanDaily` はテスト時のみ使用されるため、`tests/` 配下にテスト支援ユーティリティとして配置する。

#### ディレクトリ構造
```
tests/
  support/
    __init__.py
    jma_suisan_parser.py  # parse_jma_suisan_text, JMASuisanDaily を移動
```

#### 理由
- 現状、パースロジックはテストでのみ使用されている
- 本番コード (`src/`) では使用されていない
- 将来的に必要になれば、その時点で `src/` に格上げ可能

## 具体的な変更内容

### 1. `tests/support/jma_suisan_parser.py` (新規作成)
以下を `scripts/fetch_jma_suisan_tide_data.py` から移動:
- `JMASuisanDaily` データクラス
- `parse_jma_suisan_text` 関数
- `_parse_time_height_block` 関数
- 関連する定数 (LINE_LENGTH, HIGH_BLOCK_START, LOW_BLOCK_START, etc.)

#### モジュールdocstring
```python
"""JMA Suisan text parser for testing.

This module provides parsing utilities for JMA tide prediction (suisan) text files.
It is used exclusively for test verification against JMA official data.

気象庁の推算テキストをパースするテスト支援モジュール。
JMA公式データとの検証テストでのみ使用されます。
"""
```

### 2. `tests/support/__init__.py` (新規作成)
空ファイルまたは簡単な説明コメントを含める。

### 3. `scripts/fetch_jma_suisan_tide_data.py` (修正)
パースロジック削除後、以下の構成に簡素化:
- `fetch_suisan_text` 関数はそのまま維持
- `main` 関数で `tests.support.jma_suisan_parser` をインポート
- CLIダウンローダーとしての役割に集中

#### 修正後のインポート例
```python
from tests.support.jma_suisan_parser import parse_jma_suisan_text
```

#### 代替案: パースロジックを完全に削除
`main` 関数をダウンロード専用に縮退し、パースによる要約表示をスキップ。
ただし、利便性を考慮して当面はインポートを維持する方針を推奨。

### 4. `tests/integration/infrastructure/test_tide_prediction_against_jma_suisan.py` (修正)
インポートパスを変更:

**Before:**
```python
from scripts.fetch_jma_suisan_tide_data import parse_jma_suisan_text
```

**After:**
```python
from tests.support.jma_suisan_parser import parse_jma_suisan_text
```

## テスト計画

### 単体テスト (新規)
`tests/unit/support/test_jma_suisan_parser.py` を作成し、以下をテスト:
- `JMASuisanDaily` のインスタンス化
- `parse_jma_suisan_text` の正常系 (2回満潮・2回干潮)
- `parse_jma_suisan_text` の異常系 (不正な行、空データ)
- `_parse_time_height_block` の境界値テスト

### 既存テストの確認
- `tests/integration/infrastructure/test_tide_prediction_against_jma_suisan.py` がすべてパス
- インポートパス変更後の動作確認

## 検証方法

### 1. コード品質チェック
```bash
uv run ruff format .
uv run ruff check .
uv run pyright
```

### 2. テスト実行
```bash
# 新規単体テスト
uv run pytest tests/unit/support/test_jma_suisan_parser.py -v

# 既存統合テスト
uv run pytest tests/integration/infrastructure/test_tide_prediction_against_jma_suisan.py -v

# 全テスト
uv run pytest
```

### 3. スクリプトの動作確認
```bash
uv run python scripts/fetch_jma_suisan_tide_data.py --station TK --year 2026
```

## 実装ステップ

1. ✅ 要件の詳細化 (`docs/inprogress/issue-69.md` 作成)
2. ⚪ `tests/support/` ディレクトリ構造の作成
3. ⚪ `tests/support/jma_suisan_parser.py` へのパースロジック移動
4. ⚪ `tests/unit/support/test_jma_suisan_parser.py` の作成
5. ⚪ `scripts/fetch_jma_suisan_tide_data.py` のリファクタリング
6. ⚪ `tests/integration/infrastructure/test_tide_prediction_against_jma_suisan.py` のインポートパス更新
7. ⚪ 全品質チェックの実行
8. ⚪ コミット・PR作成

## 関連タスク
- T-006: 潮汐計算ライブラリアダプター
- T-013: E2E テスト
- T-013.2: 分単位の潮汐時刻精度改善
- T-013.3: 満干潮の欠落調査と修正

## リンク
- Issue: https://github.com/nakagawah13/fishing-forecast-gcal/issues/69
