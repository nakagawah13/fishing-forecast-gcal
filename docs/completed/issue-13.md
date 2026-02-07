# Issue #13: T-002 リポジトリインターフェース定義

## ステータス
- **状態**: ✅ Completed
- **担当**: AI Assistant
- **開始日**: 2026-02-08
- **完了日**: 2026-02-08
- **関連Issue**: [#13](https://github.com/nakagawah13/fishing-forecast-gcal/issues/13)
- **依存**: T-001 (完了済み)

## 概要
Domain層のリポジトリインターフェース（抽象基底クラス）を定義し、外部データソースへのアクセスを抽象化します。これにより、Infrastructure層の実装とDomain層を疎結合に保ち、テスト容易性を向上させます。

## 責務
- 潮汐データ、気象予報データ、カレンダーイベントへのアクセスを抽象化
- 依存性逆転の原則（DIP）に基づき、Domain層がInfrastructure層に依存しないようにする
- 型安全なインターフェースを提供し、型チェックによる品質担保

## 成果物

### 1. ITideDataRepository (`domain/repositories/tide_data_repository.py`)
**責務**: 潮汐データの取得を抽象化

**メソッド**:
- `get_tide_data(location: Location, target_date: date) -> Tide`
  - 指定地点・日付の潮汐データ（満潮・干潮・潮回り）を取得
  - 天文潮計算ライブラリまたはAPIを経由して取得（Infrastructure層で実装）

**設計方針**:
- Pythonの`abc.ABC`を使用した抽象基底クラス
- `@abstractmethod`で実装を強制
- 型ヒントを完全に記述

### 2. IWeatherRepository (`domain/repositories/weather_repository.py`)
**責務**: 気象予報データの取得を抽象化

**メソッド**:
- `get_forecast(location: Location, target_date: date) -> FishingCondition | None`
  - 指定地点・日付の気象予報を取得
  - 予報が存在しない場合は `None` を返す（遠い未来の日付など）
  - Infrastructure層で気象APIクライアントを実装

**設計方針**:
- 予報が取得できない場合の扱いを明確にする（`None`許容）
- MVP では使用しないが、Phase 2 で実装するため先行定義

### 3. ICalendarRepository (`domain/repositories/calendar_repository.py`)
**責務**: Google カレンダーイベントの作成・取得・更新を抽象化

**メソッド**:
- `get_event(event_id: str) -> CalendarEvent | None`
  - イベントIDでイベントを取得
  - 存在しない場合は `None` を返す
- `upsert_event(event: CalendarEvent) -> None`
  - イベントを作成または更新（冪等性を保証）
  - 同一IDのイベントが存在する場合は更新、存在しない場合は作成
- `list_events(start_date: date, end_date: date, location_id: str) -> list[CalendarEvent]`
  - 指定期間・地点のイベントリストを取得
  - Phase 2 の予報更新で使用

**設計方針**:
- upsert パターンで冪等性を保証（複数回実行しても結果が同じ）
- イベントIDの生成ロジックはInfrastructure層で実装

## テスト方針

### テスト要件
1. **型チェック**: `pyright` で全インターフェースの型シグネチャを検証
2. **抽象メソッドの検証**: インスタンス化を試みると `TypeError` が発生することを確認
3. **Mock実装**: テスト用のMock実装を作成し、正しく継承できることを確認

### テストファイル
- `tests/unit/domain/repositories/test_tide_data_repository.py`
- `tests/unit/domain/repositories/test_weather_repository.py`
- `tests/unit/domain/repositories/test_calendar_repository.py`

各テストで以下を検証:
- 抽象基底クラスが直接インスタンス化できないこと
- サブクラスがすべての抽象メソッドを実装していない場合、インスタンス化できないこと
- Mock実装が正しく動作すること

## 実装計画

### ステップ1: ディレクトリ構造の確認
```bash
src/fishing_forecast_gcal/domain/repositories/
├── __init__.py
├── tide_data_repository.py
├── weather_repository.py
└── calendar_repository.py
```

### ステップ2: インターフェース実装
1. `ITideDataRepository` を実装
2. `IWeatherRepository` を実装
3. `ICalendarRepository` を実装
4. `__init__.py` にエクスポートを追加

### ステップ3: テスト実装
1. 各リポジトリの単体テストを作成
2. Mock実装を作成
3. 型チェックを実行

### ステップ4: 品質チェック
```bash
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
```

## 変更予定ファイル

### 新規作成
- `src/fishing_forecast_gcal/domain/repositories/tide_data_repository.py`
- `src/fishing_forecast_gcal/domain/repositories/weather_repository.py`
- `src/fishing_forecast_gcal/domain/repositories/calendar_repository.py`
- `src/fishing_forecast_gcal/domain/repositories/__init__.py`（更新）
- `tests/unit/domain/repositories/test_tide_data_repository.py`
- `tests/unit/domain/repositories/test_weather_repository.py`
- `tests/unit/domain/repositories/test_calendar_repository.py`
- `tests/unit/domain/repositories/__init__.py`

### 更新
なし（既存ファイルの変更は不要）

## レビュー観点
1. **抽象化の妥当性**: インターフェースがDomain層の責務を適切に表現しているか
2. **型安全性**: すべてのメソッドに適切な型ヒントが付与されているか
3. **テスト網羅性**: 抽象基底クラスの特性を十分にテストしているか
4. **将来の拡張性**: Phase 2 以降の機能拡張に対応できる設計か

## 次のステップ（完了後）
- T-003: 潮汐計算サービスの実装
- T-006: 潮汐計算ライブラリアダプターの実装
- T-007: TideDataRepository の具象実装

---

## 実装結果・変更点

### 実装完了日
2026-02-08

### 作成したファイル
1. **リポジトリインターフェース**:
   - `src/fishing_forecast_gcal/domain/repositories/tide_data_repository.py` (48行)
   - `src/fishing_forecast_gcal/domain/repositories/weather_repository.py` (43行)
   - `src/fishing_forecast_gcal/domain/repositories/calendar_repository.py` (91行)
   - `src/fishing_forecast_gcal/domain/repositories/__init__.py` (14行) - エクスポート追加

2. **テストファイル**:
   - `tests/unit/domain/repositories/test_tide_data_repository.py` (87行)
   - `tests/unit/domain/repositories/test_weather_repository.py` (100行)
   - `tests/unit/domain/repositories/test_calendar_repository.py` (175行)
   - `tests/unit/domain/repositories/__init__.py` (1行)

### テスト結果
- **総テスト数**: 67件（全テスト通過）
- **新規テスト**: 11件
  - ITideDataRepository: 3件
  - IWeatherRepository: 4件
  - ICalendarRepository: 4件
- **カバレッジ**: 100%（新規作成ファイル）
- **型チェック**: エラーなし（pyright）
- **Lintチェック**: エラーなし（ruff）

### コミット履歴
1. `b7919f3` - docs: add T-002 implementation plan for repository interfaces
2. `7b82336` - feat(domain): add repository interfaces for data access abstraction
3. `d23f79e` - test(domain): add comprehensive tests for repository interfaces

### 設計上の判断・変更点

1. **Union型の採用**:
   - `FishingCondition | None` と `CalendarEvent | None` で Optional を表現
   - Python 3.10+ の新しい型表現を採用

2. **抽象基底クラスパターン**:
   - すべてのインターフェースで `abc.ABC` を継承
   - `@abstractmethod` デコレータで実装を強制
   - 直接インスタンス化を防止

3. **冪等性の明示**:
   - `ICalendarRepository.upsert_event()` は冪等操作として設計
   - 複数回実行しても結果が同じになることをドキュメント化

4. **テストでの Tide モデル修正**:
   - 当初のテストで `high_tides` / `low_tides` を使用していたが、
     実際のモデルは `events` を使用していたため修正
   - `events` リストに満潮・干潮を混在させる設計に対応

### 次のタスクへの影響
- T-003（潮汐計算サービス）: 影響なし、予定通り着手可能
- T-006（潮汐計算ライブラリアダプター）: `ITideDataRepository` の実装で使用
- T-007（TideDataRepository 実装）: `ITideDataRepository` を実装する具象クラスを作成
- T-008（Google Calendar API クライアント）: 並行して着手可能
- T-009（CalendarRepository 実装）: `ICalendarRepository` を実装する具象クラスを作成

### 所感
- レイヤードアーキテクチャの責務分離が明確になり、今後の実装がスムーズに進むと予想
- インターフェース駆動開発により、テスト容易性が向上
- Phase 2（予報更新）に向けた `IWeatherRepository` の先行定義が完了
