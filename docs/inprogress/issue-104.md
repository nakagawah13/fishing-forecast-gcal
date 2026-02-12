# Issue #104: sync-tide の複数回実行で Google Drive にタイドグラフ画像が重複保存される

## ステータス: In Progress

## 概要

`sync-tide` コマンドを複数回実行すると、Google Drive 上に同名のタイドグラフ画像
が重複して保存される。カレンダーイベント側は `upsert_event` で冪等性を担保して
いるが、Drive アップロード側には同名ファイルの存在チェックがなく、実行ごとに
新規ファイルが作成される。

## 原因分析

### `GoogleDriveClient.upload_file()`

- `service.files().create()` で常に新規ファイルを作成
- Google Drive は同名ファイルの共存を許容するため、呼び出しのたびに重複

### `SyncTideUseCase._generate_and_upload_graph()`

- `upload_file()` を無条件に呼び出し
- 既存画像の確認や置換ロジックなし

## 修正方針

**案 A（推奨: update 方式）** を採用する。

### 実装内容

#### 1. `GoogleDriveClient` に `upload_or_update_file()` メソッドを追加

- フォルダ内で同名ファイルを `list_files()` で検索
- 存在すれば `service.files().update()` で上書き（メディアのみ更新）
- 存在しなければ従来通り `service.files().create()` で新規作成
- いずれの場合も公開読み取り権限を設定

#### 2. `SyncTideUseCase._generate_and_upload_graph()` を修正

- `upload_file()` → `upload_or_update_file()` に変更

### メリット

- ファイル ID が維持される → Calendar attachments の URL が変わらない
- 既存の `list_files()` を活用でき、最小限の変更で済む
- 冪等性が担保される

## 変更予定ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/.../infrastructure/clients/google_drive_client.py` | `upload_or_update_file()` メソッド追加 |
| `src/.../application/usecases/sync_tide_usecase.py` | `upload_file()` → `upload_or_update_file()` 呼び出し変更 |
| `tests/.../clients/test_google_drive_client.py` | `upload_or_update_file()` のテスト追加 |
| `tests/.../usecases/test_sync_tide_usecase.py` | `upload_or_update_file()` を使用するテスト修正 |

## 検証計画

1. **ユニットテスト**: `upload_or_update_file()` の新規作成パス・更新パスの分岐テスト
2. **ユニットテスト**: UseCase 側で新メソッドが呼ばれることの確認
3. **ruff / pyright**: 静的解析パス
4. **手動テスト**: `sync-tide` の複数回実行で Drive 上に重複が発生しないことを確認
