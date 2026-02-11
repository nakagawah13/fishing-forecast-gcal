# Issue #78: Google Drive/Calendar API 添付機能の実装

**ステータス**: 🔵 In Progress
**担当**: AI Assistant
**作成日**: 2026-02-11
**関連Issue**: #78
**フェーズ**: Phase 1.9
**親Issue**: #76（POC — 方式B採用決定）

---

## 概要

Google Drive API クライアントを新規実装し、GoogleCalendarClient に attachments 対応を追加する。Issue #76（POC）で採用した **方式 B（Google Drive + Calendar attachments）** の Infrastructure 層を構築する。

## 変更対象

### 新規作成

1. **`src/fishing_forecast_gcal/infrastructure/clients/google_drive_client.py`**
   - `GoogleDriveClient` クラス
   - `authenticate()`: OAuth2 認証（既存 credentials/token を共有）
   - `upload_file()`: ファイルアップロード + 公開権限設定 → 公開URL返却
   - `delete_file()`: ファイル削除
   - `list_files()`: ファイル一覧取得（フォルダ・クエリフィルタ対応）
   - `get_or_create_folder()`: 専用フォルダ管理

2. **`tests/unit/infrastructure/clients/test_google_drive_client.py`**
   - Upload/delete/list のモック API テスト
   - フォルダ作成・取得のモック API テスト
   - 認証失敗時のエラーハンドリング

### 変更

3. **`src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py`**
   - `SCOPES` に `drive.file` 追加
   - `create_event()` に `attachments` パラメータ追加 + `supportsAttachments=True`
   - `update_event()` に `attachments` パラメータ追加 + `supportsAttachments=True`

4. **`tests/unit/infrastructure/clients/test_google_calendar_client.py`**
   - attachments 付きイベント作成/更新のモックテスト追加
   - attachments なしの後方互換性テスト（既存テスト活用）

## 技術仕様

### Google Drive API

- **スコープ**: `https://www.googleapis.com/auth/drive.file`（アプリ作成ファイルのみ、最小権限）
- **アップロード**: `files.create` / multipart upload
- **公開設定**: `permissions.create` → `role: reader, type: anyone`
- **専用フォルダ**: `fishing-forecast-tide-graphs`（他ファイルと混在しない）
- **ライブラリ**: `google-api-python-client`（既存依存に含む）

### Calendar API attachments

- `fileUrl`: `https://drive.google.com/file/d/{fileId}/view?usp=drivesdk` 形式
- `supportsAttachments=true` をクエリパラメータに設定
- 最大25個/イベント

### OAuth2 スコープ変更

```python
SCOPES = [
    "https://www.googleapis.com/auth/calendar",      # 既存
    "https://www.googleapis.com/auth/drive.file",     # 新規追加
]
```

**注意**: スコープ変更時は `token.json` 削除 → 再認証が必要

## 実装手順

### Phase 1: GoogleDriveClient 新規実装
1. `google_drive_client.py` のスケルトン作成
2. `authenticate()` 実装（Calendar Client と同じパターン）
3. `get_or_create_folder()` 実装
4. `upload_file()` 実装（multipart upload + permissions.create）
5. `delete_file()` 実装
6. `list_files()` 実装
7. ユニットテスト作成

### Phase 2: GoogleCalendarClient attachments 対応
1. `SCOPES` に `drive.file` 追加
2. `create_event()` に `attachments` パラメータ追加
3. `update_event()` に `attachments` パラメータ追加
4. 両メソッドで `supportsAttachments=True` を設定
5. ユニットテスト追加

## 検証計画

- [ ] `uv run ruff format .` パス
- [ ] `uv run ruff check .` パス
- [ ] `uv run pyright` パス
- [ ] `uv run pytest` パス（全テスト）
- [ ] Drive upload/delete/list のモック API テスト
- [ ] フォルダ作成・取得のモック API テスト
- [ ] attachments 付きイベント作成/更新のモックテスト
- [ ] attachments なしの後方互換性テスト
- [ ] 認証失敗時のエラーハンドリング

## 依存

- T-008: Google Calendar API クライアント（✅ 完了）
- T-009: CalendarRepository 実装（✅ 完了）
- T-013.11: タイドグラフ画像の表示方式POC（✅ 完了）
