# Issue #79: タイドグラフ画像生成サービスの実装

**ステータス**: 🔵 In Progress
**担当**: AI Assistant
**作成日**: 2026-02-11
**関連Issue**: #79
**フェーズ**: Phase 1.9
**親Issue**: #76（POC — 方式B採用決定）
**前提**: #78（Google Drive/Calendar API 添付機能）✅ Completed

---

## 概要

潮汐データからタイドグラフ画像を生成する Domain サービス `TideGraphService` を実装する。
matplotlib + seaborn + matplotlib-fontja を使用し、スマホ表示に最適化されたダークモード基調の画像を生成する。

## 実装方針

### アーキテクチャ配置

```
Domain Layer:
  services/
    tide_graph_service.py      ← 新規: タイドグラフ画像生成サービス

Tests:
  tests/unit/domain/services/
    test_tide_graph_service.py  ← 新規
```

**注**: Issue の成果物に挙げられていた `IImageRepository` は、本 Issue のスコープでは不要。
画像の保存先は後続の ST-4（#80: SyncTideUseCase への統合）で Drive にアップロードするため、
Domain サービスは一時ファイルの `Path` を返すだけで十分。

### 主要設計判断

1. **入力データ**: `TideGraphService.generate_graph()` は以下を受け取る:
   - `target_date: date` — 対象日
   - `hourly_heights: list[tuple[float, float]]` — (時刻(h), 潮位(cm)) のペアリスト
   - `tide_events: list[TideEvent]` — 満干潮イベント
   - `location_name: str` — 地点名（タイトル用）
   - `tide_type: TideType` — 潮回り（タイトル用）
   - `prime_time: tuple[datetime, datetime] | None` — 時合い帯（ハイライト用）
   - `output_dir: Path` — 出力ディレクトリ
   - `location_id: str` — ファイル名用

2. **出力**: PNG 画像ファイルの `Path` を返す

3. **`hourly_heights` の取得元**:
   - `TideCalculationAdapter.calculate_tide()` が返す `list[tuple[datetime, float]]` を変換
   - 呼び出し元（ST-4 で SyncTideUseCase）が変換して渡す

## 画像仕様

| 項目 | 仕様 |
|------|------|
| アスペクト比 | 1:1（スクエア） |
| サイズ | 6×6 インチ (900×900px @150dpi) |
| ファイルサイズ | 100KB 以下目標 |
| フォーマット | PNG |
| 配色 | ダークモード基調（背景 `#0d1117`） |
| 日本語フォント | `matplotlib-fontja`（IPAexゴシック同梱） |

### カラーパレット

| 要素 | カラーコード |
|------|-------------|
| 背景 | `#0d1117` |
| 潮位曲線 | `#58a6ff` |
| 海面フィル | `#58a6ff` (alpha=0.15) |
| 満潮マーカー | `#f0883e` |
| 干潮マーカー | `#3fb950` |
| 時合い帯 | `#d29922` (alpha=0.15) |
| グリッド | `#30363d` |
| テキスト | `#c9d1d9` |
| タイトル | `#f0f6fc` |

### 描画要素

1. 潮位曲線（24 時間分）
2. 海面フィル（曲線下の半透明塗りつぶし）
3. 満干潮マーカー（●ドット + 時刻/潮位の 2 行ラベル）
4. 時合い帯ハイライト（半透明の縦帯）
5. グリッド（低コントラストグレー）
6. タイトル: `{地名} {YYYY年MM月DD日}` + 潮回り絵文字
7. X 軸: 0〜24 時（3 時間刻み）
8. Y 軸: 潮位 (cm)

### ファイル命名規則

```
tide_graph_{location_id}_{YYYYMMDD}.png
```

## 変更予定ファイル

### 新規作成
- `src/fishing_forecast_gcal/domain/services/tide_graph_service.py`
- `tests/unit/domain/services/test_tide_graph_service.py`

### 変更
- `src/fishing_forecast_gcal/domain/services/__init__.py` — エクスポート追加

## テスト計画

1. 画像ファイルが正常に生成されること
2. ファイルサイズが 100KB 以下であること
3. ダークモード配色が正しく適用されていること（背景色チェック）
4. 満干潮アノテーション（時刻・潮位）が含まれていること
5. 地名がタイトルに含まれていること
6. 時合い帯ハイライトが正しい時間帯に表示されること
7. 異常データ（空リスト等）でのエラーハンドリング
8. 時合い帯なし（None）の場合でも正常に描画されること
9. ruff / pyright パス

## 依存

- T-001: ドメインモデル定義（✅ 完了）— `TideEvent`, `TideType`
- T-005: 時合い帯特定サービス（✅ 完了）— `PrimeTimeFinder`
- T-013.11: タイドグラフ画像の表示方式POC（✅ 完了）— 画像仕様確定
