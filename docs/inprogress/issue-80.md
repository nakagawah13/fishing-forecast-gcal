# Issue #80: SyncTideUseCase への画像添付統合

## ステータス: In Progress

## 概要

タイドグラフ画像の生成・Drive アップロード・Calendar 添付を SyncTideUseCase に統合する。
Issue #76（POC）の ST-4 に対応。Application 層のオーケストレーション変更。

## 前提（完了済み）

- ST-1 + ST-2: Google Drive/Calendar API 添付機能（Issue #78）✅
  - `GoogleDriveClient` 実装済み（upload_file, get_or_create_folder）
  - `GoogleCalendarClient` に attachments パラメータ追加済み
- ST-3: タイドグラフ画像生成サービス（Issue #79）✅
  - `TideGraphService.generate_graph()` 実装済み
  - ダークモード、満干潮アノテーション、時合い帯ハイライト対応

## 実装方針

### 1. Repository インターフェース拡張

#### ITideDataRepository に `get_hourly_heights()` 追加
- `TideGraphService.generate_graph()` は `hourly_heights: list[tuple[float, float]]`（時間 0.0-24.0, 潮位cm）を要求
- 現行の `get_tide_data()` は `Tide` オブジェクトを返すが、時系列データは含まない
- Repository インターフェースに新メソッドを追加し、Application 層がインフラ層に直接依存しない設計を維持

#### ICalendarRepository の `upsert_event()` に `attachments` 追加
- カレンダーイベントに画像 URL を添付するため、`upsert_event()` に `attachments` パラメータ追加
- Domain モデル（CalendarEvent）には添付情報を持たせない（インフラ関心事のため）

### 2. 設定ファイル拡張

`AppSettings` に `TideGraphSettings` を追加:
```python
@dataclass(frozen=True)
class TideGraphSettings:
    enabled: bool
    drive_folder_name: str
    # retention_days, dpi, figsize, dark_mode は将来拡張
```

### 3. SyncTideUseCase 拡張

- `TideGraphService` と `GoogleDriveClient` をオプションDI
- `tide_graph_enabled` フラグで ON/OFF 制御
- 処理フロー:
  1. 潮汐データ取得（既存）
  2. イベント本文生成（既存）
  3. **タイドグラフ画像生成**（新規、`TideGraphService`）
  4. **Google Drive にアップロード**（新規、`GoogleDriveClient`）
  5. **attachments 付きでイベント作成/更新**（拡張）
  6. **一時ファイル削除**（新規）
- 画像添付失敗時の graceful degradation（ログ警告のみ、イベント同期は継続）

### 4. CLI 拡張

- DI 構築で `TideGraphService` / `GoogleDriveClient` を注入
- `tide_graph.enabled` 設定に基づいて有効化

## 変更予定ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/.../domain/repositories/tide_data_repository.py` | `get_hourly_heights()` 追加 |
| `src/.../domain/repositories/calendar_repository.py` | `upsert_event()` に `attachments` 追加 |
| `src/.../infrastructure/repositories/tide_data_repository.py` | `get_hourly_heights()` 実装 |
| `src/.../infrastructure/repositories/calendar_repository.py` | `upsert_event()` に `attachments` 対応 |
| `src/.../presentation/config_loader.py` | `TideGraphSettings` 追加 |
| `src/.../application/usecases/sync_tide_usecase.py` | 画像統合フロー追加 |
| `src/.../presentation/cli.py` | DI 構築更新 |
| `config/config.yaml.template` | `tide_graph` セクション追加 |
| `tests/unit/application/usecases/test_sync_tide_usecase.py` | 新規テスト追加 |

## テスト計画

1. **画像添付有効時の正常フロー** - 画像生成→アップロード→添付の一連動作
2. **画像添付無効時の後方互換性** - `enabled: false` で既存動作を維持
3. **画像生成失敗時の graceful degradation** - イベント同期は継続
4. **Drive アップロード失敗時の graceful degradation** - イベント同期は継続
5. **既存テストの維持** - [TIDE]/[FORECAST]/[NOTES] セクション更新ルール維持
6. **[NOTES] セクション保持** - 手動メモが消えないこと
