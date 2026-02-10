# Fishing Forecast GCal

**最終更新**: 2026-02-10

釣行計画のために、潮汐・潮回り・満干潮時刻を Google カレンダーへ自動登録するツールです。

## 🎯 MVP達成（Phase 1完了）

**Phase 1（天文潮ベースのMVP）** が完了しました。以下の機能が実装済みです:

### 実装済み機能

- ✅ **天文潮の計算**: UTideライブラリによる高精度な潮汐計算
- ✅ **満潮・干潮の算出**: 日次での満潮・干潮時刻とピーク潮位の算出
- ✅ **潮回り判定**: 大潮・中潮・小潮・長潮・若潮の自動判定
- ✅ **時合い帯の特定**: 満潮±2時間の釣行好適時間帯の算出
- ✅ **Google カレンダー連携**: 終日イベントとして自動登録
- ✅ **CLI操作**: コマンドラインからの同期実行
- ✅ **レイヤードアーキテクチャ**: 保守性・テスト容易性を重視した設計
- ✅ **潮回り絵文字表示**: タイトルに視認性の高い絵文字アイコン（🔴大潮 🟠中潮 🔵小潮 等）
- ✅ **中央日マーカー**: 大潮期間の中央日を⭐で表示
- ✅ **潮位基準面の明文化**: UTide による観測基準面からの潮位計算を文書化

### イベントフォーマット

カレンダーに登録されるイベントは以下の形式です:

```
タイトル: 🔴東京 (大潮)
種別: 終日イベント

本文:
[TIDE]
- 満潮: 06:12 (162cm)
- 干潮: 12:34 (58cm)
- 時合い: 04:12-08:12
- ⭐ 中央日（大潮期間の中央日のみ表示）

[FORECAST]
（Phase 2で実装予定）

[NOTES]
（ユーザーメモ欄）
```

**潮回りアイコン**:
- 🔴 大潮
- 🟠 中潮
- 🔵 小潮
- ⚪ 長潮
- 🟢 若潮

## 🚀 クイックスタート

### 1. 環境セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/nakagawah13/fishing-forecast-gcal.git
cd fishing-forecast-gcal

# 依存関係をインストール（uvが必要）
uv sync
```

### 2. Google Calendar API の設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. Google Calendar API を有効化
3. OAuth 同意画面を設定（Testing モードでOK）
4. デスクトップアプリ用のOAuthクライアントIDを作成
5. `credentials.json` をダウンロードし `config/` に配置

### 3. 調和定数の生成

潮汐計算に必要な調和定数を生成します:

```bash
# 例: 東京（TK）の2025年データで調和定数を生成
uv run python scripts/fetch_jma_tide_data.py --station TK --year 2025

# 利用可能な地点一覧を表示
uv run python scripts/fetch_jma_tide_data.py --list-stations
```

生成された調和定数ファイル（`.pkl`）は `config/harmonics/` に保存されます。

### 4. 設定ファイルの作成

```bash
# テンプレートをコピー
cp config/config.yaml.template config/config.yaml
```

`config/config.yaml` を編集し、以下を設定:

```yaml
google:
  credentials_path: "config/credentials.json"
  token_path: "config/token.json"
  calendar_id: "your_calendar_id@group.calendar.google.com"

locations:
  - id: "tk"  # 調和定数ファイル名に対応
    name: "東京"
    lat: 35.6544
    lon: 139.7447

settings:
  timezone: "Asia/Tokyo"
  forecast_window_days: 7
```

### 5. 初回認証

```bash
# CLIを実行して初回認証
uv run fishing-forecast-gcal sync-tide --days 30

# ブラウザが開き、Googleアカウントでの認証を求められます
# 認証完了後、config/token.json が生成されます
```

### 6. 同期実行

```bash
# 潮汐データを同期（30日分）
uv run fishing-forecast-gcal sync-tide --days 30

# 実行ログで同期状況を確認
```

## 📋 設定ファイル

個人の地点情報とAPI認証情報を含むため、実体ファイルはGit管理から除外されています。

**重要なファイル**:
- `config/config.yaml`: メイン設定（テンプレートから作成）
- `config/credentials.json`: Google OAuth クレデンシャル
- `config/token.json`: 認証トークン（初回認証後に自動生成）
- `config/harmonics/*.pkl`: 潮汐調和定数（スクリプトで生成）

## 🏗️ アーキテクチャ

本プロジェクトは **レイヤードアーキテクチャ** を採用しています:

```
Presentation Layer (CLI)
    ↓
Application Layer (UseCases)
    ↓
Domain Layer (Models, Services)
    ↑
Infrastructure Layer (Repositories, API Clients)
```

詳細は [docs/architecture.md](docs/architecture.md) を参照してください。

## 🧪 テスト

```bash
# 全テストを実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=src --cov-report=html

# 型チェック
uv run pyright

# Lint
uv run ruff check .
```

## 📚 ドキュメント

- **アーキテクチャ**: [docs/architecture.md](docs/architecture.md)
- **要件定義**: [docs/requirements.md](docs/requirements.md)
- **実装計画**: [docs/implementation_plan.md](docs/implementation_plan.md)
- **タスク一覧**: [docs/task_table.md](docs/task_table.md)
- **データソース**: [docs/data_sources.md](docs/data_sources.md)
- **ドキュメント索引**: [docs/document_index.md](docs/document_index.md)

## 🔜 次のステップ（Phase 2: 予報更新）

Phase 2では以下の機能を実装予定です:

- 🌤️ **気象予報の取得**: 風速・風向・気圧などの予報データ
- 🔄 **自動更新**: 3時間ごとの予報更新
- 📅 **フォーマット統合**: `[FORECAST]` セクションへの予報データ反映
- ⏰ **スケジューラー**: 定期実行の自動化

詳細は [docs/implementation_plan.md](docs/implementation_plan.md) のPhase 2セクションを参照してください。

## 📝 ライセンス

[LICENSE](LICENSE) を参照してください。

## 🤝 コントリビューション

Issue や Pull Request を歓迎します。
実装計画に沿った貢献をお願いします。
