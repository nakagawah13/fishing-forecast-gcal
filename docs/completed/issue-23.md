# T-012: CLIエントリーポイント

**Status**: ✅ Completed

---

## 概要

コマンドラインインターフェースを実装し、ユーザーが潮汐イベント同期を実行できるようにします。
SyncTideUseCase（T-010）とConfigLoader（T-011）を統合し、実用的なCLIツールを提供します。

---

## 依存関係

- ✅ T-010: SyncTideUseCase 実装（完了）
- ✅ T-011: 設定ファイルローダー（完了）
- ✅ T-008: GoogleCalendarClient（完了）
- ✅ T-007: TideDataRepository（完了）

---

## 成果物

### 1. `src/fishing_forecast_gcal/presentation/cli.py`

**責務**:
- コマンドライン引数のパースと検証
- 依存オブジェクトの構築（DI）
- UseCaseの呼び出しとエラーハンドリング
- ユーザーフレンドリーなログ出力

**実装方針**:

#### CLI仕様

```bash
# 基本的な使用方法
fishing-forecast-gcal sync-tide

# オプション指定
fishing-forecast-gcal sync-tide \
  --config config/config.yaml \
  --location-id "tokyo_bay" \
  --start-date 2026-02-08 \
  --end-date 2026-03-08 \
  --dry-run \
  --verbose
```

#### コマンドラインオプション

| オプション | 短縮形 | デフォルト値 | 説明 |
|-----------|--------|------------|------|
| `--config` | `-c` | `config/config.yaml` | 設定ファイルのパス |
| `--location-id` | `-l` | 全地点 | 対象地点ID（省略時は設定ファイルの全地点を処理） |
| `--start-date` | - | 今日 | 開始日（YYYY-MM-DD形式） |
| `--end-date` | - | 設定値に基づく | 終了日（YYYY-MM-DD形式、`--days` と排他） |
| `--days` | `-d` | 設定値に基づく | 同期日数（`--end-date` と排他、>= 1） |
| `--dry-run` | - | False | 実際には登録せず、処理内容のみ表示 |
| `--verbose` | `-v` | False | 詳細ログ出力 |

#### 処理フロー

```
1. 引数パース
   ↓
2. 設定ファイル読み込み
   ↓
3. ロギング設定
   ↓
4. 依存オブジェクト構築
   - GoogleCalendarClient
   - TideCalculationAdapter
   - TideDataRepository
   - CalendarRepository
   - SyncTideUseCase
   ↓
5. 対象地点のループ処理
   - 対象期間の日付ループ
   - SyncTideUseCase.execute()
   ↓
6. 結果サマリー表示
```

#### エラーハンドリング

- 設定ファイルが見つからない場合
- OAuth認証エラー
- ネットワークエラー
- バリデーションエラー
- 予期しない例外

すべて適切なエラーメッセージとともに終了コードを返す。

---

## テスト要件

### 単体テスト（`tests/unit/presentation/test_cli.py`）

1. **引数パーステスト**
   - すべてのオプション指定時のパース
   - デフォルト値の適用確認
   - 不正な引数の拒否（日付フォーマット、存在しないオプション）

2. **依存構築テスト**
   - Mock設定から依存オブジェクトが正しく構築されること
   - 設定ファイルが存在しない場合のエラー

3. **UseCaseスロー呼び出しテスト**
   - Mock UseCaseが正しい引数で呼び出されること
   - 対象地点が複数ある場合のループ処理
   - dry-runモードでUseCaseが呼び出されないこと

4. **エラーハンドリングテスト**
   - 設定ファイル読み込みエラー
   - UseCase実行時の例外
   - 終了コードの確認

### 統合テスト（手動確認、将来的にE2Eテストで自動化）

- 実際の設定ファイルを使用した動作確認
- Google Calendar APIとの統合動作確認
- ログ出力の妥当性確認

---

## 実装の詳細

### ログ出力

`logging` モジュールを使用し、以下のレベルでログを出力：

- **INFO**: 処理の進行状況（デフォルト）
- **DEBUG**: 詳細な処理内容（--verbose時）
- **WARNING**: 警告（例: 地点IDが見つからない）
- **ERROR**: エラー（例: API呼び出し失敗）

出力形式:
```
[2026-02-08 10:00:00] INFO: 設定ファイルを読み込みました: config/config.yaml
[2026-02-08 10:00:01] INFO: 地点: 東京湾（tokyo_bay）
[2026-02-08 10:00:02] INFO: 期間: 2026-02-08 ～ 2026-03-08
[2026-02-08 10:00:03] INFO: 2026-02-08のイベントを作成しました
...
[2026-02-08 10:01:00] INFO: 完了: 28日分のイベントを処理しました
```

### dry-runモード

`--dry-run` が指定された場合：
- カレンダーAPIへの書き込みを実行しない
- 処理内容のみをログ出力
- 「[DRY-RUN]」プレフィックスを付けてログ出力

---

## 変更予定ファイル

- ✏️ `src/fishing_forecast_gcal/presentation/cli.py` - 全面書き換え
- ✏️ `pyproject.toml` - エントリーポイント設定（確認のみ）
- ✅ `tests/unit/presentation/test_cli.py` - 新規作成

---

## 検証計画

### 検証項目

1. **基本動作**
   - [ ] デフォルト設定で実行できる
   - [ ] ヘルプメッセージが表示される（`--help`）
   - [ ] 設定ファイルが存在しない場合にエラーメッセージが表示される

2. **オプション動作**
   - [ ] `--config` で別の設定ファイルを指定できる
   - [ ] `--location-id` で特定の地点のみ処理できる
   - [ ] `--start-date`, `--end-date` で期間を指定できる
   - [ ] `--dry-run` でカレンダー書き込みをスキップできる
   - [ ] `--verbose` で詳細ログが出力される

3. **エラー処理**
   - [ ] 不正な日付フォーマットでエラーメッセージが表示される
   - [ ] 存在しない地点IDでエラーメッセージが表示される
   - [ ] OAuth認証エラー時に適切なメッセージが表示される

4. **品質**
   - [ ] `ruff format` でフォーマットが通る
   - [ ] `ruff check` でlintエラーがない
   - [ ] `pyright` で型チェックが通る
   - [ ] `pytest` で全テストがパスする

---

## Notes

- ✅ 既存のcli.pyはセットアップテスト用のプレースホルダーなので、全面的に書き換える
- サブコマンド方式（`sync-tide`）を採用し、フェーズ2で `sync-weather` を追加しやすくする
- エントリーポイントは `pyproject.toml` の `[project.scripts]` で定義済み（`fishing-forecast-gcal`）
- ロギング設定は標準ライブラリのみで実装（依存追加なし）

---

## 実装結果・変更点

### 実装完了日
2026-02-08

### 成果物

#### 1. `src/fishing_forecast_gcal/presentation/cli.py` ✅
- **概要**: argparseを使用したCLIエントリーポイントの実装
- **機能**:
  - サブコマンド `sync-tide` の実装
  - コマンドラインオプション（`--config`, `--location-id`, `--start-date`, `--end-date`, `--days`, `--dry-run`, `--verbose`）のサポート
  - `--days` と `--end-date` の排他チェック
  - `--days` の値バリデーション（>= 1）
  - 依存オブジェクトの構築（DI）
  - SyncTideUseCaseの呼び出しとエラーハンドリング
  - ユーザーフレンドリーなログ出力（標準loggingモジュール使用）
  - dry-runモード（カレンダー書き込みをスキップ）
  - 対象地点のループ処理
  - 結果サマリー表示
- **行数**: 256行（従来の76行から大幅拡張）

#### 2. `tests/unit/presentation/test_cli.py` ✅
- **概要**: CLI単体テスト（13件）
- **テスト内容**:
  - ロギング設定テスト（2件）
  - 引数パーステスト（8件）
  - 日付パーステスト（3件）
  - メイン処理の統合テスト（6件）
    - 基本フロー
    - 設定ファイル不在エラー
    - 地点ID不在エラー
    - dry-runモード
    - ユーザー中断
    - `--days` オプションによる期間算出
- **カバレッジ**: 91%（cli.py）

### テスト結果
- **単体テスト**: 19件すべてパス
- **全体テスト**: 204件パス、3件スキップ
- **カバレッジ**: 92%（全体）

### 品質チェック
- ✅ `ruff format .` - パス
- ✅ `ruff check .` - パス（不要なインポートを自動修正）
- ✅ `pyright` - パス（型エラー0件）
- ✅ `pytest` - 全テストパス

### 技術的な詳細

#### 依存オブジェクトの構築
- `GoogleCalendarClient`: OAuth2認証を実行
- `TideCalculationAdapter`: 調和定数ディレクトリ `config/harmonics` を指定
- `TideDataRepository`: アダプターをラップ
- `CalendarRepository`: クライアントとカレンダーIDを指定
- `SyncTideUseCase`: リポジトリを注入

#### エラーハンドリング
- 設定ファイル不在: 適切なエラーメッセージと終了コード1
- 地点ID不在: 利用可能な地点IDを表示して終了コード1
- 開始日 > 終了日: エラーメッセージと終了コード1
- `--days` と `--end-date` の同時指定: 排他エラーと終了コード2
- `--days` に 0 以下の値: バリデーションエラーと終了コード2
- ユーザー中断（Ctrl+C）: 終了コード130
- 予期しない例外: スタックトレースを表示して終了コード1

#### ログ出力
- INFOレベル: 処理の進行状況（デフォルト）
- DEBUGレベル: 詳細な処理内容（`--verbose` 時）
- フォーマット: `[YYYY-MM-DD HH:MM:SS] LEVEL: message`

### 変更点（計画からの差異）

#### 調和定数ディレクトリの指定
- **計画**: 設定ファイルから読み込む可能性を検討
- **実装**: デフォルト値 `config/harmonics` をハードコード
- **理由**: 設定ファイルに追加するとテンプレート更新が必要になり、ユーザーの初期設定が複雑になるため

#### 検証項目の達成状況
- ✅ 基本動作: すべて確認（単体テストで検証）
- ✅ オプション動作: すべて確認（単体テストで検証）
- ✅ エラー処理: すべて確認（単体テストで検証）
- ✅ 品質: すべてパス

### 次のステップ
- T-013: E2Eテストで実際のGoogle Calendar APIとの統合動作を確認
- フェーズ2でのサブコマンド `sync-weather` 追加の準備完了

### コミット履歴
1. `feat: implement CLI entry point for tide sync` (5d11d46)
   - CLI実装とテスト追加
2. `style: fix linting and type errors` (67a56c8)
   - 不要なインポート削除、型エラー修正
3. `fix(cli): add --days option to sync-tide command` (7c69fce)
   - `--days/-d` オプション追加（README quickstart との整合）
4. `fix(cli): add mutual exclusion and validation for --days option`
   - `--days` と `--end-date` の排他チェック追加
   - `--days` の値バリデーション（>= 1）追加
   - テスト6件追加（合計19件）

