# Implementation Plan

## タスク表
- タスク一覧は別ファイルに集約: [task_table.md](task_table.md)
- 本書のタスク定義と同期させること（タスク分割・依存・テスト要件の更新時は両方を更新）

## 方針
- まずは天文潮のみで動く MVP を作る
- 予報更新は後続フェーズで拡張
- すべて自動化可能なパイプラインを意識して設計
- **レイヤードアーキテクチャ** を最初から導入し、責務を明確に分離

## フェーズ 0: 仕様確定（短期）
- 対象地点、期間、出力フォーマットの合意
- Google カレンダーのイベント設計（MVP 仕様を確定、詳細は下記参照）
- 天文潮の取得方式の決定
- タイドグラフ画像の表現方針は後続フェーズで検討
- 開発環境（uv 前提）の手順をドキュメント化
- 配布/セットアップ手順の草案化（uv 前提、Docker は後続）
- 更新ウィンドウ（Sync-Tide/Sync-Weather）の範囲を決定
- **レイヤードアーキテクチャの詳細設計**

## 決定事項（2026-02-07）
- 天文潮は計算ライブラリ優先（API は比較・代替手段）
- MVP は画像なし
- 設定ファイルはテンプレート運用（実体は Git 管理しない）
- **レイヤードアーキテクチャを採用**（責務分離、テスト容易性、保守性向上）
- **更新間隔を 3 時間ごとに短縮**（気象庁の更新頻度に合わせる）
- MVP では遠征カレンダー（trips）の運用を扱わない

## イベント設計（MVP）
- 種別: 終日イベント（`settings.timezone` の日付基準）
- タイトル: `潮汐 {location_name} ({tide_type})`
- 本文構造: 予報更新の差分反映を前提に、セクションを明示的に区切る

本文フォーマット（例）:
```
[TIDE]
- 満潮: 06:12 (162cm)
- 干潮: 12:34 (58cm)
- 時合い: 04:12-08:12

[FORECAST]
- 風速: 5m/s
- 風向: 北
- 気圧: 1012hPa

[NOTES]
- 手動メモ（ここは自動更新で保持）
```

- 更新方針:
  - Sync-Tide はタイトルと `[TIDE]` を更新（予報・メモは保持）
  - Sync-Weather は `[FORECAST]` のみ更新（他セクションは保持）
- ユーザー編集は `[NOTES]` のみを対象とし、セクション名は変更しない
- 破損対策: セクションが欠落している場合は自動更新をスキップし、ログで警告する（メモ保護を優先）
- イベント ID 生成: `location_id + date` を素材に MD5 ハッシュで生成（`CalendarEvent.generate_event_id()` ドメインモデルの静的メソッド）

## セットアップフロー（案）
1. GCP プロジェクト作成
2. Google Calendar API を有効化
3. OAuth 同意画面を Testing で設定（テストユーザー登録）
4. Desktop App の OAuth クライアント ID を作成し `credentials.json` を配置
5. `uv sync` で依存関係をセットアップ
6. `config/config.yaml` を作成し `google_credentials_path` を設定
7. 初回認証で `config/token.json` を生成（CLI コマンドは確定後に記載）
8. スケジューラー起動（CLI コマンドは確定後に記載）

注記:
- OAuth の同意画面が Testing の場合、リフレッシュトークン期限に注意

---

## フェーズ 1: MVP（天文潮ベース）

### タスク分割方針
レイヤードアーキテクチャに従い、各層を独立して開発・テスト可能な粒度に分割します。

---

### 1.1 Domain Layer（基礎）

#### T-001: ドメインモデル定義 ✅
**責務**: ビジネスロジックの中心となるデータ構造を定義

**ステータス**: ✅ 完了（再調査）

**成果物**:
- `domain/models/tide.py`
  - `Tide`, `TideEvent`, `TideType` クラス
- `domain/models/fishing_condition.py`
  - `FishingCondition` クラス（注意レベルを含む）
- `domain/models/calendar_event.py`
  - `CalendarEvent` クラス
- `domain/models/location.py`
  - `Location` クラス（不変IDを含む）

**テスト要件**:
- 各モデルのインスタンス化テスト ✅
- バリデーションテスト（不正値の拒否） ✅
- **実績**: 56テスト、カバレッジ100%

**依存**: なし

---

#### T-002: リポジトリインターフェース定義 ✅
**責務**: 外部データソースへのアクセスを抽象化

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `domain/repositories/tide_data_repository.py`
  - `ITideDataRepository` インターフェース
- `domain/repositories/weather_repository.py`
  - `IWeatherRepository` インターフェース
- `domain/repositories/calendar_repository.py`
  - `ICalendarRepository` インターフェース

**テスト要件**:
- インターフェースのシグネチャ検証（型チェック） ✅
- **実績**: 11テスト、カバレッジ100%

**依存**: T-001

---

#### T-003: 潮汐計算サービス ✅
**責務**: 満潮・干潮の抽出ロジック

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `domain/services/tide_calculation_service.py`
  - `TideCalculationService` クラス
  - `extract_high_low_tides()` メソッド

**テスト要件**:
- 模擬潮汐データから満干潮を正しく抽出 ✅
- エッジケース（フラットな潮汐、極端な値） ✅
- **実績**: 8テスト、カバレッジ100%

**依存**: T-001

---

#### T-004: 潮回り判定サービス ✅
**責務**: 大潮・中潮・小潮の判定ロジック

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `domain/services/tide_type_classifier.py`
  - `TideTypeClassifier` クラス
  - `classify()` メソッド（潮位差と月齢から判定）
  - 月齢による基本判定 + 潮位差による補正

**テスト要件**:
- 潮位差と月齢から正しく判定 ✅
- 境界値テスト ✅
- **実績**: 23テスト、カバレッジ100%

**依存**: T-001

---

#### T-005: 時合い帯特定サービス ✅
**責務**: 満潮前後の時合い帯を計算

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `domain/services/prime_time_finder.py`
  - `PrimeTimeFinder` クラス
  - `find()` メソッド（満潮時刻から±2時間を計算）

**テスト要件**:
- 満潮時刻から正しく±2時間を計算 ✅
- 日付を跨ぐ場合のテスト ✅
- **実績**: 7テスト、カバレッジ100%

**依存**: T-001

---

### 1.2 Infrastructure Layer（外部連携）

#### T-006: 潮汐計算ライブラリアダプター ✅
**責務**: UTideライブラリをラップして潮汐予測を実行

**ステータス**: ✅ 完了（Issue #17）

**成果物**:
- `infrastructure/adapters/tide_calculation_adapter.py`
  - UTideライブラリの呼び出しロジック
  - 調和定数データの読み込み（pickle形式）
  - 潮汐予測の実行と結果の変換
- `scripts/fetch_jma_tide_data.py`
  - 気象庁の観測潮位データ取得・パーススクリプト
  - UTide調和解析→pickle保存の自動化

**テスト要件**:
- ライブラリが正しく呼び出されること
- 公式潮見表との差分検証（許容差以内、目標: ±10cm以内）
- 調和定数が正しく読み込まれること

**技術補足**:
- UTideは調和解析による潮汐予測を実行
- 地点ごとの調和定数データ（振幅・位相）が必要
- 17 JMA 主要観測地点に対応（`scripts/fetch_jma_tide_data.py` で調和定数を生成）
- 調和定数は pickle 形式で保存（UTide coef の内部状態を完全保持するため）

**依存**: T-002

---

#### T-007: TideDataRepository 実装 ✅
**責務**: 潮汐データの取得ロジックを実装

**成果物**:
- `infrastructure/repositories/tide_data_repository.py`
  - `ITideDataRepository` の実装
  - アダプターを使用してDomainモデルに変換

**テスト要件**:
- Mockアダプターで単体テスト
- 実ライブラリで統合テスト

**依存**: T-001, T-002, T-006

**実装完了**: 2026-02-08
- Issue #18 にて実装
- 単体テスト 9件、統合テスト 4件
- ドキュメント: [docs/completed/issue-18.md](./completed/issue-18.md)

---

#### T-008: Google Calendar API クライアント ✅
**責務**: Google Calendar API のラッパー

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `infrastructure/clients/google_calendar_client.py`
  - OAuth2認証
  - `settings.google_credentials_path` と `settings.google_token_path` を使用
  - イベント作成・get・更新API呼び出し

**テスト要件**:
- Mock APIレスポンスで単体テスト ✅
- テストカレンダーで統合テスト（T-009で実施予定）

**実績**:
- 3つのCRUDメソッド実装（create/get/update）
- 単体テスト9件すべてパス
- カバレッジ57%（実装メソッドは100%）
- Pylance警告解消済み
- 詳細: [docs/completed/issue-19.md](completed/issue-19.md)

**依存**: なし

---

#### T-009: CalendarRepository 実装 ✅
**責務**: カレンダーイベントの作成・取得・更新

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `infrastructure/repositories/calendar_repository.py`
  - `ICalendarRepository` の実装
  - DomainモデルとGoogle API形式の変換
  - upsertロジック
  - `extendedProperties` を使用した location_id の保存・取得

**テスト要件**:
- Mockクライアントで単体テスト ✅
- 冗等性テスト（同一IDで複数回実行） ✅

**実績**:
- 12件の単体テストすべてパス（リファクタリングでID生成テスト4件をドメイン層に移動）
- カバレッジ100%（CalendarRepository）
- extendedProperties サポートを GoogleCalendarClient に追加
- 詳細: [docs/completed/issue-20.md](completed/issue-20.md)

**注記**:
- イベントID生成は T-010 リファクタリングで `CalendarEvent.generate_event_id()` に移動済み

**依存**: T-001, T-002, T-008

**実装完了**: 2026-02-08
- Issue #20 にて実装
- 単体テスト 16件、カバレッジ100%
- ドキュメント: [docs/completed/issue-20.md](./completed/issue-20.md)

---

### 1.3 Application Layer（ユースケース）

#### T-010: SyncTideUseCase 実装 ✅
**責務**: 天文潮の同期処理をオーケストレーション

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `application/usecases/sync_tide_usecase.py`
  - 潮汐データ取得
  - 満干潮抽出
  - 潮回り判定
  - 時合い帯計算
  - カレンダーイベント作成/更新
  - [NOTES]セクション保持機能

**テスト要件**:
- Mockリポジトリで単体テスト ✅
- エンドツーエンドテスト（実リポジトリ使用）

**実績**:
- 7件の単体テストすべてパス
- カバレッジ100%（SyncTideUseCase）
- イベントID生成を `CalendarEvent.generate_event_id()` ドメインモデルに配置
- `_format_tide_section` / `_build_description` を `@staticmethod` 化
- 詳細: [docs/completed/issue-21.md](completed/issue-21.md)

**依存**: T-001, T-002, T-003, T-004, T-005, T-007, T-009

**実装完了**: 2026-02-08
- Issue #21 にて実装
- 単体テスト 7件、カバレッジ100%
- リファクタリング: event_id 生成をインフラ層からドメイン層に移動
- ドキュメント: [docs/completed/issue-21.md](./completed/issue-21.md)

---

### 1.4 Presentation Layer（CLI・設定）

#### T-011: 設定ファイルローダー ✅
**責務**: `config.yaml` の読み込みと検証

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `presentation/config_loader.py`
  - YAMLパース
  - スキーマ検証（必須キー、型チェック、範囲チェック）
  - Locationモデルへのマッピング
  - Locationの不変ID（`locations[].id`）の読み込み
  - OAuth 認証パス（`google_credentials_path`, `google_token_path`）の読み込み
  - 型安全なデータクラス（`AppSettings`, `FishingConditionSettings`, `AppConfig`）

**テスト要件**:
- 正常なYAMLのパース ✅
- 不正なYAMLのエラー検知 ✅

**実績**:
- 21件の単体テストすべてパス
- カバレッジ93%（config_loader.py）
- 正常系・異常系・エッジケースを網羅
- Pyright型チェックパス（型エラー0件）
- 詳細: [docs/completed/issue-22.md](completed/issue-22.md)

**依存**: T-001

**実装完了**: 2026-02-08
- Issue #22 にて実装
- 単体テスト 21件、カバレッジ93%
- ドキュメント: [docs/completed/issue-22.md](./completed/issue-22.md)

**依存**: T-001

---

#### T-012: CLIエントリーポイント ✅
**責務**: コマンドラインインターフェース

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `presentation/cli.py`
  - 引数パース（argparse）
  - サブコマンド `sync-tide` の実装
  - コマンドラインオプション（`--config`, `--location-id`, `--start-date`, `--end-date`, `--days`, `--dry-run`, `--verbose`）
  - `--days` と `--end-date` の排他チェック、`--days` の値バリデーション（>= 1）
  - 期間決定の優先度: `--end-date` > `--days` > `config.tide_register_months`
  - 依存オブジェクトの構築（DI）
  - SyncTideUseCaseの呼び出しとエラーハンドリング
  - ユーザーフレンドリーなログ出力

**テスト要件**:
- CLI引数のパーステスト ✅
- Mock UseCaseで呼び出し確認 ✅
  
**実績**:
- 単体テスト19件すべてパス
- カバレッジ91%（cli.py）
- サブコマンド方式でフェーズ2での拡張に対応
- dry-runモードサポート
- 詳細: [docs/completed/issue-23.md](./completed/issue-23.md)

**依存**: T-010, T-011

**実装完了**: 2026-02-08
- Issue #23 にて実装
- 単体テスト 13件、全体カバレッジ92%
- ドキュメント: [docs/completed/issue-23.md](./completed/issue-23.md)

---

### 1.5 統合テスト

#### T-013: E2Eテスト ✅
**責務**: システム全体の統合テスト

**ステータス**: ✅ 完了

**成果物**:
- `tests/e2e/conftest.py`
  - 共有フィクスチャ（認証、設定ファイル生成、クリーンアップ）
- `tests/e2e/test_sync_tide_flow.py`
  - テストカレンダーへの実際の登録（5テストケース）
  - 冪等性確認（複数回実行）
  - [NOTES]セクション保持の検証
  - エラーハンドリングの検証

**実装詳細**:
- テスト地点: 東京（`tk`）
- テスト日付: 2026-06-15～17
- 環境変数 `E2E_CALENDAR_ID` でテスト用カレンダーを指定
- デフォルトの pytest 実行から除外（`-m 'not e2e'`）

**依存**: 全タスク

---

#### T-013.1: station_id マッピングの導入 ✅
**責務**: 釣行地点IDと観測地点コードを分離し、調和定数の参照を安定化

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `domain/models/location.py`
  - `station_id` 追加とバリデーション
- `presentation/config_loader.py`
  - `locations[].station_id` を必須化
- `infrastructure/adapters/tide_calculation_adapter.py`
  - 調和定数参照を `station_id` に統一
  - 調和定数ファイル名の小文字正規化
- `config/config.yaml.template`
  - `station_id` サンプル追加
- テスト更新（unit/integration/e2e）
- ドキュメント更新
  - `docs/潮位データ：推算値と実測値の違い.md`

**テスト要件**:
- `Location` バリデーションの更新
- `station_id` を含むテストデータ整合性の確認
- 調和定数参照キーの一致

**依存**: T-001, T-006, T-011, T-013

**実装完了**: 2026-02-08
- ドキュメント: [docs/completed/t-0131-station-id-mapping.md](./completed/t-0131-station-id-mapping.md)

---

## フェーズ 1 の成果物
- 1か月分の潮汐イベントを生成・登録できる（画像なし）
- レイヤードアーキテクチャで実装され、各層が独立してテスト可能
- 複数回実行しても重複登録が起きない（冗等性）

---

## フェーズ 1.6: MVP安定化（ポストMVP・第1弾）

**方針**:
- MVP直後に判明した精度・表示・運用上の課題を優先的に解消
- 追加の安定化が見つかった場合はフェーズ 1.7 に切り出す

### タスク分割

#### T-013.2: 分単位の潮汐時刻精度改善 ✅
**責務**: 分が 00 固定になる問題を解消し、分単位の潮汐時刻を算出

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `infrastructure/adapters/tide_calculation_adapter.py`
  - 予測時刻の粒度を分単位に調整
- `domain/services/tide_calculation_service.py`
  - 分単位の極値抽出が正しく動作することを確認
- テスト（unit/integration）
  - 公式潮見表との差分検証（許容差を明記）

**テスト要件**:
- 分単位の時刻が出力されること
- 公式潮見表との差分が許容範囲に収まること

**依存**: T-003, T-006

---

#### T-013.3: 満干潮の欠落調査と修正 ✅
**責務**: 1 日に満潮/干潮が 1 回しか抽出されない問題の原因調査と修正

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `domain/services/tide_calculation_service.py`
  - 極値抽出ロジックの改善
- 再現テスト
  - 欠落が発生した日付の再現テスト

**テスト要件**:
- 対象地点の 30 日分で満干潮が 2 回ずつ抽出されること
- 例外条件がある場合は明文化されること

**依存**: T-003, T-006

**実装完了**: 2026-02-08
- ドキュメント: [docs/completed/issue-54.md](./completed/issue-54.md)

---

#### T-013.4: 潮位基準面の説明と補正方針 ✅
**責務**: 潮位の 0cm 基準面を明確化し、必要なら補正方針を設計

**成果物**:
- ドキュメント更新（基準面の説明）
- 需要に応じた補正手段の設計（地点別オフセットなど）

**テスト要件**:
- 公式潮見表との差異が説明できること

**依存**: T-006

**実装状況**:
- ステータス: ✅ 完了（Phase 1: ドキュメント化）
- Issue: #55
- ドキュメント: [docs/completed/issue-55.md](./completed/issue-55.md)
- PR: [PR番号は作成後に追記]
- 完了日: 2026-02-08

**主な成果**:
- UTideの基準面（MSL: 平均潮位）を文書化
- 本ツールが「観測基準面からの高さ」を出力することを明記
- 気象庁推算値（DL基準）との約88cm差の原因を説明
- 3ファイルにドキュメント追加: `data_sources.md`, `tide_calculation_adapter.py`, `潮位データ：推算値と実測値の違い.md`
- Phase 2（補正機能）は需要に応じて将来実装

---

#### T-013.5: 潮回り期間中央日のマーカー ✅
**責務**: 大潮/小潮などの期間中央日を本文で視認できるようにする

**ステータス**: ✅ 完了（2026-02-10）

**成果物**:
- `domain/services/tide_period_analyzer.py`（新規）
  - `TidePeriodAnalyzer.is_midpoint_day()`: 対象日が期間中央日か判定
  - `_find_continuous_period()`: 双方向検索で連続TideTypeの期間を特定
  - `_calculate_midpoint()`: 偶数日の場合は前半側を中央日とする
- `application/usecases/sync_tide_usecase.py`（修正）
  - `execute()`: ±3日分（計7日）のデータを取得して前後文脈を確保
  - `_get_date_range()`: 日付リスト生成ヘルパー追加
  - `_format_tide_section()`: 大潮の中央日に "⭐ 中央日" マーカーを追加
- 大潮のみにマーカー表示（ユーザー決定）

**テスト要件**:
- 連続期間の中央日にのみ印が付くこと ✅
- 偶数日数時の扱いが明確化されること ✅
- 月・年境界をまたぐ期間でも正しく判定できること ✅
- 大潮以外の中央日にはマーカーが付かないこと ✅

**実績**:
- TidePeriodAnalyzer: 12テスト合格、100%カバレッジ
- SyncTideUseCase: 10テスト合格、99%カバレッジ
- 全232テスト合格、コード品質チェック合格（ruff/pyright）
- Phase 1 commit: 55b7854（TidePeriodAnalyzer実装）
- Phase 2 commit: 915b7d1（UseCase統合）
- 詳細: [docs/completed/issue-57.md](completed/issue-57.md)

**依存**: T-010

---

#### T-013.6: イベントタイトルの潮回り絵文字化 ✅
**責務**: タイトル先頭に潮回り絵文字を付けて視認性を改善

**ステータス**: ✅ 完了（2026-02-08）

**成果物**:
- `domain/models/tide.py`
  - `TideType.to_emoji()` メソッド追加（🔴大潮 🟠中潮 🔵小潮 ⚪長潮 🟢若潮）
- `application/usecases/sync_tide_usecase.py`
  - タイトル形式: `{emoji}{location.name} ({tide_type.value})`（例: `🔴東京湾 (大潮)`）
  - 説明文に絵文字凡例を追加
- テスト: 単体テスト 2 件追加、全 6 ファイルのテストデータ更新

**テスト要件**:
- タイトルが新形式になること ✅
- イベントカラーは変更しないこと ✅
- 全 223 テストパス（カバレッジ 92%）

**実績**:
- TideType に `to_emoji()` メソッドを実装
- SyncTideUseCase で絵文字付きタイトル生成とイベント説明に絵文字凡例を追加
- 単体テスト 2 件・統合テスト・E2E テストすべて更新
- ruff/pyright チェックすべてパス
- 詳細: [docs/completed/issue-56.md](completed/issue-56.md)

**依存**: T-010

---

## フェーズ 1.7: MVP安定化（ポストMVP・第2弾）

**方針**:
- MVP運用で追加発見された安定化/運用課題を追加投入

### タスク分割

#### T-013.7: 釣り情報の初期化コマンド ✅
**ステータス**: ✅ 完了
**責務**: 登録済みの潮汐イベントを安全に初期化できる CLI を提供

**成果物**:
- `presentation/cli.py`
  - `reset-tide` もしくは `clear-events` サブコマンドの追加
- 期間/地点指定、`--dry-run`、`--force` のサポート
- 実行ログの詳細化

**テスト要件**:
- 対象条件に合致するイベントのみ削除されること
- `--dry-run` で削除対象が確認できること

**依存**: T-009, T-010

---

## フェーズ 1.8: MVP安定化（ポストMVP・第3弾）

**方針**:
- テスト基盤・コード品質に関する技術的負債を解消

### タスク分割

#### T-013.8: JMA推算テキストパーサーの分離 ✅
**責務**: 臨時スクリプト (`scripts/fetch_jma_suisan_tide_data.py`) のパースロジックをテスト支援モジュールに分離し、テストコードのパッケージ外依存を解消

**ステータス**: ✅ 完了（2026-02-11）

**背景**:
- `scripts/fetch_jma_suisan_tide_data.py` は気象庁推算テキストのダウンロード用臨時スクリプト
- 統合テスト (`test_tide_prediction_against_jma_suisan.py`) が `parse_jma_suisan_text` を `from scripts.fetch_jma_suisan_tide_data import ...` で直接インポートしている
- 臨時スクリプトがテストインフラの構成要素になっており、スクリプトの変更・削除でテストが壊れるリスクがある

**成果物**:
- `tests/support/jma_suisan_parser.py`（新規）
  - `JMASuisanDaily` データクラスと `parse_jma_suisan_text` 関数を移動
- `scripts/fetch_jma_suisan_tide_data.py`（修正）
  - パースロジックを `tests/support/` からインポートするか、CLI ダウンローダーに縮退
- `tests/integration/infrastructure/test_tide_prediction_against_jma_suisan.py`（修正）
  - インポートパスを `tests/support/jma_suisan_parser` に変更

**テスト要件**:
- 既存の統合テスト（JMA推算値との差分検証）がすべてパスすること ✅
- `scripts/` からのインポートが解消されていること ✅
- ruff / pyright チェックがパスすること ✅

**実装結果** (2026-02-11):
- 新規作成: `tests/support/jma_suisan_parser.py` (152行)
- 新規作成: `tests/unit/support/test_jma_suisan_parser.py` (200行、11テストケース)
- 修正: `scripts/fetch_jma_suisan_tide_data.py` (パースロジック削除、-125行)
- 修正: `tests/integration/infrastructure/test_tide_prediction_against_jma_suisan.py` (インポートパス更新)
- テスト結果: 281 passed, 1 skipped
- 品質チェック: ruff ✅ / pyright ✅ (型エラー0件)
- ドキュメント: [docs/completed/issue-69.md](completed/issue-69.md)

**依存**: T-006, T-013

#### T-013.9: JMA潮汐データ取得ロジックの正式モジュール化と全70地点拡張 ✅
**責務**: `scripts/fetch_jma_tide_data.py` のコアロジック（地点データ・パーサー・調和解析）を `src/` 配下の正式モジュールに移動し、地点カバレッジを全 70 地点に拡張する

**ステータス**: ✅ 完了

**背景**:
- 現行 `STATIONS` 辞書は 17 地点のみ（カバー率 24%）。気象庁公式一覧は 70 地点
- 地点コードの誤マッピングが 2 件存在: `FK`(福岡→正しくは深浦), `HA`(博多→正しくは浜田)
- `ref_level_tp_cm` の値も複数地点で公式データと不一致
- 参照: https://www.data.jma.go.jp/kaiyou/db/tide/genbo/station.php

**成果物**:
- `src/` 配下に `JMAStation` データクラスと全 70 地点定義を配置
- `parse_jma_hourly_text` および `run_harmonic_analysis` を `src/` 配下に移動
- `scripts/fetch_jma_tide_data.py` をエントリーポイントのみに縮退
- 全 70 地点の調和定数（pickle）生成が可能な状態

**テスト要件**:
- パーサー・調和解析の単体テストを追加
- 既存の統合テストがパスすること
- 地点コードの誤マッピング（FK, HA）が修正されていること
- ruff / pyright チェックがパスること

**依存**: T-013.8
- ドキュメント: [docs/completed/issue-70.md](completed/issue-70.md)

#### T-013.10: upsert_event の重複 get_event API 呼び出し削除 ✅
**責務**: `SyncTideUseCase.execute()` と `CalendarRepository.upsert_event()` 間の重複 API 呼び出しを削除

**ステータス**: ✅ 完了（2026-02-11）

**背景**:
- `SyncTideUseCase.execute()` 内で `calendar_repo.get_event(event_id)` → NOTES 抽出後、`calendar_repo.upsert_event(event)` を呼ぶと `upsert_event` 内部で再度 `get_event(event_id)` が呼ばれる
- 同一イベントID に対して Google Calendar API の GET が2回発生していた

**成果物**:
- `domain/repositories/calendar_repository.py`
  - `ICalendarRepository.upsert_event()` に `existing: CalendarEvent | None = None` keyword-only 引数追加
- `infrastructure/repositories/calendar_repository.py`
  - `CalendarRepository.upsert_event()` で `existing` 渡し時に内部 `get_event` スキップ
- `application/usecases/sync_tide_usecase.py`
  - `upsert_event(event, existing=existing_event)` として呼び出し

**テスト要件**:
- `existing` ありの場合に `get_event` がスキップされること ✅
- `existing` なしの場合に従来通り `get_event` が呼ばれること ✅（後方互換性）
- UseCase テストで `existing` パラメータが渡されることを検証 ✅
- テスト結果: 320 passed, ruff / pyright パス
- ドキュメント: [docs/completed/issue-46.md](completed/issue-46.md)

**依存**: T-009, T-010

---

## フェーズ 1.9: MVP安定化（ポストMVP・第4弾）

**方針**:
- 既存のブロック課題に干渉しない範囲で、タイドグラフ画像の表示方式を検証
- カレンダーイベントの説明文/添付の両方を試し、実運用に適した方式を選定

### タスク分割

#### T-013.11: タイドグラフ画像の表示方式POC ✅
**責務**: カレンダーイベントでのタイドグラフ画像表示方式を比較検証し、実装方針を確定する

**ステータス**: ✅ 完了

**方式決定**: 方式 B（Google Drive + Calendar attachments）を採用
- Google アカウントのみで完結（外部サービス不要）
- `drive.file` スコープ（最小権限）+ `calendar` スコープ（既存）
- Calendar API の `attachments` フィールドでイベントに添付

**POC 成果**:
- 方式 A（Imgur）/ 方式 B（Google Drive）の比較検証 → 方式 B 採用
- API 仕様調査: Calendar attachments, Drive files.create, permissions.create
- POC スクリプトによるタイドグラフ画像生成検証（matplotlib + seaborn）
- 画像仕様確定: スクエア 6×6, ダークモード, 満干潮アノテーション
- 日本語フォント対応: matplotlib-fontja（IPAexゴシック同梱）
- 実装計画策定: ST-1〜ST-5 のサブタスク分割

**後続 Issue（実装フェーズ）**:

| サブタスク | 概要 | Issue | ステータス |
|-----------|------|-------|-----------|
| ST-1 + ST-2 | Google Drive/Calendar API 添付機能 ([doc](completed/issue-78.md)) | [#78](https://github.com/nakagawah13/fishing-forecast-gcal/issues/78) | ✅ Completed |
| ST-3 | タイドグラフ画像生成サービス ([doc](completed/issue-79.md)) | [#79](https://github.com/nakagawah13/fishing-forecast-gcal/issues/79) | ✅ Completed |
| ST-4 | SyncTideUseCase への統合 ([doc](completed/issue-80.md)) | [#80](https://github.com/nakagawah13/fishing-forecast-gcal/issues/80) | ✅ Completed |
| ST-5 | 古い画像の定期削除 ([doc](completed/issue-81.md)) | [#81](https://github.com/nakagawah13/fishing-forecast-gcal/issues/81) | ✅ Completed |

**依存**: T-009, T-010
**詳細ドキュメント**: [docs/completed/issue-76.md](completed/issue-76.md)

## フェーズ 1.10: MVP安定化（ポストMVP・第5弾）

**方針**:
- CLI モジュールの責務分離によるコードの保守性向上
- Phase 2 の `sync-weather` コマンド追加に備えた拡張性の確保

### タスク分割

#### T-013.12: CLI モジュール分割（cli.py の責務分離） ✅
**責務**: `cli.py`（600行）をコマンドごとにファイル分割し、薄いディスパッチャーに変更する

**ステータス**: ✅ 完了

**変更内容**:
- `cli.py` を薄いディスパッチャー（約200行）に変更
- `commands/common.py`: 共通ユーティリティ（`setup_logging`, `parse_date`, 引数ヘルパー）
- `commands/sync_tide.py`: sync-tide コマンドの引数定義と実行ロジック
- `commands/reset_tide.py`: reset-tide コマンドの引数定義と実行ロジック
- `commands/cleanup_images.py`: cleanup-images コマンドの引数定義と実行ロジック
- テストも同様に分割（`test_cli.py` → ディスパッチャーテスト + コマンド別テスト4ファイル）

**依存**: T-012
**詳細ドキュメント**: [docs/completed/issue-90.md](completed/issue-90.md)

## フェーズ 2: 直前更新（予報）

### タスク分割

#### T-014: Weather API クライアント
**責務**: 気象予報APIのラッパー

**ステータス**: ⏸️ Pending（API 選定待ち）

**Pending 理由**（2026-02-11）:
- Issue #25 で指定の tsukumijima API を実測調査した結果、風速 (m/s) と気圧 (hPa) の数値データが提供されないことが判明
- 現行 `FishingCondition` モデル（`wind_speed_mps: float`, `pressure_hpa: float` を必須）と不整合
- 代替候補として Open-Meteo API（無料、風速・気圧・気温を数値提供、日本対応）を調査済み
- API 選定の決定後に実装を再開する
- 詳細: Issue #25 コメント参照

**ブロック影響**: T-015, T-017, T-018, T-019（一部）が本タスクに依存

**成果物**:
- `infrastructure/clients/weather_api_client.py`
  - 予報データ取得
  - レートリミット対応
  - リトライロジック

**テスト要件**:
- Mock APIレスポンスで単体テスト
- レートリミットエラー時のリトライテスト

**依存**: なし

---

#### T-015: WeatherRepository 実装
**責務**: 予報データの取得とDomainモデル変換

**成果物**:
- `infrastructure/repositories/weather_repository.py`
  - `IWeatherRepository` の実装
  - APIレスポンスを `FishingCondition` に変換

**テスト要件**:
- Mockクライアントで単体テスト
- 実データで統合テスト

**依存**: T-001, T-002, T-014

---

#### T-016: イベント本文フォーマッター
**責務**: カレンダーイベント本文の生成・更新

**成果物**:
- `domain/services/event_description_formatter.py`
  - 天文潮セクション生成
  - 予報セクション生成
  - `[TIDE]`, `[FORECAST]`, `[NOTES]` セクションを使った差分更新
  - セクション欠落時は更新をスキップして警告ログ

**テスト要件**:
- 本文の生成テスト
- 予報セクションの部分更新テスト
- 手動追記の保持確認

**依存**: T-001

---

#### T-017: SyncWeatherUseCase 実装
**責務**: 予報更新のオーケストレーション

**成果物**:
- `application/usecases/sync_weather_usecase.py`
  - 予報データ取得
  - 既存イベント取得
  - 予報セクション更新
  - イベント更新

**テスト要件**:
- Mockリポジトリで単体テスト
- 実リポジトリでE2Eテスト

**依存**: T-001, T-002, T-009, T-015, T-016

---

#### T-018: Scheduler 実装
**責務**: バッチスケジュール管理

**成果物**:
- `presentation/scheduler.py`
  - APSchedulerを使用
  - Sync-Tide：月次実行
  - Sync-Weather：3時間ごと実行
  - 優先時間帯（4-7時, 20-23時）の頻度調整（将来拡張）

**テスト要件**:
- Mock UseCaseでスケジュールテスト
- タイマー発火確認

**依存**: T-010, T-017

---

### フェーズ 2 の成果物
- 1週間前から前日までの更新が反映される
- 3時間ごとの自動更新
- 風速・風向・気圧の予報情報がイベント本文に追記
- 手動追記セクションを保持したまま更新

---

## フェーズ 3: 運用強化

### タスク分割

#### T-019: リトライロジック強化
**責務**: 失敗時の自動リトライと通知

**成果物**:
- `infrastructure/retry_policy.py`
  - Exponential backoff
  - 最大リトライ回数設定
- 失敗通知機構（ログまたはメール）

**依存**: T-010, T-017

---

#### T-020: 監視ログ
**責務**: 構造化ログと監視

**成果物**:
- 構造化ログ（JSONフォーマット）
- バッチ実行統計（成功/失敗件数、実行時間）
  - JSONキー一覧（例）: `job_name`, `location_id`, `status`, `duration_ms`, `started_at`, `finished_at`, `error_type`, `error_message`
  - MVPでは開始/終了/例外ログを先行実装

**依存**: 全UseCase

---

#### T-021: 複数地点対応
**責務**: 設定ファイルで複数地点を扱えるようにする

**成果物**:
- `locations` 配列の複数要素をサポート
- UseCaseに地点ループ処理を追加
- 地点別のカレンダー分離オプション

**依存**: T-011

---

## 相談事項（後日詰める）
- 計算ライブラリの精度評価（許容誤差の基準）
- タイドグラフ画像のホスティング方法
- Google カレンダーの画像添付方式
- Google カレンダー API のイベント ID 制約確認
- 公式/準公式データの利用規約と安定性確認
- 本文の自動生成セクションの仕様確定
- `extendedProperties` に管理タグ・更新ハッシュを持たせるかの判断
- 設定から外れた地点の未来イベント削除（ガベージコレクション）の方針
- 予報値に差分がない場合の更新スキップ方針
- 時合い帯の時間指定イベント化（別カレンダー運用を含む）
- MVP運用結果を踏まえた `trips` 導入タスクの要件・設計・テスト観点の再検討
- MVP運用結果を踏まえた `trips_calendar` 運用ルール（重複防止・更新対象）の再検討

---

## レイヤードアーキテクチャの利点（まとめ）

| 観点 | 利点 |
|------|------|
| **テスト容易性** | 各層を独立してテスト可能。MockリポジトリでUseCaseを単体テスト |
| **保守性** | 責務が明確なため、変更の影響範囲が限定される |
| **拡張性** | 新機能追加時に既存コードへの影響が少ない |
| **依存性逆転** | Domain層が外部ライブラリに依存せず、ビジネスロジックが純粋 |
| **並行開発** | 各層を独立して開発可能（インタフェースを先に定義） |
| **再利用性** | Domainサービスは他のUseCaseからも利用可能 |

---

## ディレクトリ構造（予定）

```
fishing-forecast-gcal/
├── src/
│   ├── domain/
│   │   ├── models/
│   │   │   ├── tide.py
│   │   │   ├── fishing_condition.py
│   │   │   ├── calendar_event.py
│   │   │   └── location.py
│   │   ├── services/
│   │   │   ├── tide_calculation_service.py
│   │   │   ├── tide_type_classifier.py
│   │   │   ├── prime_time_finder.py
│   │   │   └── event_description_formatter.py
│   │   └── repositories/
│   │       ├── tide_data_repository.py
│   │       ├── weather_repository.py
│   │       └── calendar_repository.py
│   ├── application/
│   │   └── usecases/
│   │       ├── sync_tide_usecase.py
│   │       └── sync_weather_usecase.py
│   ├── infrastructure/
│   │   ├── adapters/
│   │   │   └── tide_calculation_adapter.py
│   │   ├── clients/
│   │   │   ├── google_calendar_client.py
│   │   │   └── weather_api_client.py
│   │   └── repositories/
│   │       ├── tide_data_repository.py
│   │       ├── weather_repository.py
│   │       └── calendar_repository.py
│   └── presentation/
│       ├── cli.py
│       ├── scheduler.py
│       └── config_loader.py
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/
│   └── e2e/
├── config/
│   ├── config.yaml (gitignore)
│   └── config.yaml.template
└── docs/
```
