# Issue #91: Google API クライアント認証ロジックの共通化

## ステータス: Completed

## 概要

`GoogleCalendarClient.authenticate()` と `GoogleDriveClient.authenticate()` の重複認証ロジックを共通モジュール `google_auth.py` に抽出し、DRY 原則を適用する。

## 変更理由

### 現状の問題

1. **認証フローの重複**: 両クライアントの `authenticate()` メソッドがほぼ同一のロジック
   - トークン読み込み → 有効性チェック → リフレッシュ/新規フロー → トークン保存
2. **SCOPES の重複定義**: 同一の `SCOPES` リストが2ファイルで独立定義
3. **`print()` と `logger` の混在**: `GoogleCalendarClient` は `print()` を使用、`GoogleDriveClient` は `logger` を使用

### 影響

- Phase 2 で Weather API クライアント追加時にまたコピペの温床
- SCOPES 変更時に複数箇所の修正が必要
- ログ管理の一貫性が欠如

## 実装方針

### 変更ファイル

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `infrastructure/clients/google_auth.py` | 新規作成 | 共通認証ヘルパー（SCOPES、authenticate 関数） |
| `infrastructure/clients/google_calendar_client.py` | 修正 | 認証ロジック除去、`google_auth` 利用、`print()` → `logger` |
| `infrastructure/clients/google_drive_client.py` | 修正 | 認証ロジック除去、`google_auth` 利用 |
| `tests/unit/infrastructure/clients/test_google_auth.py` | 新規作成 | 共通認証モジュールのテスト |
| `tests/unit/infrastructure/clients/test_google_calendar_client.py` | 修正 | パッチパス更新 |
| `tests/unit/infrastructure/clients/test_google_drive_client.py` | 修正 | パッチパス更新、SCOPES インポート元変更 |

### `google_auth.py` 設計

```python
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
]

def authenticate(credentials_path: str, token_path: str) -> Credentials:
    """Perform OAuth2 authentication and return valid Credentials."""
    ...
```

### クライアント側の変更

各クライアントの `authenticate()` メソッドは以下のように簡素化:
1. `google_auth.authenticate()` を呼び出して `Credentials` を取得
2. それを使って `build()` で API サービスを構築

### `print()` → `logger` 統一

`GoogleCalendarClient` 内の全 `print()` 呼び出しを `logger` に置換:
- `print("Refreshing ...")` → `logger.info("Refreshing ...")`
- `print("Starting ...")` → `logger.info("Starting ...")`
- `print("Authentication successful!")` → `logger.info("Authentication successful!")`
- `print(f"Token saved ...")` → `logger.info("Token saved to: %s", ...)`
- `test_connection()` 内の `print()` → `logger.info()`

## 検証計画

1. `uv run pytest` - 全テスト通過
2. `uv run ruff format .` - フォーマットチェック
3. `uv run ruff check .` - Lintチェック
4. `uv run pyright` - 型チェック

## 実装結果

### 品質チェック結果

| チェック | 結果 |
|---------|------|
| `uv run ruff format .` | ✅ Pass |
| `uv run ruff check .` | ✅ Pass |
| `uv run pyright` | ✅ Pass（0 errors） |
| `uv run pytest` | ✅ Pass（全テスト通過） |

### 変更サマリ

- `google_auth.py`: 新規作成（約100行）- 共通認証関数 + SCOPES
- `google_calendar_client.py`: 認証ロジック除去、`print()` → `logger` 統一（-98行、+80行）
- `google_drive_client.py`: 認証ロジック除去（-70行）
- `test_google_auth.py`: 新規テスト（8ケース）
- `test_google_calendar_client.py`: フィクスチャ・インポート更新
- `test_google_drive_client.py`: 認証テスト簡素化・インポート更新
