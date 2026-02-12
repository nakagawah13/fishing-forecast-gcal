# Issue #93: TideDataRepository のドメインロジック分離と DI 改善

## ステータス: Completed

## 変更概要

`infrastructure/repositories/tide_data_repository.py` 内の月齢計算・潮位差計算ロジックを Domain 層に移動し、SRP 違反と DI 不完全を解消する。

## 現状の問題

1. **`_calculate_moon_age()`**: 月齢計算（天文学的計算）がリポジトリ内に存在 — リポジトリの責務外
2. **`_calculate_tide_range()`**: 潮位差計算がリポジトリ内に存在 — リポジトリの責務外
3. **コンストラクタでの直接インスタンス化**: DI が不完全で、テスト時にサービスの差し替えが困難
   ```python
   self._calculation_service = TideCalculationService()
   self._type_classifier = TideTypeClassifier()
   self._prime_time_finder = PrimeTimeFinder()
   ```

## 変更計画

### Step 1: `MoonAgeCalculator` ドメインサービスの新規作成

- **新規ファイル**: `src/fishing_forecast_gcal/domain/services/moon_age_calculator.py`
- `_calculate_moon_age()` のロジックを移動
- 定数 `MOON_CYCLE_DAYS`, `REFERENCE_NEW_MOON` も移動
- `@staticmethod` の `calculate()` メソッドとして実装

### Step 2: 潮位差計算の `TideCalculationService` への統合

- `_calculate_tide_range()` を `TideCalculationService.calculate_tide_range()` として追加
- `@staticmethod` メソッドとして実装（イベントリストを受け取り、潮位差を返す）

### Step 3: `TideDataRepository` コンストラクタの DI 化

- コンストラクタに以下の引数を追加:
  - `tide_calc_service: TideCalculationService`
  - `tide_type_classifier: TideTypeClassifier`
  - `prime_time_finder: PrimeTimeFinder`
- `_calculate_moon_age()` / `_calculate_tide_range()` を削除し、外部サービスを呼び出す
- `MOON_CYCLE_DAYS` / `REFERENCE_NEW_MOON` 定数を削除

### Step 4: CLI DI 構築の更新

- `presentation/commands/sync_tide.py` の `run()` 関数で DI 構築を更新
- ドメインサービスを明示的にインスタンス化し、`TideDataRepository` に注入

### Step 5: テスト更新

- `tests/unit/infrastructure/repositories/test_tide_data_repository.py`
  - `MoonAgeCalculator` テストを新テストファイルに移動
  - `_calculate_tide_range` テストを `TideCalculationService` テストに移動
  - リポジトリのフィクスチャに DI パラメータを追加
- `tests/unit/domain/services/test_moon_age_calculator.py` を新規作成
- `tests/unit/domain/services/test_tide_calculation_service.py` にテストケースを追加
- 統合テストのフィクスチャ更新

## 変更対象ファイル

### 新規作成
- `src/fishing_forecast_gcal/domain/services/moon_age_calculator.py`
- `tests/unit/domain/services/test_moon_age_calculator.py`

### 修正
- `src/fishing_forecast_gcal/infrastructure/repositories/tide_data_repository.py`
- `src/fishing_forecast_gcal/presentation/commands/sync_tide.py`
- `src/fishing_forecast_gcal/domain/services/tide_calculation_service.py`
- `src/fishing_forecast_gcal/domain/services/__init__.py`
- `tests/unit/infrastructure/repositories/test_tide_data_repository.py`
- `tests/unit/domain/services/test_tide_calculation_service.py`
- `tests/integration/infrastructure/test_tide_data_repository_integration.py`

## 検証計画

1. 全既存テストが通過すること
2. `MoonAgeCalculator` の単体テストが追加されること
3. `TideCalculationService.calculate_tide_range()` のテストが追加されること
4. DI 化後もリポジトリの動作が変わらないこと
5. `uv run ruff format .` / `uv run ruff check .` / `uv run pyright` / `uv run pytest` すべてパス

## 実装結果

### 品質チェック結果

| 種別 | 結果 |
|------|------|
| ruff format | 変更なし（準拠済み） |
| ruff check | All checks passed |
| pyright | 0 errors, 0 warnings |
| pytest | 441 passed, 1 skipped |

### 変更サマリ

- `MoonAgeCalculator` ドメインサービスを新規作成（7テスト追加）
- `TideCalculationService` に `calculate_tide_range()` 静的メソッドを追加（4テスト追加）
- `TideDataRepository` コンストラクタを DI 化（Optional デフォルト付きで後方互換性維持）
- リポジトリから `_calculate_moon_age()`, `_calculate_tide_range()`, 定数 `MOON_CYCLE_DAYS`, `REFERENCE_NEW_MOON` を削除
- CLI `sync_tide.py` で明示的な DI 構築を実装
- 単体テスト・統合テストのフィクスチャを更新
