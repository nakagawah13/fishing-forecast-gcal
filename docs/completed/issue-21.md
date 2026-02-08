# Issue #21: T-010 SyncTideUseCase 実装

**ステータス**: In Progress  
**担当**: AI  
**開始日**: 2026-02-08  
**関連Issue**: [#21](https://github.com/nakagawah13/fishing-forecast-gcal/issues/21)

---

## 概要

天文潮の同期処理をオーケストレーションするユースケースを実装します。
これはMVPの中核となるコンポーネントで、潮汐データ取得からカレンダーイベント作成までの一連の流れを統括します。

---

## 責務

- 潮汐データの取得（`ITideDataRepository` 経由）
- カレンダーイベントの作成/更新（`ICalendarRepository` 経由）
- イベント本文の生成（`[TIDE]` セクション）
- エラーハンドリングとログ出力

---

## 現在の実装状況（前提）

### 完了しているコンポーネント

#### ドメイン層
- ✅ **ドメインモデル** (T-001)
  - `Location`: 地点情報（不変ID含む）
  - `Tide`: 1日分の潮汐情報（潮回り、満干潮、時合い帯）
  - `TideEvent`: 満潮・干潮の個別イベント
  - `CalendarEvent`: カレンダーイベント（セクション分割対応）

- ✅ **リポジトリインターフェース** (T-002)
  - `ITideDataRepository`: 潮汐データ取得の抽象化
  - `ICalendarRepository`: カレンダーイベント操作の抽象化

- ✅ **ドメインサービス** (T-003, T-004, T-005)
  - `TideCalculationService`: 満干潮抽出
  - `TideTypeClassifier`: 潮回り判定
  - `PrimeTimeFinder`: 時合い帯計算

#### インフラ層
- ✅ **TideCalculationAdapter** (T-006): UTideライブラリラッパー
- ✅ **TideDataRepository** (T-007): 潮汐データ取得実装
- ✅ **GoogleCalendarClient** (T-008): Google Calendar API ラッパー
- ✅ **CalendarRepository** (T-009): カレンダーイベント操作実装（upsertロジック含む）

### 未実装のコンポーネント

- ❌ **Application層**
  - `SyncTideUseCase`: 天文潮同期のオーケストレーション（**本タスクで実装**）
  - `SyncWeatherUseCase`: 天気予報同期（フェーズ2）

- ❌ **Presentation層**
  - `ConfigLoader`: 設定ファイルローダー (T-011)
  - `CLI`: コマンドラインインターフェース (T-012)

---

## 実装方針

### 設計原則

1. **単一責任の原則**: UseCaseは「調整」のみを担当し、具体的なロジックはドメインサービス・リポジトリに委譲
2. **依存性注入**: リポジトリはコンストラクタで注入し、テスト容易性を確保
3. **エラーハンドリング**: 例外は適切にキャッチし、ユーザーフレンドリーなメッセージをログ出力
4. **冪等性**: 同じ入力で複数回実行しても結果が同じになることを保証（CalendarRepositoryのupsertで実現）

### 実装スコープ

- **対象**: 単一地点・単一日付の潮汐同期
- **MVP制約**: 複数地点のループ処理はフェーズ3で実装（T-021）
- **イベント本文**: `[TIDE]` セクションのみ生成（`[FORECAST]` はフェーズ2）

### イベント本文フォーマット

```
潮汐 {location_name} ({tide_type})

[TIDE]
- 満潮: {HH:MM} ({height}cm), {HH:MM} ({height}cm)
- 干潮: {HH:MM} ({height}cm), {HH:MM} ({height}cm)
- 時合い: {HH:MM}-{HH:MM}

[FORECAST]
（フェーズ2で追加予定）

[NOTES]
（ユーザー手動追記欄）
```

**更新時の動作**:
- 既存イベントに `[NOTES]` セクションが存在する場合は保持
- `[TIDE]` セクションのみを更新
- セクションが存在しない場合は、全体を新規作成

---

## 変更予定のファイル

### 新規作成

1. **`src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py`**
   - `SyncTideUseCase` クラス
   - `execute()` メソッド

### テスト

2. **`tests/unit/application/usecases/test_sync_tide_usecase.py`**
   - Mockリポジトリを使用した単体テスト
   - 正常系・異常系のテスト

3. **`tests/integration/application/usecases/test_sync_tide_usecase_integration.py`** (オプション)
   - 実リポジトリを使用した統合テスト
   - E2Eテスト (T-013) で代替可能

---

## 実装の詳細設計

### クラス構造

```python
class SyncTideUseCase:
    """天文潮同期のユースケース
    
    指定された地点・日付の潮汐情報を取得し、
    Google カレンダーにイベントを作成/更新します。
    
    Attributes:
        _tide_repo: 潮汐データリポジトリ
        _calendar_repo: カレンダーリポジトリ
    """
    
    def __init__(
        self,
        tide_repo: ITideDataRepository,
        calendar_repo: ICalendarRepository,
    ) -> None:
        """初期化
        
        Args:
            tide_repo: 潮汐データリポジトリ（依存性注入）
            calendar_repo: カレンダーリポジトリ（依存性注入）
        """
        ...
    
    def execute(
        self,
        location: Location,
        target_date: date,
    ) -> None:
        """天文潮を同期
        
        Args:
            location: 対象地点
            target_date: 対象日
        
        Raises:
            RuntimeError: 潮汐データ取得またはカレンダー更新に失敗した場合
        """
        ...
```

### 処理フロー

```
1. 潮汐データ取得
   ↓ tide_repo.get_tide_data(location, target_date)
   
2. イベント本文生成
   ↓ _format_tide_section(tide)
   
3. 既存イベント取得
   ↓ calendar_repo.get_event(event_id)
   
4. 既存の[NOTES]を保持
   ↓ existing_event.extract_section("NOTES") if exists
   
5. CalendarEvent作成
   ↓ CalendarEvent(...)
   
6. カレンダーに登録
   ↓ calendar_repo.upsert_event(event)
```

### イベントID生成

- CalendarRepositoryが `calendar_id + location_id + date` のMD5ハッシュを生成
- UseCaseではevent_idを直接生成せず、CalendarRepositoryに委譲

### 本文生成ロジック

#### `[TIDE]` セクション

```python
def _format_tide_section(tide: Tide) -> str:
    """[TIDE]セクションの生成
    
    Args:
        tide: 潮汐データ
    
    Returns:
        [TIDE]セクションの文字列
    """
    lines = []
    
    # 満潮のリスト
    high_tides = [e for e in tide.events if e.event_type == "high"]
    high_times = ", ".join([
        f"{e.time.strftime('%H:%M')} ({int(e.height_cm)}cm)"
        for e in high_tides
    ])
    lines.append(f"- 満潮: {high_times}")
    
    # 干潮のリスト
    low_tides = [e for e in tide.events if e.event_type == "low"]
    low_times = ", ".join([
        f"{e.time.strftime('%H:%M')} ({int(e.height_cm)}cm)"
        for e in low_tides
    ])
    lines.append(f"- 干潮: {low_times}")
    
    # 時合い帯
    if tide.prime_time_start and tide.prime_time_end:
        prime_time = (
            f"{tide.prime_time_start.strftime('%H:%M')}-"
            f"{tide.prime_time_end.strftime('%H:%M')}"
        )
        lines.append(f"- 時合い: {prime_time}")
    
    return "\n".join(lines)
```

#### イベントタイトル

```python
title = f"潮汐 {location.name} ({tide.tide_type.value})"
```

#### 完全な本文

```python
def _build_description(tide: Tide, existing_notes: str | None) -> str:
    """イベント本文を構築
    
    Args:
        tide: 潮汐データ
        existing_notes: 既存の[NOTES]セクション（存在する場合）
    
    Returns:
        完全なイベント本文
    """
    sections = [
        f"[TIDE]\n{_format_tide_section(tide)}",
        "\n[FORECAST]\n（フェーズ2で追加予定）",
    ]
    
    if existing_notes:
        sections.append(f"\n[NOTES]\n{existing_notes}")
    else:
        sections.append("\n[NOTES]\n（ユーザー手動追記欄）")
    
    return "\n".join(sections)
```

---

## テスト計画

### 単体テスト (tests/unit/application/usecases/)

#### テストケース一覧

1. **正常系**
   - `test_execute_creates_new_event`: 新規イベント作成
   - `test_execute_updates_existing_event`: 既存イベント更新
   - `test_execute_preserves_notes_section`: [NOTES]セクション保持

2. **境界値・特殊ケース**
   - `test_execute_with_single_high_tide`: 満潮が1回のみ
   - `test_execute_with_no_prime_time`: 時合い帯なし
   - `test_execute_with_multiple_high_tides`: 満潮が複数回

3. **異常系**
   - `test_execute_raises_on_tide_data_error`: 潮汐データ取得失敗
   - `test_execute_raises_on_calendar_error`: カレンダー更新失敗

#### Mockの利用

```python
from unittest.mock import Mock

# Mockリポジトリの準備
mock_tide_repo = Mock(spec=ITideDataRepository)
mock_calendar_repo = Mock(spec=ICalendarRepository)

# 潮汐データのMock
mock_tide_repo.get_tide_data.return_value = Tide(...)

# UseCaseの実行
usecase = SyncTideUseCase(mock_tide_repo, mock_calendar_repo)
usecase.execute(location, target_date)

# 検証
mock_tide_repo.get_tide_data.assert_called_once_with(location, target_date)
mock_calendar_repo.upsert_event.assert_called_once()
```

### 統合テスト（オプション）

- 実リポジトリを使用してエンドツーエンドの動作を確認
- T-013 (E2Eテスト) で代替可能

---

## 検証手順

### コード品質チェック

```bash
# フォーマット
uv run ruff format .

# Lintチェック
uv run ruff check .

# 型チェック
uv run pyright

# テスト実行
uv run pytest tests/unit/application/usecases/test_sync_tide_usecase.py -v
```

### 動作確認（手動）

1. **テストカレンダーの準備**
   - Google カレンダーでテスト用カレンダーを作成
   - `config/config.yaml` にカレンダーIDを設定

2. **UseCaseの実行**（Pythonスクリプト）
   ```python
   from datetime import date
   from fishing_forecast_gcal.domain.models.location import Location
   from fishing_forecast_gcal.infrastructure.adapters.tide_calculation_adapter import TideCalculationAdapter
   from fishing_forecast_gcal.infrastructure.repositories.tide_data_repository import TideDataRepository
   from fishing_forecast_gcal.infrastructure.repositories.calendar_repository import CalendarRepository
   from fishing_forecast_gcal.infrastructure.clients.google_calendar_client import GoogleCalendarClient
   from fishing_forecast_gcal.application.usecases.sync_tide_usecase import SyncTideUseCase
   
   # リポジトリのセットアップ
   adapter = TideCalculationAdapter(harmonics_dir="config/harmonics")
   tide_repo = TideDataRepository(adapter)
   
   calendar_client = GoogleCalendarClient(
       credentials_path="config/credentials.json",
       token_path="config/token.json",
       calendar_id="YOUR_CALENDAR_ID"
   )
   calendar_repo = CalendarRepository(calendar_client)
   
   # UseCaseの実行
   usecase = SyncTideUseCase(tide_repo, calendar_repo)
   
   location = Location(id="tokyo", name="東京湾", latitude=35.6762, longitude=139.6503)
   target_date = date(2026, 2, 10)
   
   usecase.execute(location, target_date)
   print(f"✅ Event created/updated for {location.name} on {target_date}")
   ```

3. **カレンダーで確認**
   - Google カレンダーでイベントが作成されているか確認
   - タイトル: `潮汐 東京湾 (大潮)` 等
   - 本文に `[TIDE]`, `[FORECAST]`, `[NOTES]` セクションが存在するか確認

4. **冪等性確認**
   - 同じスクリプトを再度実行
   - イベントが重複せず、更新されることを確認

---

## 実装後の確認事項

- [ ] 単体テストがすべてパス
- [ ] ruff format/check 通過
- [ ] pyright 通過
- [ ] カレンダーに正しくイベントが作成される
- [ ] 既存イベントの [NOTES] が保持される
- [ ] 冪等性が保証される（複数回実行しても重複しない）
- [ ] ログ出力が適切
- [ ] エラー時に適切な例外が発生する

---

## 依存タスク

- ✅ T-001: ドメインモデル定義
- ✅ T-002: リポジトリインターフェース定義
- ✅ T-003: 潮汐計算サービス
- ✅ T-004: 潮回り判定サービス
- ✅ T-005: 時合い帯特定サービス
- ✅ T-007: TideDataRepository 実装
- ✅ T-009: CalendarRepository 実装

---

## 次のステップ

- T-011: 設定ファイルローダー（`config.yaml` の読み込み）
- T-012: CLI エントリーポイント（コマンドライン実行）
- T-013: E2E テスト（システム全体の統合テスト）

---

## 参考資料

- [implementation_plan.md - T-010](../implementation_plan.md#t-010-synctideusecase-実装)
- [Issue #21](https://github.com/nakagawah13/fishing-forecast-gcal/issues/21)
- [domain/models/calendar_event.py](../../src/fishing_forecast_gcal/domain/models/calendar_event.py)
- [docs/completed/issue-20.md](../completed/issue-20.md) - CalendarRepository実装詳細
