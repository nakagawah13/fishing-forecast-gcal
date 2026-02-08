# T-013.1: station_id マッピングの導入

**Status**: ✅ Completed

---

## 概要

釣行地点の不変IDと気象庁の観測地点コードを分離し、調和定数の参照を `station_id` に統一する。
これにより、カレンダー運用の安定性を維持しながら、データ取得の柔軟性を確保する。

---

## 依存関係

- ✅ T-001: ドメインモデル定義（完了）
- ✅ T-006: 潮汐計算ライブラリアダプター（完了）
- ✅ T-011: 設定ファイルローダー（完了）
- ✅ T-013: E2Eテスト（完了）

---

## 成果物

### 1. `src/fishing_forecast_gcal/domain/models/location.py`

**責務**:
- `Location` に `station_id` を追加
- 観測地点コードのバリデーション追加

### 2. `src/fishing_forecast_gcal/presentation/config_loader.py`

**責務**:
- `config.yaml` の `locations[].station_id` を必須化
- `Location` へのマッピング更新

### 3. `src/fishing_forecast_gcal/infrastructure/adapters/tide_calculation_adapter.py`

**責務**:
- 調和定数ファイルの参照キーを `station_id` に変更
- 調和定数ファイル名の小文字正規化
- ログ・エラーメッセージに `station_id` を追加

### 4. `config/config.yaml.template`

**責務**:
- `locations[].station_id` のサンプル追加

### 5. テスト更新

- `tests/unit/domain/models/test_location.py`
- `tests/unit/application/usecases/test_sync_tide_usecase.py`
- `tests/unit/domain/repositories/test_tide_data_repository.py`
- `tests/unit/domain/repositories/test_weather_repository.py`
- `tests/unit/infrastructure/repositories/test_tide_data_repository.py`
- `tests/integration/infrastructure/test_tide_data_repository_integration.py`
- `tests/e2e/conftest.py`
- `tests/e2e/test_sync_tide_flow.py`

### 6. ドキュメント更新

- `docs/潮位データ：推算値と実測値の違い.md`
  - 運用設計メモを追加

---

## テスト要件

- `Location` のバリデーション更新
- `station_id` を含むテストデータの整合性確認
- 調和定数ファイル名と `station_id` の参照一致

---

## 実装結果・変更点

### 実装完了日
2026-02-08

### 主要な変更

- `Location` に `station_id` を追加し、設定ファイルで必須化
- 調和定数の参照キーを `station_id` に統一
- 調和定数ファイル名を小文字で扱う運用に統一
- 関連テストとドキュメントを更新

### 互換性

- **破壊的変更**: `config.yaml` に `locations[].station_id` の追加が必須
- 既存の `config.yaml` は更新が必要

---

## Notes

- `station_id` は調和定数ファイル名と一致させる（例: `TK` → `tk.pkl`）
- 釣行地点IDはイベントID用に不変のまま保持する
