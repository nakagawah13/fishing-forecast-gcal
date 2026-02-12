# Issue #92: TideGraphService のレイヤー移動（Domain → Infrastructure）

## ステータス: ✅ Completed

## 変更概要

`TideGraphService` を `domain/services/` から `infrastructure/services/` に移動し、レイヤードアーキテクチャの DIP（依存性逆転原則）違反を解消する。

## 変更理由

### 現状の問題

`domain/services/tide_graph_service.py`（358行）が以下の外部ライブラリに直接依存:

- `matplotlib` — グラフ描画
- `seaborn` — スタイル設定
- `numpy` — 数値計算
- `matplotlib_fontja` — 日本語フォント

Domain 層は外部ライブラリに依存すべきでなく、ビジネスルールのみを表現する層。グラフ描画は「表示・出力」に関する責務であり、Infrastructure 層が適切。

### 付随する問題

- モジュールレベルの副作用: `matplotlib.use("Agg")`, `sns.set_theme()`, `matplotlib_fontja.japanize()` がインポート時に実行される（テストに影響）
- Domain 層が重い外部依存を持つことで、Domain 層の単体テストに matplotlib のインストールが必須になる

## 実装方針

### 方式: Domain 層に Protocol 定義 + Infrastructure 層に実装

Issue の提案通り、DIP に従って以下の構造にする:

```
domain/services/
  tide_graph_service.py      → ITideGraphService (Protocol) を定義

infrastructure/services/
  tide_graph_renderer.py     → TideGraphRenderer (実装クラス)
```

### 変更予定ファイル

#### 新規作成
- `src/fishing_forecast_gcal/infrastructure/services/__init__.py`
- `src/fishing_forecast_gcal/infrastructure/services/tide_graph_renderer.py`
  - 現 `TideGraphService` の実装をそのまま移動
  - クラス名を `TideGraphRenderer` に変更

#### 修正
- `src/fishing_forecast_gcal/domain/services/tide_graph_service.py`
  - 実装を削除し、`ITideGraphService` Protocol を定義
  - `generate_graph()` メソッドのシグネチャのみ残す
- `src/fishing_forecast_gcal/domain/services/__init__.py`
  - `TideGraphService` の export を `ITideGraphService` に変更
- `src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py`
  - import を `ITideGraphService` Protocol に変更
  - 型注釈を `ITideGraphService | None` に変更
- `src/fishing_forecast_gcal/presentation/commands/sync_tide.py`
  - import を `infrastructure/services/tide_graph_renderer.TideGraphRenderer` に変更
- `tests/unit/domain/services/test_tide_graph_service.py`
  - `tests/unit/infrastructure/services/test_tide_graph_renderer.py` に移動
  - import パスを更新
- `tests/unit/presentation/commands/test_sync_tide.py`
  - パッチパスを更新

### Protocol 設計

```python
from typing import Protocol
from datetime import date, datetime
from pathlib import Path

class ITideGraphService(Protocol):
    def generate_graph(
        self,
        target_date: date,
        hourly_heights: list[tuple[float, float]],
        tide_events: list[TideEvent],
        location_name: str,
        tide_type: TideType,
        prime_time: tuple[datetime, datetime] | None = None,
        output_dir: Path | None = None,
        location_id: str = "unknown",
    ) -> Path: ...
```

## 検証計画

1. 全既存テストがパスすること
2. ruff format / ruff check がパスすること
3. pyright 型チェックがパスすること
4. `ITideGraphService` Protocol を `TideGraphRenderer` が満たすこと
5. SyncTideUseCase が Protocol 型で受け取れること

## 実装結果・変更点

### 実施日
2026-02-12

### 変更ファイル一覧

#### 新規作成
- `src/fishing_forecast_gcal/infrastructure/services/__init__.py`
- `src/fishing_forecast_gcal/infrastructure/services/tide_graph_renderer.py` — `TideGraphRenderer` 実装（旧 `TideGraphService` の全コードを移動）
- `tests/unit/infrastructure/services/__init__.py`

#### 修正
- `src/fishing_forecast_gcal/domain/services/tide_graph_service.py` — 実装を削除し `ITideGraphService` Protocol のみを定義（358行 → 53行）
- `src/fishing_forecast_gcal/domain/services/__init__.py` — `TideGraphService` → `ITideGraphService` に export 変更
- `src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py` — import と型注釈を `ITideGraphService` Protocol に変更
- `src/fishing_forecast_gcal/presentation/commands/sync_tide.py` — import を `TideGraphRenderer`（Infrastructure 層）に変更
- `tests/unit/presentation/commands/test_sync_tide.py` — パッチパスを `TideGraphRenderer` に更新

#### 移動（git mv）
- `tests/unit/domain/services/test_tide_graph_service.py` → `tests/unit/infrastructure/services/test_tide_graph_renderer.py`

### テスト結果
- 432 passed, 1 skipped, 5 deselected
- ruff format: 107 files unchanged
- ruff check: 0 errors（import 順序を自動修正後）
- pyright: 0 errors, 0 warnings
- カバレッジ: 94%

### アーキテクチャ改善
- Domain 層から `matplotlib`, `seaborn`, `numpy`, `matplotlib_fontja` への依存を完全除去
- DIP（依存性逆転原則）に準拠: `SyncTideUseCase` は `ITideGraphService` Protocol に依存
- モジュールレベル副作用（`matplotlib.use("Agg")`, `sns.set_theme()`）を Infrastructure 層に隔離
