# Issue #18: T-007 TideDataRepository 実装

**ステータス**: 🔵 In Progress  
**担当者**: AI  
**開始日**: 2026-02-08  
**Issue**: https://github.com/nakagawah13/fishing-forecast-gcal/issues/18

---

## 概要

潮汐データリポジトリ（`ITideDataRepository` インターフェースの実装）を作成します。
このリポジトリは、地点・日付を指定して潮汐データを取得し、Domainモデル（`Tide`）に変換して返します。

---

## 責務

Infrastructure層として、以下を担います：

1. **TideCalculationAdapter の呼び出し**: UTideライブラリから時系列潮位データを取得
2. **Domainサービスの連携**: 満干潮抽出、潮回り判定、時合い帯計算を実行
3. **Domainモデルへの変換**: 取得したデータを `Tide` モデルに変換して返す
4. **エラーハンドリング**: データ取得失敗時の適切な例外処理

---

## 実装方針

### 処理フロー

```
Location + date
    ↓
TideCalculationAdapter.calculate_tide()
    ↓ (時系列潮位データ: list[tuple[datetime, float]])
TideCalculationService.extract_high_low_tides()
    ↓ (満干潮: list[TideEvent])
PrimeTimeFinder.find()
    ↓ (時合い帯: tuple[datetime, datetime] | None)
TideTypeClassifier.classify()
    ↓ (潮回り: TideType)
Tide モデル構築
    ↓
return Tide
```

### 依存コンポーネント

- **Adapter**: `TideCalculationAdapter` (infrastructure/adapters/)
- **Domain Services**:
  - `TideCalculationService` (満干潮抽出)
  - `TideTypeClassifier` (潮回り判定)
  - `PrimeTimeFinder` (時合い帯計算)
- **Models**: `Tide`, `TideEvent`, `TideType`, `Location`

### 設計上の考慮点

1. **依存性注入**: TideCalculationAdapter を外部から注入し、テスタビリティを確保
2. **月齢の計算**: 潮回り判定には月齢が必要。簡易計算式（新月を基準とした日数差分）を使用
3. **時合い帯の計算**: 満潮が複数ある場合、時間的に中央に位置する満潮を使用
4. **エラーハンドリング**:
   - アダプター呼び出し失敗時: RuntimeError
   - 地点の調和定数が存在しない場合: FileNotFoundError

---

## 成果物

### 実装ファイル

**ファイルパス**: `src/fishing_forecast_gcal/infrastructure/repositories/tide_data_repository.py`

**クラス**: `TideDataRepository`

**メソッド**:
- `__init__(adapter: TideCalculationAdapter)`: コンストラクタ（アダプターを注入）
- `get_tide_data(location: Location, target_date: date) -> Tide`: 潮汐データ取得

**補助メソッド**:
- `_calculate_moon_age(target_date: date) -> float`: 月齢計算（簡易実装）
- `_calculate_tide_range(events: list[TideEvent]) -> float`: 潮位差計算

---

## テスト要件

### 単体テスト (tests/unit/infrastructure/repositories/test_tide_data_repository.py)

テスト対象: TideDataRepository（アダプターをモック化）

**テストケース**:

1. **正常系: 潮汐データの取得**
   - モックアダプターから正常な時系列データを返す
   - Tideモデルが正しく構築されることを確認
   - 満干潮、潮回り、時合い帯が適切に設定されていること

2. **正常系: 満潮なしの場合**
   - 時系列データに極大値がない場合
   - 時合い帯が None であることを確認

3. **異常系: アダプター呼び出し失敗**
   - アダプターが例外をスローした場合
   - RuntimeError が発生することを確認

4. **異常系: 調和定数が存在しない地点**
   - アダプターが FileNotFoundError をスローした場合
   - FileNotFoundError が伝播することを確認

### 統合テスト (tests/integration/infrastructure/test_tide_data_repository_integration.py)

テスト対象: TideDataRepository（実アダプターを使用）

**テストケース**:

1. **実データでの潮汐データ取得**
   - 実際の調和定数ファイルを使用
   - 横須賀（JMA観測地点）の2026-02-08のデータを取得
   - 満干潮が2-4個程度検出されることを確認
   - 潮回りが適切に判定されていることを確認

2. **公式潮見表との差分検証**
   - 気象庁の公式潮見表データと比較
   - 潮位差が目標の ±10cm 以内であることを確認

---

## 依存関係

- **完了している依存タスク**:
  - T-001: ドメインモデル定義（Tide, TideEvent, TideType, Location）
  - T-002: リポジトリインターフェース定義（ITideDataRepository）
  - T-003: 潮汐計算サービス（TideCalculationService）
  - T-004: 潮回り判定サービス（TideTypeClassifier）
  - T-005: 時合い帯特定サービス（PrimeTimeFinder）
  - T-006: 潮汐計算ライブラリアダプター（TideCalculationAdapter）

---

## 実装チェックリスト

### 実装

- [ ] `TideDataRepository` クラスの作成
- [ ] `__init__` メソッド（アダプター注入）
- [ ] `get_tide_data` メソッド（メインロジック）
- [ ] `_calculate_moon_age` メソッド（月齢計算）
- [ ] `_calculate_tide_range` メソッド（潮位差計算）
- [ ] Docstring の追加（Google Style）
- [ ] Type hints の追加

### テスト

- [ ] 単体テスト作成（モックアダプター使用）
- [ ] 統合テスト作成（実アダプター使用）
- [ ] 全テストパス確認

### 品質チェック

- [ ] `uv run ruff format .`
- [ ] `uv run ruff check .`
- [ ] `uv run pyright`
- [ ] `uv run pytest`

---

## 技術補足

### 月齢計算の簡易実装

月齢は新月を基準（0日）として0-29.5の範囲で表されます。
簡易的には、2000年1月6日を基準新月とし、経過日数から算出します：

```python
# 2000年1月6日 18:14 UTC が新月
MOON_CYCLE_DAYS = 29.53058867
REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

def _calculate_moon_age(target_date: date) -> float:
    target_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    days_since_ref = (target_dt - REFERENCE_NEW_MOON).total_seconds() / 86400
    moon_age = days_since_ref % MOON_CYCLE_DAYS
    return moon_age
```

### 潮位差の計算

潮位差は、その日の満潮の最大値と干潮の最小値の差として計算します：

```python
def _calculate_tide_range(events: list[TideEvent]) -> float:
    high_tides = [e for e in events if e.event_type == "high"]
    low_tides = [e for e in events if e.event_type == "low"]
    
    if not high_tides or not low_tides:
        return 0.0
    
    max_high = max(e.height_cm for e in high_tides)
    min_low = min(e.height_cm for e in low_tides)
    return max_high - min_low
```

---

## 備考

- MVP では1地点のみサポート（複数地点対応は T-021）
- 調和定数ファイルは `config/harmonics/` に配置される想定
- 月齢計算は簡易実装（実用上十分な精度）で、専用ライブラリは不使用
