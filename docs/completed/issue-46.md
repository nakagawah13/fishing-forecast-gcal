# Issue #46: refactor: eliminate duplicate get_event API call in upsert flow

## ステータス: ✅ Completed (2026-02-11)

## 概要

`SyncTideUseCase.execute()` 内で `calendar_repo.get_event(event_id)` を呼び出して既存イベントの `[NOTES]` セクションを取得しているが、その直後に `calendar_repo.upsert_event(event)` を呼ぶと、`upsert_event` 内部でも `get_event(event_id)` が再度呼ばれる。結果として同一イベントID に対して Google Calendar API の GET が2回発生する。

## 現状のコールフロー

```
SyncTideUseCase.execute()
  ├── calendar_repo.get_event(event_id)      # 1回目: [NOTES] 抽出のため
  ├── ... (CalendarEvent 構築)
  └── calendar_repo.upsert_event(event)
        └── self.get_event(event.event_id)    # 2回目: upsert 内部で存在チェック
```

## 採用方針: 案A（upsert_event に既存イベント情報を渡す）

Issue で提案されていた3つの候補から **案A** を採用する。

### 理由

- インターフェース変更が最小限（オプション引数の追加のみ）
- 後方互換性を維持（`existing` は `None` がデフォルト）
- upsert のセマンティクスを維持
- キャッシュ層のような追加の複雑性を導入しない

### 改善後のコールフロー

```
SyncTideUseCase.execute()
  ├── calendar_repo.get_event(event_id)      # 1回のみ: [NOTES] 抽出 + 存在チェック
  ├── ... (CalendarEvent 構築)
  └── calendar_repo.upsert_event(event, existing=existing_event)
        └── (内部 get_event をスキップ)
```

## 変更対象ファイル

### 1. ドメイン層（インターフェース）

- `src/fishing_forecast_gcal/domain/repositories/calendar_repository.py`
  - `ICalendarRepository.upsert_event()` に `existing: CalendarEvent | None = None` パラメータ追加

### 2. インフラ層（実装）

- `src/fishing_forecast_gcal/infrastructure/repositories/calendar_repository.py`
  - `CalendarRepository.upsert_event()` で `existing` が渡された場合は内部の `get_event` をスキップ
  - `existing` が `None` の場合は従来通り内部で `get_event` を呼び出す（後方互換性）

### 3. アプリケーション層（UseCase）

- `src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py`
  - `upsert_event(event, existing=existing_event)` として既存イベント情報を渡す

### 4. テスト

- `tests/unit/infrastructure/repositories/test_calendar_repository.py`
  - `upsert_event` に `existing` パラメータを渡すテストケースを追加
  - `existing` が渡された場合に内部 `get_event` がスキップされることを検証
- `tests/unit/application/usecases/test_sync_tide_usecase.py`
  - `upsert_event` 呼び出し時に `existing` が渡されていることを検証

## 検証計画

1. 既存テストがすべてパスすること
2. `get_event` が UseCase 内で1回のみ呼ばれることを検証
3. upsert_event に `existing` を渡さない場合の後方互換性を検証
4. ruff / pyright チェックがパスすること

## 実装結果・変更点

### 実装方針

Issue で提案されていた3つの案から **案A**（`upsert_event` に既存イベント情報を渡す）を採用。keyword-only 引数 `existing: CalendarEvent | None = None` を追加し、呼び出し元が事前取得済みのイベントを渡せるようにした。

### 変更ファイル一覧

| ファイル | 変更内容 |
|---------|----------|
| `src/fishing_forecast_gcal/domain/repositories/calendar_repository.py` | `ICalendarRepository.upsert_event()` に `existing` パラメータ追加 |
| `src/fishing_forecast_gcal/infrastructure/repositories/calendar_repository.py` | `CalendarRepository.upsert_event()` で `existing` 渡し時に内部 `get_event` スキップ |
| `src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py` | `upsert_event(event, existing=existing_event)` として呼び出し |
| `tests/unit/infrastructure/repositories/test_calendar_repository.py` | 新規テスト2件追加（existing あり/なし） |
| `tests/unit/application/usecases/test_sync_tide_usecase.py` | `upsert_event` の `existing` パラメータ検証追加 |

### テスト結果

- 全 320 テスト合格（1 skipped, 5 deselected=E2E）
- `CalendarRepository` カバレッジ: 100%
- `SyncTideUseCase` カバレッジ: 99%
- ruff format / ruff check / pyright: すべてパス

### 効果

- 同一イベントIDに対する Google Calendar API の GET リクエストが2回→1回に削減
- タイミング差による一貫性の問題を解消
- 後方互換性を維持（`existing` パラメータはオプション）
