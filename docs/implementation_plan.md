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
- イベント ID 生成: `calendar_id + location_id + date` を素材に安定ハッシュで生成

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

**ステータス**: ✅ 完了（2026-02-08）

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

#### ✅ T-007: TideDataRepository 実装
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

#### T-009: CalendarRepository 実装
**責務**: カレンダーイベントの作成・取得・更新

**成果物**:
- `infrastructure/repositories/calendar_repository.py`
  - `ICalendarRepository` の実装
  - DomainモデルとGoogle API形式の変換
  - イベントID生成（`calendar_id + location_id + date` を素材に MD5 ハッシュ）
  - upsertロジック

**テスト要件**:
- Mockクライアントで単体テスト
- 冗等性テスト（同一IDで複数回実行）

**依存**: T-001, T-002, T-008

---

### 1.3 Application Layer（ユースケース）

#### T-010: SyncTideUseCase 実装
**責務**: 天文潮の同期処理をオーケストレーション

**成果物**:
- `application/usecases/sync_tide_usecase.py`
  - 潮汐データ取得
  - 満干潮抽出
  - 潮回り判定
  - 時合い帯計算
  - カレンダーイベント作成/更新

**テスト要件**:
- Mockリポジトリで単体テスト
- エンドツーエンドテスト（実リポジトリ使用）

**依存**: T-001, T-002, T-003, T-004, T-005, T-007, T-009

---

### 1.4 Presentation Layer（CLI・設定）

#### T-011: 設定ファイルローダー
**責務**: `config.yaml` の読み込みと検証

**成果物**:
- `presentation/config_loader.py`
  - YAMLパース
  - スキーマ検証
  - Locationモデルへのマッピング
  - Locationの不変ID（`locations[].id`）の読み込み
  - OAuth 認証パス（`google_credentials_path`, `google_token_path`）の読み込み

**テスト要件**:
- 正常なYAMLのパース
- 不正なYAMLのエラー検知

**依存**: T-001

---

#### T-012: CLIエントリーポイント
**責務**: コマンドラインインターフェース

**成果物**:
- `presentation/cli.py`
  - 引数パース（argparse）
  - SyncTideUseCaseの呼び出し
  - ログ出力

**テスト要件**:
- CLI引数のパーステスト
- Mock UseCaseで呼び出し確認

**依存**: T-010, T-011

---

### 1.5 統合テスト

#### T-013: E2Eテスト
**責務**: システム全体の統合テスト

**成果物**:
- `tests/e2e/test_sync_tide_flow.py`
  - テストカレンダーへの実際の登録
  - 冗等性確認（複数回実行）
  - 公式潮見表との差分検証

**依存**: 全タスク

---

## フェーズ 1 の成果物
- 1か月分の潮汐イベントを生成・登録できる（画像なし）
- レイヤードアーキテクチャで実装され、各層が独立してテスト可能
- 複数回実行しても重複登録が起きない（冗等性）

---

## フェーズ 2: 直前更新（予報）

### タスク分割

#### T-014: Weather API クライアント
**責務**: 気象予報APIのラッパー

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
