# Issue #58: 釣り情報の初期化コマンド（reset-tide）

## ステータス: Completed

## 概要

登録済みの潮汐イベントを安全に初期化（削除）できる CLI サブコマンド `reset-tide` を提供する。

## 背景

一度ツールで記入した釣り情報を初期化する手段がない。運用上、まとめて削除・再同期したいケースが想定される。

## 受け入れ条件

- `reset-tide` サブコマンドで指定条件に合致するイベントのみ削除できる
- `--dry-run` で削除対象の件数が確認できる
- `--force` なしの場合は確認プロンプトが表示される
- 期間指定（`--start-date`, `--end-date`, `--days`）と地点指定（`--location-id`）が可能
- 実行ログが詳細に出力される

## 実装方針

### レイヤー別変更計画

#### 1. Infrastructure Layer - Google Calendar Client（`delete_event` 追加）

**ファイル**: `src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py`

- `delete_event(calendar_id, event_id)` メソッドを追加
- 404の場合はエラーを投げずにスキップ（冪等性）
- `list_events(calendar_id, start_date, end_date)` メソッドを追加（期間指定でイベント一覧取得）

#### 2. Domain Layer - リポジトリインターフェース拡張

**ファイル**: `src/fishing_forecast_gcal/domain/repositories/calendar_repository.py`

- `delete_event(event_id: str) -> bool` メソッドをインターフェースに追加
  - 返り値: 削除成功で True、存在しない場合は False

#### 3. Infrastructure Layer - CalendarRepository 実装

**ファイル**: `src/fishing_forecast_gcal/infrastructure/repositories/calendar_repository.py`

- `delete_event()` の実装
- `list_events()` の実装（現在はプレースホルダー）
  - Google Calendar API の `events().list()` で `privateExtendedProperty` フィルタを使用し `location_id` でフィルタリング

#### 4. Application Layer - ResetTideUseCase

**ファイル**: `src/fishing_forecast_gcal/application/usecases/reset_tide_usecase.py`（新規作成）

- 指定期間・地点のイベントを取得し、削除するユースケース
- dry-run モードのサポート
- 削除結果のサマリーを返す

#### 5. Presentation Layer - CLI

**ファイル**: `src/fishing_forecast_gcal/presentation/cli.py`

- `reset-tide` サブコマンドの追加
- オプション: `--config`, `--location-id`, `--start-date`, `--end-date`, `--days`, `--dry-run`, `--force`, `--verbose`
- `--force` なしの場合は確認プロンプト表示
- `--days` と `--end-date` の排他チェック（`sync-tide` と同様）

### テスト計画

#### 単体テスト
- `GoogleCalendarClient.delete_event()` のテスト
- `GoogleCalendarClient.list_events()` のテスト
- `CalendarRepository.delete_event()` のテスト
- `CalendarRepository.list_events()` のテスト
- `ResetTideUseCase` のテスト（Mock リポジトリ）
- CLI `reset-tide` の引数パーステスト
- CLI `reset-tide` の実行フローテスト

## 実装順序

1. `GoogleCalendarClient` に `delete_event` / `list_events` 追加 + テスト
2. `ICalendarRepository` インターフェース拡張
3. `CalendarRepository` の `delete_event` / `list_events` 実装 + テスト
4. `ResetTideUseCase` 実装 + テスト
5. CLI `reset-tide` サブコマンド実装 + テスト
6. 品質チェック（ruff, pyright, pytest）

## 実装結果

### 品質チェック

| 種別 | 結果 |
|------|------|
| ruff format | ✅ Pass |
| ruff check | ✅ Pass |
| pyright | ✅ Pass (0 errors) |
| pytest | ✅ Pass (270 passed, 1 skipped) |
| coverage | 93% |

### 変更ファイル一覧

| ファイル | 変更内容 |
|---------|----------|
| `src/.../infrastructure/clients/google_calendar_client.py` | `delete_event()`, `list_events()` 追加 |
| `src/.../domain/repositories/calendar_repository.py` | `delete_event()` 抽象メソッド追加 |
| `src/.../infrastructure/repositories/calendar_repository.py` | `list_events()` 実装, `delete_event()` 実装 |
| `src/.../application/usecases/reset_tide_usecase.py` | 新規作成 |
| `src/.../presentation/cli.py` | `reset-tide` サブコマンド追加, `main()` リファクタリング |
| `tests/unit/infrastructure/clients/test_google_calendar_client.py` | 7 テスト追加 |
| `tests/unit/infrastructure/repositories/test_calendar_repository.py` | 8 テスト追加 |
| `tests/unit/application/usecases/test_reset_tide_usecase.py` | 新規作成 (6 テスト) |
| `tests/unit/presentation/test_cli.py` | 13 テスト追加 |
| `tests/unit/domain/repositories/test_calendar_repository.py` | Mock に `delete_event` 追加 |
