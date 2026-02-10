# Issue #70: JMA潮汐データ取得ロジックの正式モジュール化と全70地点拡張

- **Issue**: [#70](https://github.com/nakagawah13/fishing-forecast-gcal/issues/70)
- **Task ID**: T-013.9
- **Phase**: 1.8
- **Status**: 🔵 In Progress
- **Branch**: `refactor/issue-70-jma-station-module`

## 概要

`scripts/fetch_jma_tide_data.py` の地点データおよびコア機能を `src/` 配下に正式モジュールとして移動し、気象庁公式の全70地点への拡張と既存データの誤りを修正する。

## 背景

1. **コードの位置づけが不適切**: 調和定数生成はコアデータパイプラインであり `src/` で管理すべき
2. **地点データの大幅な不足**: 現行17地点 → 公式70地点（カバー率24%→100%）
3. **既存データの誤り**: FK（福岡→深浦）、HA（博多→浜田）の誤マッピング。座標・`ref_level_tp_cm` の不一致

## 実装方針

### 配置先

`src/fishing_forecast_gcal/infrastructure/jma/` に新パッケージを作成:

```
src/fishing_forecast_gcal/infrastructure/jma/
├── __init__.py
├── stations.py          # JMAStation データクラス + 全70地点辞書
├── hourly_text_parser.py # parse_jma_hourly_text 関数
└── harmonic_analysis.py  # run_harmonic_analysis 関数
```

**理由**:
- JMA地点データは気象庁APIのインフラ層に属する
- 既存の `infrastructure/adapters/tide_calculation_adapter.py` と同じ層
- `domain/` に入れると外部データソース依存が発生してしまう

### サブタスク

#### 1. `stations.py`: JMAStation データクラスと全70地点定義
- 既存 `JMAStation` データクラスを移動
- 気象庁公式一覧表（2026年版）の値で全70地点を正確に定義
- FK → 深浦、HA → 浜田 の誤り修正
- 緯度・経度は公式の度分表記から小数度に変換（小数第3位）
- `ref_level_tp_cm` は公式の「観測基準面の標高(cm)」列の値を使用

#### 2. `hourly_text_parser.py`: パーサーの移動
- `parse_jma_hourly_text` を移動
- フォーマット定数も含めて移動

#### 3. `harmonic_analysis.py`: 調和解析ロジックの移動
- `run_harmonic_analysis` を移動（scripts版）
- fetch 関連のネットワーク関数（`fetch_monthly_data`, `fetch_and_parse_observation_data`）も移動

#### 4. `scripts/fetch_jma_tide_data.py` の縮退
- エントリーポイント（CLIの `main()`, `list_stations()`）のみに縮退
- `src/` からインポートして動作

#### 5. テストの追加
- `tests/unit/infrastructure/jma/test_stations.py` - 地点データの検証
- `tests/unit/infrastructure/jma/test_hourly_text_parser.py` - パーサーのテスト
- `tests/unit/infrastructure/jma/test_harmonic_analysis.py` - 調和解析のテスト

## 変更対象ファイル

### 新規作成
- `src/fishing_forecast_gcal/infrastructure/jma/__init__.py`
- `src/fishing_forecast_gcal/infrastructure/jma/stations.py`
- `src/fishing_forecast_gcal/infrastructure/jma/hourly_text_parser.py`
- `src/fishing_forecast_gcal/infrastructure/jma/harmonic_analysis.py`
- `tests/unit/infrastructure/jma/__init__.py`
- `tests/unit/infrastructure/jma/test_stations.py`
- `tests/unit/infrastructure/jma/test_hourly_text_parser.py`
- `tests/unit/infrastructure/jma/test_harmonic_analysis.py`

### 修正
- `scripts/fetch_jma_tide_data.py` - エントリーポイントのみに縮退

## 検証計画

1. 全テスト（pytest）が通過すること
2. ruff format / ruff check / pyright がパスすること
3. 全70地点のデータ整合性（地点コード・座標・基準面が公式一覧表と一致）
4. 既存の統合テスト（JMA推算値との差分検証）がパスすること

## 受け入れ条件

- [ ] `JMAStation` と全70地点データが `src/` 配下に存在
- [ ] FK(深浦)・HA(浜田) の誤り修正済み
- [ ] 全地点の緯度・経度が公式一覧表の値と一致
- [ ] `ref_level_tp_cm` が公式一覧表の値と一致
- [ ] `parse_jma_hourly_text` と `run_harmonic_analysis` が `src/` 配下にある
- [ ] 単体テストが追加されている
- [ ] `scripts/fetch_jma_tide_data.py` がエントリーポイントのみに縮退
- [ ] docstring に気象庁地点一覧表のURL参照がある
- [ ] ruff / pyright チェックがパスする
