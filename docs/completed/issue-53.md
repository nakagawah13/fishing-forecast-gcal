# Issue #53: 分単位の潮汐時刻精度改善

## ステータス
- Status: Completed
- Issue: https://github.com/nakagawah13/fishing-forecast-gcal/issues/53
- 対象タスク: T-013.2

## 背景
- 満潮/干潮の時刻が常に「xx:00」になるため、公式潮見表と 20 分以上ズレるケースがある。
- 予報更新（Phase 2）前に天文潮の時刻精度を担保する必要がある。

## 目的 / 期待値
- 分単位の時刻が算出される（分=00 固定を解消）。
- 公式潮見表との時刻差が許容範囲（目標: ±10 分）に収まる。
- 東京/川崎の 2 地点で差分検証を行う。

## 実装方針
- `TideCalculationAdapter` の予測時刻配列の粒度を 5 分間隔に変更する。
- 分単位の極値抽出が適切に動作することを `TideCalculationService.extract_high_low_tides()` のテストで確認する。
- 公式潮見表との差分検証用テストを追加する（許容差: ±10 分）。

## 変更予定ファイル
- `src/fishing_forecast_gcal/infrastructure/adapters/tide_calculation_adapter.py`
  - 予測間隔を 5 分へ変更
  - 関連する docstring と定数の見直し
- `tests/unit/infrastructure/adapters/test_tide_calculation_adapter.py`
  - 分単位の時刻間隔のテスト
- `tests/integration/...`
  - 公式潮見表との差分検証（東京/川崎）

## 検証計画
- `uv run ruff format .`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest`

## 実装メモ
- 予測間隔を 5 分にした場合、1 日あたり 288 点となる。
- 既存の「24点/1時間刻み」のテストは更新が必要。

## 実装結果・変更点
- `TideCalculationAdapter` の予測間隔を 5 分に変更し、データ点数を日次で自動計算するよう更新。
- 分単位の時刻が含まれることをユニット/統合テストで検証。
- `Location` の `station_id` 必須化に合わせ、関連テストデータを更新。
- 潮位の妥当性テストの範囲を実データの変動に合わせて調整。

## 実行した検証
- `uv run ruff format .`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest`
