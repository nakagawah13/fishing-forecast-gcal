# Data Sources

## 潮汐（天文潮）
- 方式 A: 天文潮計算ライブラリ
- 方式 B: 公開 API や配布される潮汐データ

比較観点:
- 精度（地点ごとの補正の可否）
- ライセンスと利用規約
- API 制限（レート・日次上限）
- オフライン実行の可否

**採用決定（MVP）**:
- **UTide ライブラリ**（https://github.com/wesleybowman/UTide）を採用
  - 調和解析による潮汐予測
  - MITライセンス（商用利用可能）
  - オフライン実行可能
  - 地点ごとの調和定数データが必要
- 公式潮見表と差分比較を行い、精度を検証
- 差分が許容範囲を超える場合は調和定数の調整または API への切り替えを検討

**データソース（実装済み）**:
- **気象庁 潮汐観測データ**（毎時潮位テキストファイル）
  - URL: `https://www.data.jma.go.jp/gmd/kaiyou/data/db/tide/genbo/{YYYY}/{YYYYMM}/hry{YYYYMM}{STN}.txt`
  - フォーマット: 137文字固定長（1行 = 1日、3桁 × 24時間の毎時潮位）
  - 対応地点: 17 JMA 主要観測地点（TK=東京, MR=布良, OK=岡田, SM=清水港 等）
  - 参考: [JMAtide](https://github.com/hydrocoast/JMAtide)（MATLAB, MIT License）— URL パターン解析に使用
- **データ取得 → 調和定数生成の流れ**:
  1. `scripts/fetch_jma_tide_data.py` で気象庁の観測潮位データを HTTP 取得
  2. UTide `solve()` で調和解析を実行
  3. 結果を pickle 形式で `config/harmonics/{station}.pkl` に保存
  4. `TideCalculationAdapter` が pickle を読み込み、UTide `reconstruct()` で予測実行

注意点:
- 非公式 API やスクレイピングは規約違反や仕様変更のリスクがある
- 公的データでも提供条件や再配布条件の確認が必要

## 風速・風向などの予報
- 方式 A: 天気予報 API（風速、風向、気圧）
- 方式 B: 予報値 CSV の定期取得

候補（参考）:
- https://weather.tsukumijima.net/
	- 気象庁配信データを加工した非公式 API
	- 注意: 仕様変更や停止の可能性がある
	- 注意: アクセス間隔の制限やユーザーエージェント設定が必要

## タイドグラフ画像
- ライブラリでの描画（PNG/SVG）
- 画像ホスティング（GCS、S3 など）

## Google カレンダー連携
- Google Calendar API でイベント作成・更新
- 画像はイベント本文に URL を埋め込み

MVP 方針:
- 画像は扱わず、本文のテキスト情報のみで運用
