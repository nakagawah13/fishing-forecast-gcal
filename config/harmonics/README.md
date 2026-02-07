# Harmonics Directory

UTide で生成した潮汐調和定数の pickle ファイルを格納するディレクトリです。

## ファイル命名規則

`{station_id}.pkl` — JMA 地点コード（小文字）+ `.pkl`

例: `tk.pkl`（東京）

## 生成方法

```bash
# 東京（TK）の 2025 年全月データで調和定数を生成
uv run python scripts/fetch_jma_tide_data.py --station TK --year 2025

# 利用可能な地点一覧を表示
uv run python scripts/fetch_jma_tide_data.py --list-stations
```

## 注意事項

- `.pkl` ファイルはバイナリのため `.gitignore` で除外されています
- 実データは各自のローカル環境で生成してください
- 生成には気象庁サーバーへのアクセスが必要です
