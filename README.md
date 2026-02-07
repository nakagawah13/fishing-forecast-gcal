# Fishing Forecast GCal

釣行計画のために、潮汐・潮回り・満干潮時刻・タイドグラフ画像、さらに風速などの予報情報を Google カレンダーへ埋め込むツールを目指します。

## 目的
- 潮汐（天文潮）に基づく満潮・干潮の時刻と潮回りをカレンダーに登録する
- タイドグラフを画像として可視化し、カレンダーに埋め込む
- 風速など変化する予報情報を自動更新できる設計にする

## 状況
- まずは MVP（天文潮ベースの予定作成）を優先
- 風速などの予報値は直前更新フェーズで扱う

## ドキュメント
- 全体像: [docs/architecture.md](docs/architecture.md)
- 要件整理: [docs/requirements.md](docs/requirements.md)
- データソース候補: [docs/data_sources.md](docs/data_sources.md)
- 実装計画: [docs/implementation_plan.md](docs/implementation_plan.md)
- Gemini 会話整理: [docs/conversation_gemini.md](docs/conversation_gemini.md)
- ドキュメント一覧: [docs/document_index.md](docs/document_index.md)

## 次のアクション（予定）
- MVP 仕様の確定
- 潮汐データ取得方法の決定
- Google カレンダー連携の PoC
