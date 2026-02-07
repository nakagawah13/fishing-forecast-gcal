# Task Table

- Implementation plan: [implementation_plan.md](implementation_plan.md)
- This table mirrors the tasks defined in the implementation plan.

## 運用手順（Issue ドリブン）
1. Issue ごとに作業ブランチを発行
2. 現在の実装に合わせて Issue を最適化
3. docs/inprogress に内容を書き起こす
4. 書き起こしたドキュメントを見ながら実装し、段階的にコミット
5. pytest, ruff, pyright を実行
6. 通過後、Issue ドキュメントのステータスを completed に更新し、docs/completed に移動（実装結果を追記）
7. [implementation_plan.md](implementation_plan.md) を更新
8. PR 作成

## フェーズ 0（仕様確定）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| F0-01 | 0 | 対象地点/期間/出力フォーマットの合意 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | TBD | Not Started |
| F0-02 | 0 | Google カレンダーのイベント設計確定 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | TBD | Not Started |
| F0-03 | 0 | 天文潮の取得方式を決定 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | TBD | Not Started |
| F0-04 | 0 | タイドグラフ画像の表現方針（後続検討） | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | TBD | Not Started |
| F0-05 | 0 | 開発環境手順（uv）をドキュメント化 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | TBD | Not Started |
| F0-06 | 0 | 配布/セットアップ手順の草案化 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | TBD | Not Started |
| F0-07 | 0 | 更新ウィンドウの範囲を決定 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | TBD | Not Started |
| F0-08 | 0 | レイヤードアーキテクチャの詳細設計 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | TBD | Not Started |

## フェーズ 1（MVP）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| T-001 | 1.1 | ドメインモデル定義 | [implementation_plan.md](implementation_plan.md#t-001-ドメインモデル定義) | TBD | Not Started |
| T-002 | 1.1 | リポジトリインターフェース定義 | [implementation_plan.md](implementation_plan.md#t-002-リポジトリインターフェース定義) | TBD | Not Started |
| T-003 | 1.1 | 潮汐計算サービス | [implementation_plan.md](implementation_plan.md#t-003-潮汐計算サービス) | TBD | Not Started |
| T-004 | 1.1 | 潮回り判定サービス | [implementation_plan.md](implementation_plan.md#t-004-潮回り判定サービス) | TBD | Not Started |
| T-005 | 1.1 | 時合い帯特定サービス | [implementation_plan.md](implementation_plan.md#t-005-時合い帯特定サービス) | TBD | Not Started |
| T-006 | 1.2 | 潮汐計算ライブラリアダプター | [implementation_plan.md](implementation_plan.md#t-006-潮汐計算ライブラリアダプター) | TBD | Not Started |
| T-007 | 1.2 | TideDataRepository 実装 | [implementation_plan.md](implementation_plan.md#t-007-tidedatarepository-実装) | TBD | Not Started |
| T-008 | 1.2 | Google Calendar API クライアント | [implementation_plan.md](implementation_plan.md#t-008-google-calendar-api-クライアント) | TBD | Not Started |
| T-009 | 1.2 | CalendarRepository 実装 | [implementation_plan.md](implementation_plan.md#t-009-calendarrepository-実装) | TBD | Not Started |
| T-010 | 1.3 | SyncTideUseCase 実装 | [implementation_plan.md](implementation_plan.md#t-010-synctideusecase-実装) | TBD | Not Started |
| T-011 | 1.4 | 設定ファイルローダー | [implementation_plan.md](implementation_plan.md#t-011-設定ファイルローダー) | TBD | Not Started |
| T-012 | 1.4 | CLI エントリーポイント | [implementation_plan.md](implementation_plan.md#t-012-cliエントリーポイント) | TBD | Not Started |
| T-013 | 1.5 | E2E テスト | [implementation_plan.md](implementation_plan.md#t-013-e2eテスト) | TBD | Not Started |

## フェーズ 2（予報更新）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| T-014 | 2 | Weather API クライアント | [implementation_plan.md](implementation_plan.md#t-014-weather-api-クライアント) | TBD | Not Started |
| T-015 | 2 | WeatherRepository 実装 | [implementation_plan.md](implementation_plan.md#t-015-weatherrepository-実装) | TBD | Not Started |
| T-016 | 2 | イベント本文フォーマッター | [implementation_plan.md](implementation_plan.md#t-016-イベント本文フォーマッター) | TBD | Not Started |
| T-017 | 2 | SyncWeatherUseCase 実装 | [implementation_plan.md](implementation_plan.md#t-017-syncweatherusecase-実装) | TBD | Not Started |
| T-018 | 2 | Scheduler 実装 | [implementation_plan.md](implementation_plan.md#t-018-scheduler-実装) | TBD | Not Started |

## フェーズ 3（運用強化）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| T-019 | 3 | リトライロジック強化 | [implementation_plan.md](implementation_plan.md#t-019-リトライロジック強化) | TBD | Not Started |
| T-020 | 3 | 監視ログ | [implementation_plan.md](implementation_plan.md#t-020-監視ログ) | TBD | Not Started |
| T-021 | 3 | 複数地点対応 | [implementation_plan.md](implementation_plan.md#t-021-複数地点対応) | TBD | Not Started |
