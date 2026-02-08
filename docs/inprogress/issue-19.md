# Issue #19: T-008 Google Calendar API クライアント

**ステータス**: In Progress  
**担当者**: AI  
**開始日**: 2026-02-08  
**Issue**: https://github.com/nakagawah13/fishing-forecast-gcal/issues/19

---

## 概要

Google Calendar API のラッパーを実装します。既にOAuth2認証の基本実装は存在していますが、
カレンダーイベントの作成・取得・更新の機能が不足しているため、これらを追加実装します。

---

## 責務

Infrastructure層として、以下を担います：

1. **OAuth2認証**: 既存実装を維持（credentials/tokenファイルを使用）
2. **イベント作成**: カレンダーにイベントを新規作成
3. **イベント取得**: イベントIDまたは検索条件でイベントを取得
4. **イベント更新**: 既存イベントを更新
5. **エラーハンドリング**: API呼び出し失敗時の適切な例外処理

---

## 実装方針

### 現在の実装状況

既存の `infrastructure/clients/google_calendar_client.py` には以下が実装済み：
- OAuth2認証フロー（`authenticate()`）
- サービスインスタンス取得（`get_service()`）
- 接続テスト（`test_connection()`）

### 追加実装が必要な機能

#### 1. イベント作成（create_event）

```python
def create_event(
    self,
    calendar_id: str,
    event_id: str,
    summary: str,
    description: str,
    start_date: date,
    end_date: date,
    timezone: str = "Asia/Tokyo"
) -> dict[str, Any]:
```

**処理内容**:
- 終日イベント（all-day event）として作成
- Google Calendar API の `events().insert()` を使用
- `eventId` パラメータで安定したIDを指定（冪等性確保）

#### 2. イベント取得（get_event）

```python
def get_event(
    self,
    calendar_id: str,
    event_id: str
) -> dict[str, Any] | None:
```

**処理内容**:
- Google Calendar API の `events().get()` を使用
- イベントが存在しない場合は `None` を返す
- 404エラーをハンドリング

#### 3. イベント更新（update_event）

```python
def update_event(
    self,
    calendar_id: str,
    event_id: str,
    summary: str | None = None,
    description: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    timezone: str = "Asia/Tokyo"
) -> dict[str, Any]:
```

**処理内容**:
- Google Calendar API の `events().patch()` を使用（部分更新）
- 既存イベントを取得し、指定されたフィールドのみ更新
- イベントが存在しない場合は例外を送出

#### 4. イベント検索（list_events）（オプション）

```python
def list_events(
    self,
    calendar_id: str,
    time_min: datetime | None = None,
    time_max: datetime | None = None,
    max_results: int = 10
) -> list[dict[str, Any]]:
```

**処理内容**:
- Google Calendar API の `events().list()` を使用
- 期間を指定してイベント一覧を取得

### 設計上の考慮点

1. **冪等性**: `create_event` で `eventId` を明示的に指定し、重複登録を防止
2. **エラーハンドリング**:
   - 404 Not Found: イベントが存在しない（get_eventではNoneを返す）
   - 409 Conflict: イベントIDが既に存在（create_eventで予期される動作）
   - 401 Unauthorized: 認証エラー
   - 403 Forbidden: 権限不足
   - 5xx: サーバーエラー（リトライ候補）
3. **終日イベント**: `date` 形式を使用（`dateTime` 形式ではない）
4. **タイムゾーン**: デフォルトは "Asia/Tokyo"、設定で変更可能

---

## 成果物

### 実装ファイル

**ファイルパス**: `src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py`（既存ファイルに追加）

**追加メソッド**:
- `create_event()`
- `get_event()`
- `update_event()`
- `list_events()` （オプション）

---

## テスト要件

### 単体テスト (tests/unit/infrastructure/clients/test_google_calendar_client.py)

**テスト対象**: GoogleCalendarClient（API呼び出しをモック化）

**テストケース**:

#### 1. OAuth2認証テスト
- [x] 新規認証フロー（トークンなし）
- [x] トークン再利用（有効なトークンが存在）
- [x] トークンリフレッシュ（期限切れトークン）
- [x] credentials.json不在時のエラー

#### 2. イベント作成テスト
- [ ] 正常系: 新規イベント作成
- [ ] 正常系: 同じイベントID で再作成（冪等性）
- [ ] 異常系: 認証エラー（401）
- [ ] 異常系: 権限不足（403）

#### 3. イベント取得テスト
- [ ] 正常系: 既存イベント取得
- [ ] 正常系: 存在しないイベント（Noneを返す）
- [ ] 異常系: 認証エラー

#### 4. イベント更新テスト
- [ ] 正常系: 既存イベント更新（summary更新）
- [ ] 正常系: 既存イベント更新（description更新）
- [ ] 正常系: 部分更新（一部フィールドのみ指定）
- [ ] 異常系: 存在しないイベント更新

### 統合テスト (tests/integration/infrastructure/clients/test_google_calendar_client_integration.py)

**テスト対象**: GoogleCalendarClient（実際のGoogle Calendar APIを使用）

**前提条件**:
- テスト用のカレンダーIDを環境変数で指定（`TEST_CALENDAR_ID`）
- OAuth2認証情報が設定済み

**テストケース**:
- [ ] E2E: イベント作成→取得→更新→削除
- [ ] 冪等性: 同じイベントを複数回作成
- [ ] APIレート制限の確認

**注意事項**:
- 統合テストは実際のGoogle Calendar APIを呼び出すため、実行にはネットワーク接続と認証が必要
- テスト後はイベントをクリーンアップする

---

## 変更予定ファイル

1. **実装ファイル**:
   - `src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py` - メソッド追加

2. **テストファイル**:
   - `tests/unit/infrastructure/clients/test_google_calendar_client.py` - 新規作成
   - `tests/integration/infrastructure/clients/test_google_calendar_client_integration.py` - 新規作成

3. **ディレクトリ作成**:
   - `tests/unit/infrastructure/clients/` - 新規作成
   - `tests/integration/infrastructure/clients/` - 新規作成

---

## 検証計画

### ステップ1: 単体テストの実装と確認
1. テストファイルを作成
2. モックを使用してAPI呼び出しをシミュレート
3. `uv run pytest tests/unit/infrastructure/clients/` を実行
4. すべてのテストがパスすることを確認

### ステップ2: メソッドの実装
1. `create_event` メソッドを実装
2. 単体テストを実行して動作確認
3. `get_event` メソッドを実装
4. 単体テストを実行して動作確認
5. `update_event` メソッドを実装
6. 単体テストを実行して動作確認

### ステップ3: 統合テストの実装と確認
1. テスト用カレンダーを準備
2. 統合テストを実装
3. `uv run pytest tests/integration/infrastructure/clients/` を実行
4. 実際のAPIとの連携を確認

### ステップ4: 品質チェック
1. `uv run ruff format .`
2. `uv run ruff check .`
3. `uv run pyright`
4. `uv run pytest`（全テスト実行）

---

## 依存関係

- **外部依存**: Google Calendar API v3
- **内部依存**: なし（最下層の Infrastructure クライアント）
- **使用ライブラリ**:
  - `google-api-python-client`
  - `google-auth`
  - `google-auth-oauthlib`

---

## 参照

- [Google Calendar API v3 Documentation](https://developers.google.com/calendar/api/v3/reference)
- [Events: insert](https://developers.google.com/calendar/api/v3/reference/events/insert)
- [Events: get](https://developers.google.com/calendar/api/v3/reference/events/get)
- [Events: patch](https://developers.google.com/calendar/api/v3/reference/events/patch)
- [docs/implementation_plan.md T-008](../implementation_plan.md)
