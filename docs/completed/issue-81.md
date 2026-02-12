# Issue #81: 古い Drive 画像の定期削除コマンド

## ステータス: ✅ Completed（2026-02-12）

## 概要

Google Drive 上の古いタイドグラフ画像を定期的に削除する CLI コマンド `cleanup-images` を実装する。
Issue #76（POC）の ST-5 に対応。Drive 容量の逼迫を防止する。

## 背景

- タイドグラフ画像は `sync-tide` 実行時に日次で生成・アップロードされる
- 古い画像が蓄積すると Google Drive 容量を圧迫する
- 保持期間を超えた画像を安全に自動削除する仕組みが必要
- 専用フォルダ（`fishing-forecast-tide-graphs`）内のみを対象とし、安全性を確保

## 実装方針

### 新規ファイル

1. **`src/fishing_forecast_gcal/application/usecases/cleanup_drive_images_usecase.py`**
   - `CleanupResult` データクラス（結果の格納）
   - `CleanupDriveImagesUseCase` クラス
     - `__init__(drive_client: GoogleDriveClient)`
     - `execute(folder_name: str, retention_days: int, dry_run: bool) -> CleanupResult`
   - 処理フロー:
     1. `drive_client.get_or_create_folder(folder_name)` でフォルダID取得
     2. `drive_client.list_files(folder_id=folder_id)` でファイル一覧取得
     3. `createdTime` と現在日時を比較し、`retention_days` を超えたファイルをフィルタ
     4. `dry_run=False` の場合のみ `drive_client.delete_file(file_id)` で削除
     5. 削除件数をログ出力・`CleanupResult` で返却

2. **`tests/unit/application/usecases/test_cleanup_drive_images_usecase.py`**
   - UseCase の単体テスト

### 変更ファイル

3. **`src/fishing_forecast_gcal/presentation/cli.py`**
   - `cleanup-images` サブコマンド追加
   - オプション: `--config`, `--retention-days`（デフォルト: 30）, `--dry-run`, `--verbose`
   - 依存オブジェクト（`GoogleDriveClient`, `CleanupDriveImagesUseCase`）の構築

4. **`tests/unit/presentation/test_cli.py`**
   - `cleanup-images` サブコマンドのパーステスト追加

## テスト要件

- [ ] 保持期間内のファイルが削除されないこと
- [ ] 保持期間を超えたファイルが削除されること
- [ ] Drive にファイルがない場合のハンドリング
- [ ] `--dry-run` で削除対象の確認のみ行えること
- [ ] 削除中のエラーが適切にハンドリングされること
- [ ] ruff / pyright パス
- [ ] 既存テストが全てパスすること

## 依存

- `GoogleDriveClient`（ST-1 で実装済み）: `list_files`, `delete_file`, `get_or_create_folder`

---

## 実装結果・変更点

### 新規作成ファイル

| ファイル | 行数 | 概要 |
|---------|------|------|
| `src/fishing_forecast_gcal/application/usecases/cleanup_drive_images_usecase.py` | 172行 | `CleanupDriveImagesUseCase` と `CleanupResult` |
| `tests/unit/application/usecases/test_cleanup_drive_images_usecase.py` | 294行 | UseCase 単体テスト 9件 |

### 変更ファイル

| ファイル | 概要 |
|---------|------|
| `src/fishing_forecast_gcal/presentation/cli.py` | `cleanup-images` サブコマンド追加（パーサー + `_run_cleanup_images` 関数） |
| `tests/unit/presentation/test_cli.py` | CLI テスト 8件追加（パーサー 4件 + main フロー 4件） |

### テスト結果

- 全 396 テストパス（1 skipped、5 deselected）
- UseCase カバレッジ: 100%
- CLI カバレッジ: 92%
- ruff check: ✅ All checks passed
- pyright: ✅ 0 errors, 0 warnings
- ruff format: ✅ Applied

### CLI 使用方法

```bash
# 30日以上前の画像を削除（デフォルト）
uv run fishing-forecast-gcal cleanup-images

# 保持日数を7日に変更
uv run fishing-forecast-gcal cleanup-images --retention-days 7

# dry-run で削除対象を確認
uv run fishing-forecast-gcal cleanup-images --dry-run

# 設定ファイルを指定
uv run fishing-forecast-gcal cleanup-images --config path/to/config.yaml
```
