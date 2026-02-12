# Issue #101: 時合い帯が最初の満潮のみ計算され、2回目が欠落する

## ステータス: Done

## 概要

1日に2回訪れる満潮それぞれに対して時合い帯（満潮±2時間）が計算されるべきだが、
現在は最初の満潮のみを基準に1回分の時合いしか計算・表示されていない。

## 原因分析

`PrimeTimeFinder.find()` が `tuple[datetime, datetime] | None` を返す設計になっており、
最初の満潮のみを使用している。この単一値の設計が `Tide` モデル、
`SyncTideUseCase`、`TideGraphRenderer` に波及している。

## 変更方針

### 1. `PrimeTimeFinder.find()` の修正
- **Before**: `tuple[datetime, datetime] | None` を返す（最初の満潮のみ）
- **After**: `list[tuple[datetime, datetime]]` を返す（すべての満潮に対応）
- 満潮がない場合は空リストを返す

### 2. `Tide` モデルの修正
- **Before**: `prime_time_start: datetime | None`, `prime_time_end: datetime | None`
- **After**: `prime_times: list[tuple[datetime, datetime]]`
- バリデーション: 各タプルの `start < end` を確認

### 3. `TideDataRepository.get_tide_data()` の修正
- `PrimeTimeFinder.find()` の戻り値を新しい `prime_times` フィールドに設定

### 4. `SyncTideUseCase._format_tide_section()` の修正
- 複数の時合い帯をカンマ区切り or 改行で表示

### 5. `SyncTideUseCase._generate_and_upload_graph()` の修正
- `prime_time` 引数を `list[tuple[datetime, datetime]] | None` に変更

### 6. `ITideGraphService` Protocol の修正
- `prime_time` パラメータの型を `list[tuple[datetime, datetime]] | None` に変更

### 7. `TideGraphRenderer` の修正
- `generate_graph()` の `prime_time` を複数対応
- `_plot_prime_time_band()` を複数バンド描画に対応

### 8. 全テストの更新
- `test_prime_time_finder.py`: 複数時合い帯の返却テスト追加
- `test_sync_tide_usecase.py`: 複数時合い帯の表示テスト追加
- `test_tide_graph_renderer.py`: 複数バンド描画テスト追加
- `Tide` モデルテスト: `prime_times` フィールドのバリデーションテスト

## 影響ファイル

- `src/.../domain/services/prime_time_finder.py`
- `src/.../domain/models/tide.py`
- `src/.../domain/services/tide_graph_service.py`
- `src/.../infrastructure/repositories/tide_data_repository.py`
- `src/.../infrastructure/services/tide_graph_renderer.py`
- `src/.../application/usecases/sync_tide_usecase.py`
- `tests/unit/domain/services/test_prime_time_finder.py`
- `tests/unit/domain/models/test_tide.py`
- `tests/unit/infrastructure/services/test_tide_graph_renderer.py`
- `tests/unit/application/usecases/test_sync_tide_usecase.py`
- `tests/unit/infrastructure/repositories/test_tide_data_repository.py`

## 検証計画

1. ユニットテストで複数の満潮に対する時合い帯計算を検証
2. カレンダー説明文に複数の時合い帯が出力されることを確認
3. タイドグラフ画像に複数のハイライトバンドが描画されることを確認
4. 満潮が1つのケース（既存互換）のリグレッションテスト
5. 満潮が0個のケースの動作確認
6. `ruff format`, `ruff check`, `pyright`, `pytest` の全パス

## 実装結果

- 全6ソースファイル + 6テストファイルを修正
- `ruff format`: 通過
- `ruff check`: 通過
- `pyright`: 0 errors
- `pytest`: 441 passed, 0 failed
