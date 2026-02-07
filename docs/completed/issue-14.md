# Issue #14: T-003 潮汐計算サービス

## ステータス
✅ Completed (2026-02-08)

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

---

## 実装結果・変更点

### 実装完了日
2026-02-08

### 実装したファイル

#### 1. `src/fishing_forecast_gcal/domain/services/tide_calculation_service.py`
- `TideCalculationService` クラスを実装
- `extract_high_low_tides()` メソッドで時系列潮位データから満干潮を抽出
- 前後の値と比較して局所的な極大値（満潮）・極小値（干潮）を検出
- 範囲外の潮位（0-500cm外）は警告ログを出力してスキップ
- データ不足（3点未満）やフラットなデータは空リストを返す

#### 2. `src/fishing_forecast_gcal/domain/services/__init__.py`
- `TideCalculationService` をエクスポート

#### 3. `tests/unit/domain/services/test_tide_calculation_service.py`
- 8つのテストケースを実装
  - 典型的なデータからの満干潮抽出
  - 空データ、データ不足（1点、2点）
  - フラットなデータ
  - 範囲外の潮位を含むデータ
  - 時系列順の保持
  - 極値が連続する場合

### テスト結果
- **テスト数**: 8件（全てパス）
- **カバレッジ**: 100%（TideCalculationService）
- **全体テスト**: 75件全てパス、全体カバレッジ60%

### 品質チェック結果
- ✅ `uv run ruff format .`: 2ファイルをフォーマット
- ✅ `uv run ruff check .`: エラーなし（自動修正適用後）
- ✅ `uv run pyright`: エラーなし
- ✅ `uv run pytest`: 75テスト全てパス

### コミット履歴
1. `bd63ef9`: feat(domain): add TideCalculationService for extracting high/low tides
2. `c1a7314`: fix(domain): address linting and type check issues in TideCalculationService

### 学びと改善点
- **アルゴリズムの妥当性**: 単純な前後比較アルゴリズムで十分に極値検出が可能
- **エッジケース対応**: データ不足、範囲外の値、フラットなデータなど、実運用で遭遇しうるケースをカバー
- **テスト駆動開発**: テストを先に書くことで実装の方向性が明確になった
- **型安全性**: `Literal["high", "low"]` を使用して型安全性を確保
- **ログ活用**: 範囲外の潮位検出時に警告ログを出力し、デバッグを容易に

### 次のステップ
- T-004: 潮回り判定サービス（依存: T-001）
- T-005: 時合い帯特定サービス（依存: T-001）
- T-006: 潮汐計算ライブラリアダプター（依存: T-002）
