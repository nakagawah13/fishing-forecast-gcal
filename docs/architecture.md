# Architecture

## 目的
- 潮汐（天文潮）を元に、満潮・干潮時刻と潮回りを Google カレンダーへ登録
- タイドグラフ画像を生成し、カレンダーへ埋め込み
- 直前の予報値（風速など）を自動更新できる仕組みを備える

## アーキテクチャパターン

### レイヤードアーキテクチャの採用

本プロジェクトでは **レイヤードアーキテクチャ（多層アーキテクチャ）** を採用します。

**採用理由**:
1. **責務の明確化**: 外部API連携、ビジネスロジック、ユースケース実装を分離
2. **保守性の向上**: 層を跨いだ変更の影響範囲を限定
3. **テスト容易性**: 各層を独立してテスト可能
4. **将来拡張**: 複数地点対応、Web UI追加時の柔軟性
5. **依存性逆転の原則**: Domain層が外部ライブラリに依存しない

**代替案との比較**:

| パターン | 適合性 | 理由 |
|---------|--------|------|
| レイヤード | ✅ **採用** | バッチ処理、複数外部API連携、ドメインロジックの複雑性に適合 |
| ヘキサゴナル | △ 過剰 | ドメインが十分複雑でないため、ヘキサゴナルは過剰設計 |
| MVC | ❌ 不適合 | Web UIがMVPに含まれず、バッチ処理が主体 |
| モノリシックなスクリプト | ❌ 不適合 | 将来の複数地点対応、Web UI追加時にリファクタリングが困難 |

---

## 多層アーキテクチャの詳細

```
┌────────────────────────────────────────┐
│  Presentation Layer                      │
│  - CLIインターフェース                        │
│  - 設定ファイル管理                        │
│  - スケジューラー起動                       │
└────────────────────────────────────────┘
           │
           ↓ 呼び出し
┌────────────────────────────────────────┐
│  Application Layer                       │
│  - ユースケース実装                         │
│    - SyncTideUseCase                     │
│    - SyncWeatherUseCase                  │
│  - バッチオーケストレーション                 │
└────────────────────────────────────────┘
           │
           ↓ 呼び出し
┌────────────────────────────────────────┐
│  Domain Layer                            │
│  - ドメインモデル                          │
│    - Tide, TideEvent, TideType           │
│    - FishingCondition                    │
│    - CalendarEvent                       │
│  - ドメインサービス                        │
│    - TideCalculationService              │
│    - TideTypeClassifier                  │
│    - PrimeTimeFinder                     │
│  - リポジトリインターフェース            │
│    - ITideDataRepository                 │
│    - IWeatherRepository                  │
│    - ICalendarRepository                 │
└────────────────────────────────────────┘
           ↑
           │ 実装（依存性逆転）
┌────────────────────────────────────────┐
│  Infrastructure Layer                    │
│  - 外部API連携                             │
│    - GoogleCalendarClient                │
│    - WeatherApiClient                    │
│  - データソース                            │
│    - TideCalculationLibraryAdapter       │
│  - リポジトリ実装                        │
│    - TideDataRepository                  │
│    - WeatherRepository                   │
│    - CalendarRepository                  │
└────────────────────────────────────────┘
```

---

## 各層の責務

### 1. Presentation Layer（プレゼンテーション層）

**責務**:
- ユーザー入力の受け付け（CLI引数、設定ファイル）
- スケジューラーの起動とバッチ実行
- ログ出力、エラー表示
- 設定の読み込みと検証

**コンポーネント**:
- `cli.py`: CLIエントリーポイント
- `scheduler.py`: APSchedulerを使用したバッチスケジュール管理
- `config_loader.py`: `config.yaml` の読み込み

**依存先**: Application Layer

**重要な原則**:
- ビジネスロジックを含まない（Application/Domain層に委譲）
- 外部APIへの直接アクセスを行わない

---

### 2. Application Layer（アプリケーション層）

**責務**:
- ユースケースの実装（ビジネスフローのオーケストレーション）
- 複数のドメインサービスとリポジトリの組み合わせ
- トランザクション管理（冗等性保証）
- エラーハンドリングとリトライ

**コンポーネント**:

#### `SyncTideUseCase`
月次の天文潮同期処理

```python
class SyncTideUseCase:
    def __init__(
        self,
        tide_repo: ITideDataRepository,
        calendar_repo: ICalendarRepository,
        tide_classifier: TideTypeClassifier,
        prime_time_finder: PrimeTimeFinder
    ):
        ...

    def execute(self, start_date: date, end_date: date, location: Location) -> None:
        # 1. 天文潮データ取得
        # 2. 満潮・干潮時刻抽出
        # 3. 潮回り判定
        # 4. 時合い帯計算
        # 5. Google カレンダーイベント作成/更新
        ...
```

#### `SyncWeatherUseCase`
気象予報の更新処理

```python
class SyncWeatherUseCase:
    def __init__(
        self,
        weather_repo: IWeatherRepository,
        calendar_repo: ICalendarRepository
    ):
        ...

    def execute(self, start_date: date, end_date: date, location: Location) -> None:
        # 1. 予報データ取得
        # 2. 既存カレンダーイベント取得
        # 3. 予報セクションを更新
        # 4. イベント更新
        ...
```

**依存先**: Domain Layer, Infrastructure Layer（インターフェース経由）

**重要な原則**:
- Domain層のインターフェースに依存（具体的な実装に依存しない）
- ビジネスロジックはDomain層に委譲
- 外部システムの詳細を知らない

---

### 3. Domain Layer（ドメイン層）

**責務**:
- ドメインモデルの定義
- ビジネスルールの実装
- ドメインサービスの実装
- リポジトリインターフェースの定義

**コンポーネント**:

#### ドメインモデル

```python
@dataclass
class Tide:
    """1日の潮汐情報"""
    date: date
    tides: List[TideEvent]  # 満潮・干潮のリスト
    tide_type: TideType  # 大潮・中潮・小潮

@dataclass
class TideEvent:
    """個々の満潮または干潮"""
    time: datetime
    height: float  # 潮位（cm）
    event_type: Literal["high", "low"]  # 満潮/干潮

class TideType(Enum):
    """潮回りの種類"""
    SPRING = "大潮"
    INTERMEDIATE = "中潮"
    NEAP = "小潮"

@dataclass
class FishingCondition:
    """釣行条件"""
    wind_speed: float  # m/s
    wind_direction: str
    pressure: float  # hPa
    is_fishable: bool  # 釣行可否

@dataclass
class CalendarEvent:
    """カレンダーイベント"""
    event_id: str
    title: str
    date: date
    description: str
    location_name: str
```

#### ドメインサービス

```python
class TideCalculationService:
    """潮汐計算サービス"""
    def extract_high_low_tides(self, tide_data: List[float], timestamps: List[datetime]) -> List[TideEvent]:
        # 満潮・干潮を抽出
        ...

class TideTypeClassifier:
    """潮回り判定サービス"""
    def classify(self, tide_range: float, moon_age: float) -> TideType:
        # 大潮・中潮・小潮を判定
        ...

class PrimeTimeFinder:
    """時合い帯特定サービス"""
    def find(self, high_tides: List[TideEvent], offset_hours: int = 2) -> List[Tuple[datetime, datetime]]:
        # 満潮前後の時合い帯を計算
        ...
```

#### リポジトリインターフェース

```python
class ITideDataRepository(ABC):
    @abstractmethod
    def get_tide_data(self, location: Location, start: date, end: date) -> List[Tide]:
        ...

class IWeatherRepository(ABC):
    @abstractmethod
    def get_forecast(self, location: Location, start: datetime, end: datetime) -> List[FishingCondition]:
        ...

class ICalendarRepository(ABC):
    @abstractmethod
    def create_event(self, event: CalendarEvent) -> str:
        ...

    @abstractmethod
    def update_event(self, event_id: str, event: CalendarEvent) -> None:
        ...

    @abstractmethod
    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        ...
```

**依存先**: なし（外部ライブラリに依存しない）

**重要な原則**:
- 外部ライブラリに依存しない（標準ライブラリのみ使用）
- ビジネスルールを一箇所に集約
- テストが容易（モック不要）

---

### 4. Infrastructure Layer（インフラストラクチャ層）

**責務**:
- 外部APIとの通信
- データソースへのアクセス
- ライブラリのラッパー
- リポジトリインターフェースの実装

**コンポーネント**:

#### `GoogleCalendarClient`
Google Calendar APIのラッパー

```python
class GoogleCalendarClient:
    def __init__(self, credentials_path: str):
        # OAuth2認証
        ...

    def create_event(self, calendar_id: str, event_data: dict) -> str:
        # API呼び出し
        ...
```

#### `WeatherApiClient`
気象APIのラッパー

```python
class WeatherApiClient:
    def __init__(self, base_url: str):
        ...

    def get_forecast(self, lat: float, lon: float, date: date) -> dict:
        # API呼び出し、レートリミット対応
        ...
```

#### `TideCalculationLibraryAdapter`
潮汐計算ライブラリのアダプター

```python
class TideCalculationLibraryAdapter:
    def calculate(self, lat: float, lon: float, start: datetime, end: datetime) -> List[float]:
        # ライブラリ呼び出し
        ...
```

#### リポジトリ実装

```python
class TideDataRepository(ITideDataRepository):
    def __init__(self, adapter: TideCalculationLibraryAdapter):
        self.adapter = adapter

    def get_tide_data(self, location: Location, start: date, end: date) -> List[Tide]:
        # アダプターを使用してDomainモデルに変換
        ...

class WeatherRepository(IWeatherRepository):
    def __init__(self, client: WeatherApiClient):
        self.client = client

    def get_forecast(self, location: Location, start: datetime, end: datetime) -> List[FishingCondition]:
        # APIクライアントを使用してDomainモデルに変換
        ...

class CalendarRepository(ICalendarRepository):
    def __init__(self, client: GoogleCalendarClient):
        self.client = client

    def create_event(self, event: CalendarEvent) -> str:
        # DomainモデルをGoogle Calendar API形式に変換
        ...
```

**依存先**: Domain Layer（インターフェースのみ）

**重要な原則**:
- Domain層のインターフェースを実装（依存性逆転）
- 外部システムの詳細をカプセル化
- エラーハンドリングとリトライ

---

## 依存性の方向

```
Presentation → Application → Domain ← Infrastructure
```

**依存性逆転の原則**:
- Infrastructure層がDomain屢のインターフェースを実装
- Domain層は具体的な実装を知らない
- テスト時にMock実装に簡単に差し替え可能

## データフロー

### Sync-Tide（月次実行）
```
1. Presentation：Scheduler が SyncTideUseCase を呼び出し
   ↓
2. Application：SyncTideUseCase が処理開始
   ↓
3. Infrastructure: TideDataRepository がデータ取得
   ↓
4. Domain: TideCalculationService が満干潮抽出
   ↓
5. Domain: TideTypeClassifier が潮回り判定
   ↓
6. Domain: PrimeTimeFinder が時合い帯計算
   ↓
7. Application: CalendarEvent モデルを構築
   ↓
8. Infrastructure: CalendarRepository がイベント作成/更新
```

### Sync-Weather（3時間ごと実行）
```
1. Presentation：Scheduler が SyncWeatherUseCase を呼び出し
   ↓
2. Application：SyncWeatherUseCase が処理開始
   ↓
3. Infrastructure: WeatherRepository が予報データ取得
   ↓
4. Infrastructure: CalendarRepository が既存イベント取得
   ↓
5. Application: 予報セクションを更新（テキスト置換）
   ↓
6. Infrastructure: CalendarRepository がイベント更新
```

## 更新ポリシー

| バッチ名 | 実行間隔 | 対象期間 | 内容 | 責務 |
|----------|---------|---------|------|------|
| Sync-Tide | 月次（1日1日） | 今日〜`tide_register_months`先 | 天文潮イベントを作成/更新 | Application: SyncTideUseCase |
| Sync-Weather | 3時間ごと | 今日〜`forecast_window_days` | 予報情報を本文の予報セクションに反映 | Application: SyncWeatherUseCase |

### Sync-Tideの詳細
- **目的**: 長期的な潮汐情報を事前登録
- **トリガー**: スケジューラー（月初自動実行）またはCLI手動実行
- **冗等性**: 同一イベントIDで upsert
- **失敗時**: リトライロジックと通知

### Sync-Weatherの詳細
- **目的**: 直前の気象予報を反映
- **トリガー**: スケジューラー（3時間ごと自動実行）
- **優先時間帯**: `high_priority_hours` （早朝・夜間）は更新頻度を上げる（將来拡張）
- **差分更新**: 予報セクションのみを上書き（手動追記を保持）

## 非機能要件（概要）
- API 失敗時のリトライ
- 予報値更新の差分更新
- ログと再実行性

## MVP のイベント設計（たたき台）
- タイトル: `潮汐 | {地点名}`
- 日時: 終日イベント（詳細時刻は説明文に記載）
- 本文: 満潮/干潮時刻、潮回り、更新日時
- タイムゾーン: 設定ファイルで固定（デフォルトは `Asia/Tokyo`）
- 更新方針: イベント ID を保持し、同一キーで差分更新
- 通知: 既定はオフ（必要ならユーザーが有効化）

本文の更新方針:
- 自動生成セクションを分離し、その範囲のみを上書き
- セパレーター例: `=== AUTO GENERATED BELOW ===`

本文テンプレ（例）:
```
満潮: 05:12 / 17:44
干潮: 11:33 / 23:58
潮回り: 大潮
更新: 2026-02-07 09:00
```

イベントキー（例）:
- `{日付}_{地点名}_{タイプ}`
   - `20251027_Kawasaki_daily`

将来拡張の方針:
- 満干潮の時刻イベントは別カレンダーに分離（レイヤー運用）
- 点イベントではなく「時合い」帯で登録する（満潮前後 2 時間）

## 冪等性方針（重複防止）
- イベント ID を日付 + 地点から決定し、同一 ID で upsert
- Google カレンダー API の ID 制約に合わせ、文字種/長さを正規化
- 実装は `md5({date}_{location}_{type}).hexdigest()` を基本案とする
- 失敗時の復旧用に `extendedProperties` へキーを保存
