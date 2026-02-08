# Issue #20: T-009 CalendarRepository 実装

**ステータス**: 🔵 In Progress  
**担当者**: AI  
**開始日**: 2026-02-08  
**完了予定日**: 2026-02-08  
**Issue**: https://github.com/nakagawah13/fishing-forecast-gcal/issues/20

---

## 概要

カレンダーリポジトリ（`ICalendarRepository` インターフェースの実装）を作成します。
このリポジトリは、Google Calendar APIを使用してカレンダーイベントの作成・取得・更新を行います。
冪等性を保証し、複数回実行しても結果が同じになるよう設計します。

---

## 責務

Infrastructure層として、以下を担います：

1. **イベントID生成**: `calendar_id + location_id + date` を素材にMD5ハッシュで安定IDを生成
2. **イベント取得**: GoogleCalendarClientを使用してイベントを取得し、Domainモデルに変換
3. **イベントUpsert**: 既存イベントがあれば更新、なければ作成（冪等操作）
4. **イベント一覧取得**: 指定期間・地点のイベントを取得
5. **API形式の変換**: Google Calendar API形式 ⇔ CalendarEvent（Domainモデル）の相互変換
6. **エラーハンドリング**: API呼び出し失敗時の適切な例外処理

---

## 実装方針

### 処理フロー

#### 1. get_event(event_id: str)

```
event_id
    ↓
GoogleCalendarClient.get_event(calendar_id, event_id)
    ↓ (Google API形式 dict | None)
_convert_to_domain_model(api_event)
    ↓ (CalendarEvent | None)
return CalendarEvent | None
```

#### 2. upsert_event(event: CalendarEvent)

```
CalendarEvent
    ↓
get_event(event.event_id) - 既存イベント確認
    ↓
if 既存あり:
    GoogleCalendarClient.update_event(...) - 差分更新
    NOTESセクション保持確認
else:
    GoogleCalendarClient.create_event(...) - 新規作成
```

#### 3. list_events(start_date, end_date, location_id)

```
start_date, end_date, location_id
    ↓
GoogleCalendarClient.list_events(time_min, time_max)
    ↓ (Google API形式 list[dict])
Filter by location_id (イベントIDのプレフィックスで判定)
    ↓
Convert to CalendarEvent
    ↓
return list[CalendarEvent]
```

### 依存コンポーネント

- **Client**: `GoogleCalendarClient` (infrastructure/clients/)
- **Models**: `CalendarEvent`, `Location`
- **Interface**: `ICalendarRepository` (domain/repositories/)

### 設計上の考慮点

1. **イベントID生成**:
   - `calendar_id + location_id + date` を結合（`f"{calendar_id}_{location_id}_{date.isoformat()}"`）
   - MD5ハッシュで64文字の安定IDを生成
   - Google Calendar APIの制約（5-1024文字の英数字・ハイフン）に準拠

2. **冪等性（Upsert）**:
   - 同じCalendarEventで複数回upsertを実行しても、結果が同じになることを保証
   - GoogleCalendarClientのcreate_eventは既存IDでの再作成時に409エラーを返すため、get_event→update/createのフローで対応

3. **NOTESセクション保持**:
   - upsert時、既存イベントの本文から `[NOTES]` セクションを抽出
   - 新しい description に `[NOTES]` セクションを結合
   - セクションが欠落している場合は更新をスキップし、ログで警告（フェーズ2で実装）

4. **API形式の変換**:
   - Google Calendar API形式（dict）⇔ CalendarEvent（dataclass）の変換ロジック
   - 終日イベント（`date` 形式）を使用

5. **エラーハンドリング**:
   - GoogleCalendarClient由来のエラーはRuntimeErrorにラップして送出
   - 404 Not Found: イベントが存在しない（get_eventではNoneを返す）
   - 認証エラー、権限不足エラー: RuntimeError

6. **設定の受け渡し**:
   - コンストラクタで `calendar_id` と `timezone` を受け取る
   - これらの値は Application層（UseCase）で設定ファイルから読み込んで注入

### API形式とDomainモデルの対応

**Google Calendar API Event形式**:
```python
{
    "id": "abc123...",
    "summary": "潮汐 横須賀 (大潮)",
    "description": "[TIDE]\n- 満潮: 06:12 (162cm)\n...",
    "start": {"date": "2026-02-08", "timeZone": "Asia/Tokyo"},
    "end": {"date": "2026-02-09", "timeZone": "Asia/Tokyo"}
}
```

**CalendarEvent (Domain Model)**:
```python
CalendarEvent(
    event_id="abc123...",
    title="潮汐 横須賀 (大潮)",
    description="[TIDE]\n- 満潮: 06:12 (162cm)\n...",
    date=date(2026, 2, 8),
    location_id="yokosuka"
)
```

**変換ロジック**:
- `id` ⇔ `event_id`
- `summary` ⇔ `title`
- `description` ⇔ `description`
- `start.date` ⇔ `date`（終日イベントなので date型）
- `location_id`: イベントIDから逆算（`event_id_to_location_id` ヘルパー関数）

---

## 成果物

### 実装ファイル

**ファイルパス**: `src/fishing_forecast_gcal/infrastructure/repositories/calendar_repository.py`

**クラス**: `CalendarRepository`

**メソッド**:
- `__init__(client: GoogleCalendarClient, calendar_id: str, timezone: str)`: コンストラクタ
- `generate_event_id(calendar_id: str, location_id: str, date: date) -> str`: イベントID生成（static method）
- `get_event(event_id: str) -> CalendarEvent | None`: イベント取得
- `upsert_event(event: CalendarEvent) -> None`: イベント作成/更新
- `list_events(start_date: date, end_date: date, location_id: str) -> list[CalendarEvent]`: イベント一覧取得

**補助メソッド（private）**:
- `_convert_to_domain_model(api_event: dict[str, Any]) -> CalendarEvent`: API形式→Domainモデル変換
- `_extract_location_id_from_event_id(event_id: str) -> str`: イベントIDから location_id を抽出
- `_preserve_notes_section(old_description: str, new_description: str) -> str`: NOTESセクション保持（フェーズ2）

---

## テスト要件

### 単体テスト (tests/unit/infrastructure/repositories/test_calendar_repository.py)

テスト対象: CalendarRepository（GoogleCalendarClientをモック化）

**テストケース**:

#### 1. イベントID生成テスト
- [x] 同じ入力（calendar_id, location_id, date）から同じIDが生成される（冪等性）
- [x] 異なる日付から異なるIDが生成される
- [x] IDがGoogle Calendar APIの制約（5-1024文字）に準拠している

#### 2. イベント取得テスト（get_event）
- [ ] 正常系: 既存イベントをCalendarEventに変換
- [ ] 正常系: 存在しないイベント（Noneを返す）
- [ ] 異常系: API呼び出し失敗（RuntimeError）

#### 3. イベントUpsertテスト（upsert_event）
- [ ] 正常系: 新規イベント作成（既存なし）
- [ ] 正常系: 既存イベント更新（既存あり）
- [ ] 正常系: 冪等性（同じCalendarEventで複数回upsert）
- [ ] 異常系: API呼び出し失敗（RuntimeError）

#### 4. イベント一覧取得テスト（list_events）
- [ ] 正常系: 指定期間・地点のイベントを取得
- [ ] 正常系: 該当イベントなし（空リスト）
- [ ] 正常系: location_idでフィルタリング
- [ ] 異常系: API呼び出し失敗（RuntimeError）

#### 5. API形式変換テスト
- [ ] Google API形式 → CalendarEvent 変換
- [ ] CalendarEvent → Google API形式 変換（Upsert時）
- [ ] 不正な形式のAPIレスポンス（KeyError等）のハンドリング

### 統合テスト (フェーズ2以降で検討)

テスト対象: CalendarRepository（実GoogleCalendarClientを使用）

**前提条件**:
- テスト用のカレンダーIDを環境変数で指定
- OAuth2認証情報が設定済み

**テストケース**:
- [ ] E2E: イベント作成→取得→更新→削除
- [ ] 冪等性: 同じCalendarEventで複数回upsert

---

## 依存関係

- **完了している依存タスク**:
  - T-001: ドメインモデル定義（CalendarEvent, Location）
  - T-002: リポジトリインターフェース定義（ICalendarRepository）
  - T-008: Google Calendar API クライアント（GoogleCalendarClient）

---

## 変更予定ファイル

### 新規作成

1. **実装ファイル**:
   - `src/fishing_forecast_gcal/infrastructure/repositories/calendar_repository.py` - 新規作成

2. **テストファイル**:
   - `tests/unit/infrastructure/repositories/test_calendar_repository.py` - 新規作成

### 既存ファイル（参照のみ）

- `src/fishing_forecast_gcal/domain/repositories/calendar_repository.py` - インターフェース
- `src/fishing_forecast_gcal/domain/models/calendar_event.py` - Domainモデル
- `src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py` - 依存クライアント

---

## 実装チェックリスト

### 実装

- [ ] `CalendarRepository` クラスの作成
- [ ] `__init__` メソッド（client, calendar_id, timezoneを受け取る）
- [ ] `generate_event_id` メソッド（MD5ハッシュでID生成）
- [ ] `get_event` メソッド（API呼び出し→変換）
- [ ] `upsert_event` メソッド（get→update/create）
- [ ] `list_events` メソッド（API呼び出し→フィルタ→変換）
- [ ] `_convert_to_domain_model` メソッド（API形式→CalendarEvent）
- [ ] `_extract_location_id_from_event_id` メソッド（イベントIDから location_id 抽出）

### テスト

- [ ] イベントID生成テスト（3件）
- [ ] get_event テスト（3件）
- [ ] upsert_event テスト（4件）
- [ ] list_events テスト（4件）
- [ ] API形式変換テスト（3件）

### 品質チェック

- [ ] `uv run ruff format .`
- [ ] `uv run ruff check .`
- [ ] `uv run pyright`
- [ ] `uv run pytest`

---

## 注意事項

### フェーズ1（MVP）のスコープ

今回のタスク（T-009）では以下がスコープ：
- イベントの作成・取得・更新・一覧取得の基本機能
- 冪等性の保証

以下はフェーズ2以降のスコープ（今回は含まない）：
- NOTESセクション保持ロジック（`_preserve_notes_section`）
- セクション欠落時の警告ログ
- 予報セクション（FORECAST）の部分更新

### Location_idの扱い

- CalendarEventには `location_id` フィールドがあるが、Google Calendar APIのイベントには対応フィールドなし
- 解決策: イベントIDの生成時に `location_id` を含めることで、イベントIDから逆算可能にする
- イベントIDフォーマット: `md5("{calendar_id}_{location_id}_{date.isoformat()}")`
- 逆算ロジック: 入力文字列の復元は不要（list_events時にすべてのイベントIDを生成して照合）

### イベントIDの制約

Google Calendar APIの制約:
- 5-1024文字
- 英数字とハイフン（`-`）のみ
- 大文字小文字を区別

MD5ハッシュ:
- 32文字（16進数表記）
- 制約を満たす

---

## 参考資料

- [Google Calendar API - Events: insert](https://developers.google.com/calendar/api/v3/reference/events/insert)
- [Google Calendar API - Events: get](https://developers.google.com/calendar/api/v3/reference/events/get)
- [Google Calendar API - Events: update](https://developers.google.com/calendar/api/v3/reference/events/update)
- [Google Calendar API - Events: list](https://developers.google.com/calendar/api/v3/reference/events/list)
- [Python hashlib](https://docs.python.org/3/library/hashlib.html)
