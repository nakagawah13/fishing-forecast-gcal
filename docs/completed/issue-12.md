# Issue #12: T-001 ドメインモデル定義

## ステータス
**Completed**  
開始日: 2026-02-08  
完了日: 2026-02-08

---

## 概要
ビジネスロジックの中心となるデータ構造（ドメインモデル）を定義します。レイヤードアーキテクチャのDomain層の基礎となります。

---

## 実装方針

### 設計原則
1. **不変性の重視**: dataclassで `frozen=True` を活用し、不変オブジェクトとして設計
2. **型安全性**: Python 3.11+ の型ヒント（PEP 604: Union types with `|`）を使用
3. **バリデーション**: 不正な値を即座に検出し、コンストラクタで例外を発生
4. **テスト容易性**: 外部依存なし、純粋なデータクラス
5. **ドメイン言語**: ビジネス用語（潮汐、釣行条件、時合い帯）を反映

### 既存構造の確認
- `src/fishing_forecast_gcal/domain/models/__init__.py` は存在（空実装）
- 各モデルファイルを新規作成

---

## 成果物の詳細

### 1. `domain/models/tide.py`

#### クラス定義

**`TideType` (Enum)**:
```python
class TideType(Enum):
    """潮回りの種類"""
    SPRING = "大潮"    # 満月・新月付近
    MODERATE = "中潮"  # 上弦・下弦付近
    NEAP = "小潮"      # 中間期
    LONG = "長潮"      # 小潮の翌日
    YOUNG = "若潮"     # 長潮の翌日
```

**`TideEvent`**:
- 満潮・干潮の1回分のイベント
- フィールド:
  - `time: datetime` - 発生時刻（timezone aware）
  - `height_cm: float` - 潮位（cm単位）
  - `event_type: Literal["high", "low"]` - 満潮/干潮の区別
- バリデーション:
  - `height_cm`: 0 ~ 500cm の範囲内（異常値検出）
  - `time`: timezone が設定されていること

**`Tide`**:
- 1日分の潮汐情報
- フィールド:
  - `date: datetime.date` - 対象日
  - `tide_type: TideType` - 潮回り
  - `events: list[TideEvent]` - 満干潮のリスト（時系列順）
  - `prime_time_start: datetime | None` - 時合い帯開始時刻
  - `prime_time_end: datetime | None` - 時合い帯終了時刻
- バリデーション:
  - `events`: 空でないこと、時系列順であること
  - `prime_time_start` と `prime_time_end`: 両方nullまたは両方non-null

---

### 2. `domain/models/fishing_condition.py`

#### クラス定義

**`FishingCondition`**:
- 釣行条件（気象予報情報）
- フィールド:
  - `wind_speed_mps: float` - 風速（m/s）
  - `wind_direction: str` - 風向（例: "北", "北北東"）
  - `pressure_hpa: float` - 気圧（hPa）
  - `forecast_time: datetime` - 予報の基準時刻
  - `warning_level: Literal["safe", "caution", "danger"]` - 注意レベル
- バリデーション:
  - `wind_speed_mps`: 0 ~ 50 m/s の範囲内
  - `pressure_hpa`: 900 ~ 1100 hPa の範囲内
  - `warning_level`: 風速から自動判定（10m/s以上で "danger"）

---

### 3. `domain/models/calendar_event.py`

#### クラス定義

**`CalendarEvent`**:
- Google カレンダーに登録するイベント
- フィールド:
  - `event_id: str` - イベントID（`calendar_id + location_id + date` から生成）
  - `title: str` - イベントタイトル（例: "潮汐 東京湾 (大潮)"）
  - `description: str` - イベント本文（Markdown形式、セクション分割）
  - `date: datetime.date` - 対象日（終日イベント）
  - `location_id: str` - 地点の不変ID
- バリデーション:
  - `event_id`: 空でないこと
  - `title`: 50文字以内
  - `description`: セクション形式（`[TIDE]`, `[FORECAST]`, `[NOTES]`）の検証

**本文フォーマット例**:
```
[TIDE]
- 満潮: 06:12 (162cm)
- 干潮: 12:34 (58cm)
- 時合い: 04:12-08:12

[FORECAST]
- 風速: 5m/s
- 風向: 北
- 気圧: 1012hPa

[NOTES]
（ユーザー手動追記欄）
```

---

### 4. `domain/models/location.py`

#### クラス定義

**`Location`**:
- 釣行地点の情報
- フィールド:
  - `id: str` - 不変ID（config.yamlの `locations[].id`）
  - `name: str` - 表示名（例: "東京湾"）
  - `latitude: float` - 緯度
  - `longitude: float` - 経度
- バリデーション:
  - `id`: 空でないこと
  - `name`: 空でないこと
  - `latitude`: -90 ~ 90 の範囲内
  - `longitude`: -180 ~ 180 の範囲内

注記:
- `id` は不変IDであり、`name` 変更時もイベントIDが変わらないようにする
- 複数地点対応はフェーズ3で実装（MVP では1地点のみ）

---

## 変更予定のファイル

| ファイルパス | 変更種別 | 内容 |
|-------------|---------|------|
| `src/fishing_forecast_gcal/domain/models/tide.py` | 新規作成 | `TideType`, `TideEvent`, `Tide` クラス定義 |
| `src/fishing_forecast_gcal/domain/models/fishing_condition.py` | 新規作成 | `FishingCondition` クラス定義 |
| `src/fishing_forecast_gcal/domain/models/calendar_event.py` | 新規作成 | `CalendarEvent` クラス定義 |
| `src/fishing_forecast_gcal/domain/models/location.py` | 新規作成 | `Location` クラス定義 |
| `src/fishing_forecast_gcal/domain/models/__init__.py` | 更新 | 各モデルをエクスポート |
| `tests/unit/domain/models/test_tide.py` | 新規作成 | `Tide` 関連クラスのテスト |
| `tests/unit/domain/models/test_fishing_condition.py` | 新規作成 | `FishingCondition` のテスト |
| `tests/unit/domain/models/test_calendar_event.py` | 新規作成 | `CalendarEvent` のテスト |
| `tests/unit/domain/models/test_location.py` | 新規作成 | `Location` のテスト |

---

## テスト計画

### テストケース一覧

#### 1. `test_tide.py`

**`TideType`**:
- [ ] 全ての列挙値が正しく定義されている
- [ ] 値が日本語の潮回り名になっている

**`TideEvent`**:
- [ ] 正常値でのインスタンス化
- [ ] 不正な `height_cm`（負値、500超過）でエラー
- [ ] timezone なしの `time` でエラー
- [ ] 不正な `event_type`（"high", "low" 以外）でエラー

**`Tide`**:
- [ ] 正常値でのインスタンス化
- [ ] `events` が空の場合にエラー
- [ ] `events` が時系列順でない場合にエラー
- [ ] `prime_time_start` のみ設定してエラー
- [ ] `prime_time_end` のみ設定してエラー

#### 2. `test_fishing_condition.py`

**`FishingCondition`**:
- [ ] 正常値でのインスタンス化
- [ ] 不正な `wind_speed_mps`（負値、50超過）でエラー
- [ ] 不正な `pressure_hpa`（900未満、1100超過）でエラー
- [ ] 不正な `warning_level` でエラー
- [ ] 風速から `warning_level` が自動判定される

#### 3. `test_calendar_event.py`

**`CalendarEvent`**:
- [ ] 正常値でのインスタンス化
- [ ] 空の `event_id` でエラー
- [ ] 空の `title` でエラー
- [ ] 50文字超の `title` でエラー
- [ ] セクション形式でない `description` で警告（または許容）

#### 4. `test_location.py`

**`Location`**:
- [ ] 正常値でのインスタンス化
- [ ] 空の `id` でエラー
- [ ] 空の `name` でエラー
- [ ] 不正な `latitude`（-90未満、90超過）でエラー
- [ ] 不正な `longitude`（-180未満、180超過）でエラー

---

## 検証計画

1. **型チェック**: `uv run pyright` ですべてのモデルの型ヒントが正しいことを確認
2. **Lintチェック**: `uv run ruff check .` でコードスタイルが規約に準拠していることを確認
3. **テスト実行**: `uv run pytest tests/unit/domain/models/` で全テストが通過
4. **カバレッジ**: 各モデルのカバレッジが95%以上であることを確認

---

## 実装順序

1. `tide.py` の基本構造（`TideType`, `TideEvent`）
2. `tide.py` の `Tide` クラス
3. `fishing_condition.py` の `FishingCondition` クラス
4. `location.py` の `Location` クラス
5. `calendar_event.py` の `CalendarEvent` クラス
6. 各テストファイルを順次作成
7. `__init__.py` でエクスポート

---

## 相談事項
- `TideEvent` の `height_cm` の上限値（500cm）は妥当か？（実際の潮位範囲を確認）
- `FishingCondition` の `warning_level` の判定基準（風速10m/s）は妥当か？
- `CalendarEvent` の `description` のセクション形式検証は必須か、それとも推奨レベルか？

---

## 実装結果・変更点

### 実装完了日
2026-02-08

### 作成したファイル
1. **ドメインモデル**:
   - `src/fishing_forecast_gcal/domain/models/tide.py` - `TideType`, `TideEvent`, `Tide` クラス
   - `src/fishing_forecast_gcal/domain/models/fishing_condition.py` - `FishingCondition` クラス
   - `src/fishing_forecast_gcal/domain/models/location.py` - `Location` クラス
   - `src/fishing_forecast_gcal/domain/models/calendar_event.py` - `CalendarEvent` クラス
   - `src/fishing_forecast_gcal/domain/models/__init__.py` - 各モデルのエクスポート

2. **テストファイル**:
   - `tests/unit/domain/models/test_tide.py` - 24テスト（TideType, TideEvent, Tide）
   - `tests/unit/domain/models/test_fishing_condition.py` - 11テスト（FishingCondition）
   - `tests/unit/domain/models/test_location.py` - 13テスト（Location）
   - `tests/unit/domain/models/test_calendar_event.py` - 16テスト（CalendarEvent）

3. **設定ファイル**:
   - `pyrightconfig.json` - 厳密な型チェック設定（src/のみ対象）
   - `pyproject.toml` - pyright設定を strict モードに更新

### 品質メトリクス
- **テスト**: 全56テストがパス（100%成功率）
- **カバレッジ**: ドメインモデル 100%
- **Lint**: ruff check クリア（0エラー）
- **型チェック**: pyright クリア（0エラー）

### 設計決定事項
1. **`TideEvent.height_cm` の上限値**: 500cm を採用（日本の潮位範囲を考慮）
2. **`FishingCondition.warning_level` の判定基準**:
   - safe: 7m/s未満
   - caution: 7m/s以上10m/s未満
   - danger: 10m/s以上
3. **`CalendarEvent.description` のセクション形式**: 推奨レベル（`has_valid_sections()` で確認可能だが必須ではない）
4. **不変性**: 全モデルで `frozen=True` を採用し、変更時は新しいインスタンスを生成

### 主要な実装ポイント
1. **バリデーション**:
   - 全モデルで `__post_init__` による厳密なバリデーション
   - timezone aware の強制（`TideEvent.time`, `FishingCondition.forecast_time`）
   - 範囲チェック（緯度・経度、潮位、風速、気圧）

2. **セクション操作**:
   - `CalendarEvent.extract_section()`: 正規表現によるセクション抽出
   - `CalendarEvent.update_section()`: イミュータブルな更新（新インスタンス生成）

3. **型安全性**:
   - Python 3.13 の Union types (`|`) を活用
   - `Literal` 型による制約（`event_type: Literal["high", "low"]`）

### コミット履歴
1. `83a663f` - feat(domain): implement core domain models
2. `5db905e` - test(domain): add comprehensive tests for domain models

### 次のタスクへの準備
T-002（リポジトリインターフェース定義）に必要なドメインモデルがすべて揃いました。

---

## 参照
- [implementation_plan.md#T-001](../implementation_plan.md#t-001-ドメインモデル定義)
- [architecture.md](../architecture.md)
- [requirements.md](../requirements.md)
- [Issue #12](https://github.com/nakagawah13/fishing-forecast-gcal/issues/12)
