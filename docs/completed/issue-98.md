# Issue #98: OAuth スコープ不一致時の再認証ハンドリング

## ステータス: Completed

## 変更概要

`token.json` の OAuth スコープが現在の `SCOPES` 定義と一致しない場合に、自動的に再認証フローを起動し、`invalid_scope: Bad Request` エラーを防止する。

## 現状の問題

1. **スコープ不一致**: T-013.13 で `SCOPES` に `drive.file` を追加したが、既存の `token.json` は Calendar スコープのみで発行済み
2. **`RefreshError` 未ハンドリング**: `creds.refresh()` で `RefreshError` が発生した場合のフォールバック処理がない
3. **ユーザーへの通知不足**: スコープ変更時にユーザーへの分かりやすいメッセージがない

## 変更計画

### Step 1: スコープ不一致検出ロジックの追加

- **対象ファイル**: `src/fishing_forecast_gcal/infrastructure/clients/google_auth.py`
- `token.json` 読み込み後、保存済みスコープと `SCOPES` 定数を比較する
- `Credentials` オブジェクトの `scopes` 属性を使用して比較
- 不一致の場合:
  - WARNING ログを出力（「スコープが変更されました。再認証が必要です。」）
  - 既存トークンを無効化（`creds = None` に設定）
  - 通常の新規認証フローにフォールバック

### Step 2: `RefreshError` のフォールバック処理

- `creds.refresh(Request())` を `try-except` で囲む
- `google.auth.exceptions.RefreshError` をキャッチ
- キャッチ時に WARNING ログを出力し、新規認証フローにフォールバック

### Step 3: テストの追加

- **対象ファイル**: `tests/unit/infrastructure/clients/test_google_auth.py`
- スコープ不一致時に再認証フローが起動されるテスト
- `RefreshError` 発生時にフォールバック再認証が起動されるテスト
- スコープ一致時は既存の動作に変更がないテスト
- WARNING ログが出力されるテスト

## 検証計画

1. ユニットテスト: スコープ不一致、`RefreshError`、正常系の各ケース
2. Lint/Format: `ruff format .` && `ruff check .`
3. 型チェック: `pyright`
4. 全テスト: `pytest`

## 影響範囲

- `infrastructure/clients/google_auth.py` — スコープ検証ロジック追加
- `tests/unit/infrastructure/clients/test_google_auth.py` — テスト追加
- 他のモジュールへの変更なし（authenticate のインターフェースは変更しない）

## 実装結果・変更点

### 変更ファイル

1. **`src/fishing_forecast_gcal/infrastructure/clients/google_auth.py`**
   - `_scopes_match(creds)` ヘルパー関数を追加: トークンのスコープと `SCOPES` 定数を比較
   - `_run_oauth_flow(creds_path)` ヘルパー関数を追加: OAuth フロー実行ロジックを抽出
   - `authenticate()` にスコープ不一致検出ロジックを追加（valid なトークンでもスコープ不足なら再認証）
   - `creds.refresh()` を `try-except RefreshError` で囲み、失敗時は再認証フローへフォールバック
   - `google.auth.exceptions.RefreshError` を新規 import

2. **`tests/unit/infrastructure/clients/test_google_auth.py`**
   - `TestScopeMismatch` クラスを追加（4テスト）
     - スコープ不一致時に再認証フロー起動
     - スコープ一致時は既存動作維持
     - WARNING ログ出力の確認
     - `scopes=None` の場合のハンドリング
   - `TestRefreshErrorFallback` クラスを追加（3テスト）
     - `RefreshError` 発生時の再認証フロー起動
     - WARNING ログ出力の確認
     - 新トークンの保存確認
   - 既存テスト `test_authenticate_with_existing_valid_token` に `scopes` 設定を追加

### テスト結果

- 全 448 テストパス、0 エラー
- pyright: 0 errors, 0 warnings
- ruff check: All checks passed
- ruff format: 適用済み
