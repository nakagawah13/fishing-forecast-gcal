# Issue #54: fix(tide): ensure daily high/low events (reopen)

## ステータス
- Completed

## 背景
1日あたり満潮2回・干潮2回が原則だが、一部の日で片側が欠落する。
前回修正後も再現があり、2026-02-18 (川崎) で干潮2回目が欠落した。

## 再現情報
- 日付: 2026-02-18
- 地点: 川崎
- 気象庁データ: https://www.data.jma.go.jp/kaiyou/data/db/tide/suisan/txt/2026/KW.txt
- 公式時刻
  - 満潮1: 06:01
  - 満潮2: 17:20
  - 干潮1: 11:43
  - 干潮2: 23:59
- 本ツール出力
  - 満潮1: 06:00
  - 満潮2: 17:20
  - 干潮1: 11:50
  - 干潮2: なし

## 目的 / 期待値
- 1日あたり原則2回の満潮・干潮が抽出されること
- 欠落が起きる条件が特定され、再現テストが追加されること
- 例外条件がある場合はドキュメント化されること

## 実装方針
1. 2026-02-18 川崎の欠落を再現するユニットテストを追加する
2. 抽出ロジックの境界条件 (日付境界、フラット区間、終端近傍) を確認する
3. 必要に応じて探索窓/閾値/サンプリング間隔の補正を行う
4. 欠落が避けられないケースは明文化する

## 変更予定ファイル
- src/fishing_forecast_gcal/domain/services/tide_calculation_service.py
- tests/unit/domain/services/test_tide_calculation_service.py
- tests/integration (必要に応じて)
- docs/implementation_plan.md

## 検証計画
- uv run ruff format .
- uv run ruff check .
- uv run pyright
- uv run pytest

## 実装メモ
- 欠落が日付境界付近 (23:59) で起きているため、日次境界の処理を重点確認する
- 終端側の極値検出条件 (前後点の比較) とサンプリング間隔の影響を検証する

## 実装結果・変更点
- 潮汐予測の時刻列に日付境界の補助点を追加し、終端側の極値欠落を抑制
- 日付境界付近の干潮検出を確認するユニットテストを追加
- アダプタ側テストを補助点込みの期待値に更新

## 実行した検証
- uv run ruff format .
- uv run ruff check .
- uv run pyright
- uv run pytest
