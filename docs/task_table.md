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
| F0-01 | 0 | 対象地点/期間/出力フォーマットの合意 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | [#4](https://github.com/nakagawah13/fishing-forecast-gcal/issues/4) | Not Started |
| F0-02 | 0 | Google カレンダーのイベント設計確定 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | [#5](https://github.com/nakagawah13/fishing-forecast-gcal/issues/5) | ✅ Completed |
| F0-03 | 0 | 天文潮の取得方式を決定 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | [#6](https://github.com/nakagawah13/fishing-forecast-gcal/issues/6) | ✅ Completed |
| F0-04 | 0 | タイドグラフ画像の表現方針（後続検討） | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | [#7](https://github.com/nakagawah13/fishing-forecast-gcal/issues/7) | ✅ Completed |
| F0-05 | 0 | 開発環境手順（uv）をドキュメント化 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | [#8](https://github.com/nakagawah13/fishing-forecast-gcal/issues/8) | ✅ Completed |
| F0-06 | 0 | 配布/セットアップ手順の草案化 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | [#9](https://github.com/nakagawah13/fishing-forecast-gcal/issues/9) | Not Started |
| F0-07 | 0 | 更新ウィンドウの範囲を決定 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | [#10](https://github.com/nakagawah13/fishing-forecast-gcal/issues/10) | ✅ Completed |
| F0-08 | 0 | レイヤードアーキテクチャの詳細設計 | [implementation_plan.md](implementation_plan.md#フェーズ-0-仕様確定短期) | [#11](https://github.com/nakagawah13/fishing-forecast-gcal/issues/11) | ✅ Completed |

## フェーズ 1（MVP）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| T-001 | 1.1 | ドメインモデル定義 | [implementation_plan.md](implementation_plan.md#t-001-ドメインモデル定義) | [#12](https://github.com/nakagawah13/fishing-forecast-gcal/issues/12) | ✅ Completed |
| T-002 | 1.1 | リポジトリインターフェース定義 | [implementation_plan.md](implementation_plan.md#t-002-リポジトリインターフェース定義) | [#13](https://github.com/nakagawah13/fishing-forecast-gcal/issues/13) | ✅ Completed |
| T-003 | 1.1 | 潮汐計算サービス | [implementation_plan.md](implementation_plan.md#t-003-潮汐計算サービス) | [#14](https://github.com/nakagawah13/fishing-forecast-gcal/issues/14) | ✅ Completed |
| T-004 | 1.1 | 潮回り判定サービス | [implementation_plan.md](implementation_plan.md#t-004-潮回り判定サービス) | [#15](https://github.com/nakagawah13/fishing-forecast-gcal/issues/15) | ✅ Completed |
| T-005 | 1.1 | 時合い帯特定サービス | [implementation_plan.md](implementation_plan.md#t-005-時合い帯特定サービス) | [#16](https://github.com/nakagawah13/fishing-forecast-gcal/issues/16) | ✅ Completed |
| T-006 | 1.2 | 潮汐計算ライブラリアダプター | [implementation_plan.md](implementation_plan.md#t-006-潮汐計算ライブラリアダプター) | [#17](https://github.com/nakagawah13/fishing-forecast-gcal/issues/17) | ✅ Completed |
| T-007 | 1.2 | TideDataRepository 実装 | [implementation_plan.md](implementation_plan.md#t-007-tidedatarepository-実装) | [#18](https://github.com/nakagawah13/fishing-forecast-gcal/issues/18) | ✅ Completed |
| T-008 | 1.2 | Google Calendar API クライアント | [implementation_plan.md](implementation_plan.md#t-008-google-calendar-api-クライアント) | [#19](https://github.com/nakagawah13/fishing-forecast-gcal/issues/19) | ✅ Completed |
| T-009 | 1.2 | CalendarRepository 実装 | [implementation_plan.md](implementation_plan.md#t-009-calendarrepository-実装) | [#20](https://github.com/nakagawah13/fishing-forecast-gcal/issues/20) | ✅ Completed |
| T-010 | 1.3 | SyncTideUseCase 実装 | [implementation_plan.md](implementation_plan.md#t-010-synctideusecase-実装) | [#21](https://github.com/nakagawah13/fishing-forecast-gcal/issues/21) | ✅ Completed |
| T-011 | 1.4 | 設定ファイルローダー | [implementation_plan.md](implementation_plan.md#t-011-設定ファイルローダー) | [#22](https://github.com/nakagawah13/fishing-forecast-gcal/issues/22) | ✅ Completed |
| T-012 | 1.4 | CLI エントリーポイント | [implementation_plan.md](implementation_plan.md#t-012-cliエントリーポイント) | [#23](https://github.com/nakagawah13/fishing-forecast-gcal/issues/23) | ✅ Completed |
| T-013 | 1.5 | E2E テスト | [implementation_plan.md](implementation_plan.md#t-013-e2eテスト) | [#24](https://github.com/nakagawah13/fishing-forecast-gcal/issues/24) | ✅ Completed |
| T-013.1 | 1.5 | station_id マッピングの導入 ([doc](completed/t-0131-station-id-mapping.md)) | [implementation_plan.md](implementation_plan.md#t-0131-station_id-マッピングの導入) | N/A | ✅ Completed |
| T-013.2 | 1.6 | 分単位の潮汐時刻精度改善 | [implementation_plan.md](implementation_plan.md#t-0132-分単位の潮汐時刻精度改善) | [#53](https://github.com/nakagawah13/fishing-forecast-gcal/issues/53) | ✅ Completed |
| T-013.3 | 1.6 | 満干潮の欠落調査と修正 | [implementation_plan.md](implementation_plan.md#t-0133-満干潮の欠落調査と修正) | [#54](https://github.com/nakagawah13/fishing-forecast-gcal/issues/54) | ✅ Completed |
| T-013.4 | 1.6 | 潮位基準面の説明と補正方針 ([doc](completed/issue-55.md)) | [implementation_plan.md](implementation_plan.md#t-0134-潮位基準面の説明と補正方針) | [#55](https://github.com/nakagawah13/fishing-forecast-gcal/issues/55) | ✅ Completed |
| T-013.5 | 1.6 | 潮回り期間中央日のマーカー ([doc](completed/issue-57.md)) | [implementation_plan.md](implementation_plan.md#t-0135-潮回り期間中央日のマーカー) | [#57](https://github.com/nakagawah13/fishing-forecast-gcal/issues/57) | ✅ Completed |
| T-013.6 | 1.6 | イベントタイトルの潮回り絵文字化 ([doc](completed/issue-56.md)) | [implementation_plan.md](implementation_plan.md#t-0136-イベントタイトルの潮回り絵文字化) | [#56](https://github.com/nakagawah13/fishing-forecast-gcal/issues/56) | ✅ Completed |
| T-013.7 | 1.7 | 釣り情報の初期化コマンド ([doc](completed/issue-58.md)) | [implementation_plan.md](implementation_plan.md#t-0137-釣り情報の初期化コマンド) | [#58](https://github.com/nakagawah13/fishing-forecast-gcal/issues/58) | ✅ Completed |

## フェーズ 1.8（MVP安定化・第3弾）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| T-013.8 | 1.8 | JMA推算テキストパーサーの分離 | [implementation_plan.md](implementation_plan.md#t-0138-jma推算テキストパーサーの分離) | [#69](https://github.com/nakagawah13/fishing-forecast-gcal/issues/69) | ✅ Completed |
| T-013.9 | 1.8 | JMA潮汐データ取得ロジックの正式モジュール化と全70地点拡張 | [implementation_plan.md](implementation_plan.md#t-0139-jma潮汐データ取得ロジックの正式モジュール化と全70地点拡張) | [#70](https://github.com/nakagawah13/fishing-forecast-gcal/issues/70) | ✅ Completed |
| T-013.10 | 1.8 | upsert_event の重複 get_event API 呼び出し削除 ([doc](completed/issue-46.md)) | [implementation_plan.md](implementation_plan.md#t-01310-upsert_event-の重複-get_event-api-呼び出し削除) | [#46](https://github.com/nakagawah13/fishing-forecast-gcal/issues/46) | ✅ Completed |

## フェーズ 1.9（MVP安定化・第4弾）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| T-013.11 | 1.9 | タイドグラフ画像の表示方式POC ([doc](completed/issue-76.md)) | [implementation_plan.md](implementation_plan.md#t-01311-タイドグラフ画像の表示方式poc) | [#76](https://github.com/nakagawah13/fishing-forecast-gcal/issues/76) | ✅ Completed |
| T-013.11a | 1.9 | Google Drive/Calendar API 添付機能の実装 ([doc](completed/issue-78.md)) | [implementation_plan.md](implementation_plan.md#t-01311-タイドグラフ画像の表示方式poc) | [#78](https://github.com/nakagawah13/fishing-forecast-gcal/issues/78) | ✅ Completed |
| T-013.11b | 1.9 | タイドグラフ画像生成サービスの実装 ([doc](completed/issue-79.md)) | [implementation_plan.md](implementation_plan.md#t-01311-タイドグラフ画像の表示方式poc) | [#79](https://github.com/nakagawah13/fishing-forecast-gcal/issues/79) | ✅ Completed |
| T-013.11c | 1.9 | SyncTideUseCase への画像添付統合 ([doc](completed/issue-80.md)) | [implementation_plan.md](implementation_plan.md#t-01311-タイドグラフ画像の表示方式poc) | [#80](https://github.com/nakagawah13/fishing-forecast-gcal/issues/80) | ✅ Completed |
| T-013.11d | 1.9 | 古い Drive 画像の定期削除コマンド ([doc](completed/issue-81.md)) | [implementation_plan.md](implementation_plan.md#t-01311-タイドグラフ画像の表示方式poc) | [#81](https://github.com/nakagawah13/fishing-forecast-gcal/issues/81) | ✅ Completed |

## フェーズ 1.10（MVP安定化・第5弾）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| T-013.12 | 1.10 | CLI モジュール分割 ([doc](completed/issue-90.md)) | [implementation_plan.md](implementation_plan.md#t-01312-cli-モジュール分割clipy-の責務分離-) | [#90](https://github.com/nakagawah13/fishing-forecast-gcal/issues/90) | ✅ Completed |
| T-013.13 | 1.10 | Google API 認証ロジック共通化 ([doc](completed/issue-91.md)) | [implementation_plan.md](implementation_plan.md#t-01313-google-api-認証ロジック共通化-) | [#91](https://github.com/nakagawah13/fishing-forecast-gcal/issues/91) | ✅ Completed |
| T-013.14 | 1.10 | TideGraphService のレイヤー移動 ([doc](completed/issue-92.md)) | [implementation_plan.md](implementation_plan.md#t-01314-tidegraphservice-のレイヤー移動domain--infrastructure-) | [#92](https://github.com/nakagawah13/fishing-forecast-gcal/issues/92) | ✅ Completed |
| T-013.15 | 1.10 | TideDataRepository の DI 改善 ([doc](completed/issue-93.md)) | [implementation_plan.md](implementation_plan.md#t-01315-tidedatarepository-のドメインロジック分離と-di-改善-) | [#93](https://github.com/nakagawah13/fishing-forecast-gcal/issues/93) | ✅ Completed |
| T-013.16 | 1.10 | OAuth スコープ不一致時の再認証ハンドリング ([doc](completed/issue-98.md)) | [implementation_plan.md](implementation_plan.md#t-01316-oauth-スコープ不一致時の再認証ハンドリング) | [#98](https://github.com/nakagawah13/fishing-forecast-gcal/issues/98) | ✅ Completed |

## フェーズ 2（予報更新）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| T-014 | 2 | Weather API クライアント | [implementation_plan.md](implementation_plan.md#t-014-weather-api-クライアント) | [#25](https://github.com/nakagawah13/fishing-forecast-gcal/issues/25) | ⏸️ Pending (API選定待ち) |
| T-015 | 2 | WeatherRepository 実装 | [implementation_plan.md](implementation_plan.md#t-015-weatherrepository-実装) | [#26](https://github.com/nakagawah13/fishing-forecast-gcal/issues/26) | ⏸️ Blocked by T-014 |
| T-016 | 2 | イベント本文フォーマッター | [implementation_plan.md](implementation_plan.md#t-016-イベント本文フォーマッター) | [#27](https://github.com/nakagawah13/fishing-forecast-gcal/issues/27) | Not Started |
| T-017 | 2 | SyncWeatherUseCase 実装 | [implementation_plan.md](implementation_plan.md#t-017-syncweatherusecase-実装) | [#28](https://github.com/nakagawah13/fishing-forecast-gcal/issues/28) | ⏸️ Blocked by T-014 |
| T-018 | 2 | Scheduler 実装 | [implementation_plan.md](implementation_plan.md#t-018-scheduler-実装) | [#29](https://github.com/nakagawah13/fishing-forecast-gcal/issues/29) | ⏸️ Blocked by T-014 |

## フェーズ 3（運用強化）

| Task ID | Phase | Title | Plan Link | Issue | Status |
| --- | --- | --- | --- | --- | --- |
| T-019 | 3 | リトライロジック強化 | [implementation_plan.md](implementation_plan.md#t-019-リトライロジック強化) | [#30](https://github.com/nakagawah13/fishing-forecast-gcal/issues/30) | Not Started |
| T-020 | 3 | 監視ログ | [implementation_plan.md](implementation_plan.md#t-020-監視ログ) | [#31](https://github.com/nakagawah13/fishing-forecast-gcal/issues/31) | Not Started |
| T-021 | 3 | 複数地点対応 | [implementation_plan.md](implementation_plan.md#t-021-複数地点対応) | [#32](https://github.com/nakagawah13/fishing-forecast-gcal/issues/32) | Not Started |
