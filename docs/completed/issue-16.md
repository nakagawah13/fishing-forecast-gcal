# Issue #16: T-005 時合い帯特定サービス

**ステータス**: In Progress  
**開始日**: 2026-02-08  
**担当**: AI Assistant  
**Epic**: Phase 1.1 - Domain Layer

## 概要

満潮前後の時合い帯を計算するドメインサービスを実装します。
時合い帯とは、満潮の前後2時間を指し、魚の活性が高まる時間帯として釣行計画に重要な指標となります。

## 責務

- 満干潮のリストから満潮時刻を特定
- 満潮時刻から±2時間を計算
- 日付を跨ぐケースに対応

## 成果物

### 実装ファイル

- `src/fishing_forecast_gcal/domain/services/prime_time_finder.py`
  - `PrimeTimeFinder` クラス
  - `find()` メソッド

### テストファイル

- `tests/unit/domain/services/test_prime_time_finder.py`
  - 満潮時刻から正しく±2時間を計算
  - 複数の満潮がある場合（最初の満潮を使用）
  - 日付を跨ぐ場合のテスト（23時の満潮など）
  - 満潮がない場合（Noneを返す）

## 依存関係

- **依存**: T-001（ドメインモデル定義）✅ 完了

## 設計方針

### インターフェース

```python
class PrimeTimeFinder:
    """時合い帯特定サービス"""
    
    def find(
        self, 
        events: list[TideEvent]
    ) -> tuple[datetime, datetime] | None:
        """満潮前後の時合い帯を計算
        
        Args:
            events: 満干潮のリスト（時系列順）
            
        Returns:
            (開始時刻, 終了時刻) または None（満潮がない場合）
        """
```

### 実装詳細

1. **満潮の特定**
   - eventsから `event_type == "high"` を抽出
   - 複数ある場合は最初の満潮を使用

2. **時合い帯の計算**
   - 開始時刻: 満潮時刻 - 2時間
   - 終了時刻: 満潮時刻 + 2時間
   - timedelta(hours=2) を使用

3. **エッジケース**
   - 満潮がない場合: Noneを返す
   - 日付を跨ぐ場合: datetimeが自動的に処理

### 既存コードとの統合

- `Tide` モデルは既に `prime_time_start` と `prime_time_end` 属性を持つ
- このサービスは、TideEventリストから時合い帯の時刻を計算するロジックを提供
- 将来的には `SyncTideUseCase` 内で使用される

## テスト計画

### ユニットテスト

| テストケース | 入力 | 期待出力 | 観点 |
|------------|------|---------|------|
| 基本ケース | 12:00満潮 | (10:00, 14:00) | ±2時間の計算 |
| 複数満潮 | 06:00満潮, 18:00満潮 | (04:00, 08:00) | 最初の満潮を使用 |
| 日付跨ぎ（前） | 01:00満潮 | (前日23:00, 03:00) | 日付境界の処理 |
| 日付跨ぎ（後） | 23:00満潮 | (21:00, 翌日01:00) | 日付境界の処理 |
| 満潮なし | 干潮のみ | None | エッジケース |
| 空リスト | [] | None | エッジケース |

### カバレッジ目標

- ライン: 100%
- ブランチ: 100%

## 実装手順

1. `prime_time_finder.py` を作成
2. `PrimeTimeFinder` クラスと `find()` メソッドを実装
3. `test_prime_time_finder.py` を作成
4. テストケースを実装
5. `pytest` で全テスト通過を確認
6. `ruff format`, `ruff check`, `pyright` で品質チェック

## 参照

- [implementation_plan.md](../implementation_plan.md#t-005-時合い帯特定サービス)
- [Issue #16](https://github.com/nakagawah13/fishing-forecast-gcal/issues/16)
- 既存サービス: `tide_calculation_service.py`, `tide_type_classifier.py`
