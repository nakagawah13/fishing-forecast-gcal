# Issue 54: fix(tide): ensure daily high/low events

## Status
- Completed

## Background
1日あたり満潮2回・干潮2回が原則だが、一部の日で片側が欠落する。
TideCalculationService の極値抽出条件やサンプリング間隔の影響が疑われる。

## Scope
- TideCalculationService の極値抽出ロジックを調査・改善する
- 欠落が発生する条件を特定し、再現テストを追加する
- 30日分で満干潮が2回ずつ抽出されることを確認する
- 例外（満干潮が1回の条件）がある場合は明文化する

## Implementation Plan
1. 既存テストとロジックを確認し、欠落条件を再現する
2. 極値抽出の探索窓/条件を見直し、欠落を防ぐ
3. 再現テストを追加し、30日分の抽出結果を検証する
4. 例外条件がある場合はドキュメント化する

## Files To Update
- src/fishing_forecast_gcal/domain/services/tide_calculation_service.py
- tests/unit/domain/services/test_tide_calculation_service.py
- tests/integration (必要に応じて)
- docs/implementation_plan.md (進捗更新)

## Validation Plan
- uv run ruff format .
- uv run ruff check .
- uv run pyright
- uv run pytest

## Notes
- 公式潮見表との差分がある日付を特定し、再現条件として採用する
- 欠落が避けられない例外条件は明示し、テストに反映する

## 実装結果・変更点
- 満干潮の極値検出でフラット区間（同一潮位が連続する区間）を考慮
- 30日分の安定波形で日次2回ずつの満干潮抽出を検証するテストを追加
- 極値抽出テストの追加と docstring 形式の統一
