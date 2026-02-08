# T-013: E2Eテスト

**Status**: ✅ Completed

---

## 概要

システム全体の統合テストを実装します。
実際のGoogle Calendar APIを使用し、潮汐イベントの作成・更新・冪等性を検証します。

---

## 依存関係

- ✅ T-001: ドメインモデル定義（完了）
- ✅ T-002: リポジトリインターフェース定義（完了）
- ✅ T-003: 潮汐計算サービス（完了）
- ✅ T-004: 潮回り判定サービス（完了）
- ✅ T-005: 時合い帯特定サービス（完了）
- ✅ T-006: 潮汐計算ライブラリアダプター（完了）
- ✅ T-007: TideDataRepository 実装（完了）
- ✅ T-008: Google Calendar API クライアント（完了）
- ✅ T-009: CalendarRepository 実装（完了）
- ✅ T-010: SyncTideUseCase 実装（完了）
- ✅ T-011: 設定ファイルローダー（完了）
- ✅ T-012: CLIエントリーポイント（完了）

---

## 成果物

### 1. `tests/e2e/test_sync_tide_flow.py`

**責務**:
- システム全体の統合フロー検証
- 実際のGoogle Calendar APIとの連携テスト
- 冗等性の確認
- エラーケースの検証

**実装方針**:

#### E2Eテストの範囲

E2Eテストでは、以下のシナリオをカバーします：

1. **基本フロー**: 潮汐イベントの作成
   - 複数日分のイベント作成
   - イベント内容の検証（タイトル、本文フォーマット）
   - 満潮・干潮情報の正確性
   - 潮回り判定の正確性
   - 時合い帯計算の正確性

2. **冗等性の検証**: 同一イベントIDで複数回実行
   - 2回目の実行でイベントが重複しないこと
   - update処理が正しく動作すること
   - イベントIDの一貫性

3. **[NOTES]セクションの保持**: ユーザー追記の保護
   - イベント作成後に[NOTES]を追加
   - 再実行時に[NOTES]が保持されること
   - [TIDE]セクションのみが更新されること

4. **エラーケース**: 異常系の動作確認
   - 調和定数ファイルが存在しない地点
   - ネットワークエラー時の挙動（モック）
   - 不正な設定ファイル

#### テスト環境の前提条件

E2Eテストを実行するには、以下の環境設定が必要です：

1. **Google Calendar 認証情報**
   - `config/credentials.json`: OAuth クライアントID
   - `config/token.json`: アクセストークン（初回認証で生成）
   - 環境変数 `E2E_CALENDAR_ID`: テスト専用カレンダーID

2. **調和定数データ**
   - `config/harmonics/yokosuka.pkl`: テスト用の調和定数

3. **設定ファイル**
   - テスト用の一時設定ファイルを動的生成

#### テスト実装構造

```python
class TestSyncTideE2E:
    """E2Eテスト: 潮汐同期の全体フロー"""

    @pytest.fixture(scope="module")
    def e2e_calendar_id(self) -> str:
        """テスト用カレンダーIDを取得"""
        calendar_id = os.environ.get("E2E_CALENDAR_ID")
        if not calendar_id:
            pytest.skip("E2E_CALENDAR_ID environment variable is required")
        return calendar_id

    @pytest.fixture(scope="module")
    def temp_config_file(self, e2e_calendar_id: str) -> Path:
        """テスト用設定ファイルを生成"""
        # 一時ファイルに設定を書き出す
        # calendar_id, credentials_path, token_path などを設定
        pass

    @pytest.fixture
    def cleanup_test_events(self, e2e_calendar_id: str) -> Iterator[None]:
        """テスト前後でイベントをクリーンアップ"""
        # テスト前: 既存のテストイベントを削除
        # yield
        # テスト後: 作成されたイベントを削除（オプション）
        pass

    def test_create_tide_events(self, temp_config_file: Path) -> None:
        """潮汐イベントの作成"""
        # Arrange: 設定、期間、地点を準備
        # Act: sync-tide コマンドまたはUseCaseを実行
        # Assert: イベントが作成されたことを確認
        pass

    def test_idempotency(self, temp_config_file: Path) -> None:
        """冗等性の検証"""
        # Arrange: 同一設定で2回実行
        # Act: 1回目と2回目でsync-tideを実行
        # Assert: イベント数が変わらない、内容が一致
        pass

    def test_preserve_notes_section(self, temp_config_file: Path) -> None:
        """[NOTES]セクションの保持"""
        # Arrange: イベント作成後、[NOTES]を手動追加
        # Act: 再度sync-tideを実行
        # Assert: [NOTES]が保持され、[TIDE]のみ更新
        pass

    def test_error_handling_missing_harmonics(self, temp_config_file: Path) -> None:
        """エラーハンドリング: 調和定数なし"""
        # Arrange: 存在しない地点IDを指定
        # Act: sync-tideを実行
        # Assert: エラーメッセージが出力され、中断しない
        pass
```

#### スキップ条件

以下の条件を満たさない場合、E2Eテストはスキップされます：

- `E2E_CALENDAR_ID` 環境変数が設定されていない
- `config/credentials.json` が存在しない
- `config/token.json` が存在しない（初回認証が必要）
- `config/harmonics/yokosuka.pkl` が存在しない

これにより、CI環境や認証情報がない環境でもテストスイートが失敗しないようにします。

---

## テスト要件

### E2Eテスト（`tests/e2e/test_sync_tide_flow.py`）

#### 必須テストケース

| テストケース | 目的 | 検証観点 |
|-------------|------|---------|
| `test_create_tide_events` | 基本的なイベント作成 | イベントが正しく作成されること |
| `test_idempotency` | 冗等性 | 2回実行しても重複しないこと |
| `test_preserve_notes_section` | ノート保持 | [NOTES]が保持されること |
| `test_error_handling_missing_harmonics` | エラーハンドリング | 調和定数がない場合の処理 |

#### 検証項目の詳細

**基本的なイベント作成**:
- イベントタイトル: `潮汐 {location_name} ({tide_type})`
- イベント本文に[TIDE]セクションが含まれる
- 満潮・干潮情報が正確
- 潮回りが正しい（大潮・中潮・小潮）
- 時合い帯が満潮±2時間

**冗等性**:
- 同一event_idで2回実行
- イベント数が変わらない
- イベント内容が一致（[NOTES]以外）

**[NOTES]保持**:
- 初回作成後、[NOTES]セクションに手動でテキストを追加
- 2回目の実行後、[NOTES]が保持されている
- [TIDE]セクションは更新されている

**エラーハンドリング**:
- 調和定数ファイルが存在しない地点を指定
- FileNotFoundError が適切に処理される
- ログにエラーメッセージが出力される
- 他の地点の処理は継続される

---

## 実装チェックリスト

### 実装前

- [x] テスト環境の準備
  - [x] テスト用カレンダーの作成
  - [x] `E2E_CALENDAR_ID` 環境変数の設定
  - [x] `config/credentials.json` の配置
  - [x] OAuth認証の実行（`config/token.json` 生成）
  - [x] `config/harmonics/tk.pkl` の配置

### 実装中

- [x] `tests/e2e/test_sync_tide_flow.py` の作成
  - [x] フィクスチャの実装
    - [x] `e2e_calendar_id`: カレンダーID取得
    - [x] `temp_config_file`: 一時設定ファイル生成
    - [x] `cleanup_events`: イベントクリーンアップ（autouse）
  - [x] テストケースの実装
    - [x] `test_create_tide_events`: 基本フロー
    - [x] `test_create_multiple_days`: 複数日分のイベント作成
    - [x] `test_idempotency`: 冪等性
    - [x] `test_preserve_notes_section`: [NOTES]保持
    - [x] `test_error_handling_missing_harmonics`: エラーハンドリング

### 実装後

- [x] 品質チェック
  - [x] `uv run ruff format .`
  - [x] `uv run ruff check .`
  - [x] `uv run pyright`
  - [x] `uv run pytest tests/e2e/ -m e2e` (E2Eテスト: 5/5 passed)
  - [x] `uv run pytest` (全テスト: 204 passed, 3 skipped, 5 deselected)

---

## 相談事項

### 1. テスト実行環境の整備

E2Eテストは実際のGoogle Calendar APIを使用するため、以下の準備が必要です：

- テスト専用のGoogle Calendarを作成し、カレンダーIDを取得する
- OAuth認証情報（`credentials.json`）を配置する
- 初回認証を実行して `token.json` を生成する
- 環境変数 `E2E_CALENDAR_ID` を設定する

これらの手順はドキュメント化する必要があります。

### 2. CI/CD環境での実行

E2Eテストは認証情報が必要なため、CI環境では以下の対応が必要です：

- GitHub Secretsに認証情報を保存
- E2Eテストを別のワークフローに分離（手動トリガー）
- または、E2Eテストをスキップするフラグを追加

この方針はユーザーと相談して決定します。

### 3. テスト後のクリーンアップ

テスト実行後、作成されたイベントを削除するかどうか：

- **削除する**: テスト環境をクリーンに保つ
- **削除しない**: 手動で結果を確認できる

どちらを採用するか、またはオプションで切り替え可能にするか検討が必要です。

---

## 参照

- [implementation_plan.md](../implementation_plan.md) - T-013セクション
- [issue-23.md](../completed/issue-23.md) - CLI実装（依存タスク）
- [issue-21.md](../completed/issue-21.md) - SyncTideUseCase実装（依存タスク）

---

## 進捗ログ

- 2026-02-08: ドキュメント作成、実装方針確定
- 2026-02-08: JMA スクリプト修正（URL パス変更 `/gmd/kaiyou/` → `/kaiyou/`、固定幅テキストパースバグ修正）
- 2026-02-08: 調和定数データ生成（`config/harmonics/tk.pkl`: 8758 データポイント、59 分潮）
- 2026-02-08: E2E テスト実装（5 テストケース）、品質チェック全通過
- 2026-02-08: E2E テスト実行完了（5/5 passed, 28.93s）

---

## 実装結果

### 成果物

| ファイル | 概要 |
|---------|------|
| `tests/e2e/conftest.py` | 共有フィクスチャ（認証、設定、クリーンアップ） |
| `tests/e2e/test_sync_tide_flow.py` | E2E テスト 5 ケース |
| `scripts/fetch_jma_tide_data.py` | JMA URL パスおよびパースバグの修正 |
| `pyproject.toml` | `e2e` マーカー追加、デフォルト除外設定 |

### テスト結果

| テストケース | 結果 | 検証観点 |
|-------------|------|---------|
| `test_create_tide_events` | ✅ Pass | タイトルフォーマット、[TIDE] セクション、潮汐情報 |
| `test_create_multiple_days` | ✅ Pass | 複数日分のイベント作成（3 日分） |
| `test_idempotency` | ✅ Pass | 2 回実行で event_id/title/date/[TIDE] 一致 |
| `test_preserve_notes_section` | ✅ Pass | [NOTES] セクションの保持 |
| `test_error_handling_missing_harmonics` | ✅ Pass | 存在しない地点で RuntimeError |

### 設計上の決定

- テスト対象地点を東京（`tk`）に変更（当初は横須賀を想定）
- テスト日付を 2026-06-15～17 に設定（未来の日付で既存データと衝突しない）
- `cleanup_events` を autouse fixture として各テスト前にイベントを削除
- API レートリミット対策として `API_DELAY_SEC = 0.5` を設定
- デフォルトの `pytest` 実行から E2E テストを除外（`-m 'not e2e'`）
