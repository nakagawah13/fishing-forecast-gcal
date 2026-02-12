# Issue #90: refactor: CLI モジュール分割（cli.py の責務分離）

## ステータス: ✅ Completed

## 概要

`presentation/cli.py`（600行）をコマンドごとにファイル分割し、薄いディスパッチャーに変更する。

## 変更理由

### 現状の問題
- `cli.py` は 600 行で プロジェクト最大のファイル
- 4つの責務が混在: 引数定義、メインディスパッチ、依存構築+実行、ユーティリティ
- Phase 2 で `sync-weather` コマンド追加時にさらに肥大化する
- テスト (`test_cli.py`) も 1105 行に膨らんでいる

## 実装方針

### ディレクトリ構造

```
presentation/
  cli.py                    # 薄いエントリーポイント: main(), parse_args() ディスパッチャー
  commands/
    __init__.py
    common.py               # 共通引数定義、parse_date(), setup_logging()
    sync_tide.py             # sync-tide: 引数定義 + _run_sync_tide()
    reset_tide.py            # reset-tide: 引数定義 + _run_reset_tide()
    cleanup_images.py        # cleanup-images: 引数定義 + _run_cleanup_images()
```

### 分割方針

#### 1. `common.py` に抽出するもの
- `setup_logging()` 関数
- `parse_date()` 関数
- 共通引数（`--config`, `--verbose`等）を各サブパーサーに追加するヘルパー

#### 2. 各コマンドモジュール
- `add_arguments(subparsers)`: サブパーサーの引数定義
- `run(args, config)`: コマンド実行ロジック（元の `_run_xxx` 関数）

#### 3. `cli.py` に残すもの
- `main()`: エントリーポイント。parse_args + config load + ディスパッチ
- `parse_args()`: subparsers を作成し、各コマンドの `add_arguments()` を呼ぶ
- 地点解決・期間計算のロジック（sync-tide / reset-tide で共通のため）

### 各コマンドの `run()` シグネチャ

```python
# sync_tide.py
def run(
    args: argparse.Namespace,
    config: AppConfig,
    target_locations: list[Location],
    start_date: date,
    end_date: date,
) -> None: ...

# reset_tide.py
def run(
    args: argparse.Namespace,
    settings: AppSettings,
    target_locations: list[Location],
    start_date: date,
    end_date: date,
) -> None: ...

# cleanup_images.py
def run(
    args: argparse.Namespace,
    config: AppConfig,
) -> None: ...
```

## 変更予定のファイル

### 新規作成
- `src/fishing_forecast_gcal/presentation/commands/__init__.py`
- `src/fishing_forecast_gcal/presentation/commands/common.py`
- `src/fishing_forecast_gcal/presentation/commands/sync_tide.py`
- `src/fishing_forecast_gcal/presentation/commands/reset_tide.py`
- `src/fishing_forecast_gcal/presentation/commands/cleanup_images.py`

### 修正
- `src/fishing_forecast_gcal/presentation/cli.py` — 薄いディスパッチャーに変更

### テスト
- `tests/unit/presentation/test_cli.py` — ディスパッチャーのテストに縮小
- `tests/unit/presentation/commands/test_common.py` — 新規
- `tests/unit/presentation/commands/test_sync_tide.py` — 新規
- `tests/unit/presentation/commands/test_reset_tide.py` — 新規
- `tests/unit/presentation/commands/test_cleanup_images.py` — 新規

## 検証計画

1. `uv run ruff format .` — フォーマット
2. `uv run ruff check .` — Lint
3. `uv run pyright` — 型チェック
4. `uv run pytest` — 全テスト通過
5. 既存の E2E テストが影響を受けないことを確認

## 依存タスク

- なし（既存機能のリファクタリング）

## 実装結果

### 品質チェック結果
- `uv run ruff format .` — ✅ Pass
- `uv run ruff check .` — ✅ Pass
- `uv run pyright` — ✅ Pass（0 errors）
- `uv run pytest` — ✅ Pass（89 tests passed）

### 変更サマリ
- `cli.py`: 600行 → 約200行（薄いディスパッチャー）
- 新規モジュール4つ: `common.py`, `sync_tide.py`, `reset_tide.py`, `cleanup_images.py`
- テスト分割: `test_cli.py`（1105行）→ ディスパッチャーテスト + コマンド別テスト4ファイル
- 後方互換性: `parse_date`, `setup_logging` の re-export を維持
