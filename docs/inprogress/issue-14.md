# Issue #14: T-003 潮汐計算サービス

## ステータス
🔵 In Progress

## 概要
潮汐データ（時系列の潮位データ）から満潮・干潮を計算・抽出するドメインサービスを実装します。

## 責務
- 連続的な時系列潮位データから満潮（極大値）・干潮（極小値）を検出
- 検出した満干潮を `TideEvent` のリストとして返す

## 実装方針

### 入力データ形式
```python
List[Tuple[datetime, float]]  # (時刻, 潮位cm)
```
- 時刻は timezone-aware な datetime
- 潮位の単位は cm
- データは時系列順にソート済みと想定

### 出力形式
```python
List[TideEvent]  # 満干潮のリスト（時系列順）
```

### アルゴリズム
1. **極値検出**: 前後の値と比較して局所的な極大値・極小値を検出
   - 極大値: `data[i-1] < data[i] > data[i+1]`
   - 極小値: `data[i-1] > data[i] < data[i+1]`

2. **分類**: 極大値を満潮（"high"）、極小値を干潮（"low"）として分類

3. **バリデーション**: 検出した潮位が有効範囲（0-500cm）内か確認

### エッジケース対応
- **データ不足（3点未満）**: 空リストを返す
- **フラット（全て同じ値）**: 空リストを返す
- **範囲外の潮位**: 警告ログを出力し、その極値をスキップ

## 変更予定ファイル

### 新規作成
- `src/fishing_forecast_gcal/domain/services/tide_calculation_service.py`
  - `TideCalculationService` クラス
  - `extract_high_low_tides(data: List[Tuple[datetime, float]]) -> List[TideEvent]` メソッド

### テスト
- `tests/unit/domain/services/test_tide_calculation_service.py`
  - 正常系: 典型的な潮汐データから満干潮を抽出
  - エッジケース1: データ不足（0点、1点、2点）
  - エッジケース2: フラットなデータ（全て同じ値）
  - エッジケース3: 範囲外の潮位（負の値、500cm超）
  - エッジケース4: 極値が連続する場合

## 検証計画
1. ユニットテストの実装と実行
2. `uv run pytest tests/unit/domain/services/test_tide_calculation_service.py -v`
3. カバレッジ確認: 100% を目指す
4. `uv run ruff check .` でLintチェック
5. `uv run pyright` で型チェック

## 依存関係
- ✅ T-001: ドメインモデル定義（完了）

## 参照
- [implementation_plan.md](../implementation_plan.md#t-003-潮汐計算サービス)
- [Issue #14](https://github.com/nakagawah13/fishing-forecast-gcal/issues/14)
