# Issue #17: T-006 潮汐計算ライブラリアダプター

**ステータス**: ✅ Completed

## 概要

UTideライブラリをラップして潮汐予測を実行するアダプターを実装します。
このアダプターはInfrastructure層に配置され、Domain層からの依存を抽象化します。

## 責務

- UTideライブラリを使用して潮汐予測を実行
- 調和定数データの読み込み
- 予測結果の変換（DataFrameからリストへ）
- エラーハンドリング

## 実装方針

### 技術選定

- **潮汐計算ライブラリ**: UTide (v0.3.1以上)
- **調和定数データ**: 気象庁の実測データから調和解析で生成
- **時系列生成**: pandasで1時間刻みの時刻リストを生成
- **予測間隔**: 1時間刻み（満干潮検出に十分な精度）

### 実装アプローチ（2段階）

#### ステップ1: 調和定数の生成（開発時・1回のみ）

1. **実測データの取得**
   - 気象庁の潮汐観測データを取得（過去1年分推奨）
   - CSV形式またはAPIから取得

2. **調和解析の実行**
   - UTide の `solve()` で調和定数を算出
   - 主要な分潮（M2, S2, K1, O1など）を抽出

3. **結果の保存**
   - JSON形式で保存: `config/harmonics/{location_id}.json`
   - 地点情報とともにバージョン管理

#### ステップ2: アダプターの実装（このタスク）

1. **調和定数の読み込み**
   - JSONファイルから地点ごとの調和定数を読み込み
   - キャッシュして再利用

2. **潮汐予測の実行**
   - UTide の `reconstruct()` で予測実行
   - 1時間刻みで24時間分のデータポイントを生成

### MVP実装の制約

- **対応地点**: 初期実装では1地点のみサポート（東京湾想定）
- **調和定数**: 固定JSONファイルから読み込み（定期更新はフェーズ3で実装）
- **予測範囲**: 1日分の予測を実行（00:00～23:59）
- **時刻精度**: 1時間刻み（後続で10分刻みに改善可能）

### クラス設計

```python
class TideCalculationAdapter:
    """UTideライブラリを使用した潮汐計算アダプター
    
    Attributes:
        harmonics_dir: 調和定数ファイルのディレクトリパス
        _harmonics_cache: 読み込み済み調和定数のキャッシュ
    """
    
    def __init__(self, harmonics_dir: Path):
        """初期化
        
        Args:
            harmonics_dir: 調和定数ファイルのディレクトリ（config/harmonics/）
        """
    
    def calculate_tide(
        self,
        location: Location,
        target_date: date
    ) -> list[tuple[datetime, float]]:
        """指定地点・日付の潮汐を計算
        
        Args:
            location: 対象地点
            target_date: 対象日
            
        Returns:
            時刻と潮位のリスト（1時間刻み、24データポイント）
            例: [(datetime(2026,2,8,0,0), 120.5), ...]
            
        Raises:
            ValueError: 地点または日付が不正な場合
            FileNotFoundError: 調和定数ファイルが存在しない場合
            RuntimeError: 計算に失敗した場合
        """
```

## 変更予定のファイル

### 新規作成

- `src/fishing_forecast_gcal/infrastructure/adapters/tide_calculation_adapter.py`
  - TideCalculationAdapterクラス
  - 調和定数の読み込み
  - UTideによる潮汐予測

- `config/harmonics/` ディレクトリ
  - 地点ごとの調和定数ファイル（JSON形式）
  - 例: `tokyo_bay.json`, `sagami_bay.json`

- `scripts/generate_harmonics.py`（オプション）
  - 調和定数生成スクリプト
  - 実測データから調和解析を実行

- `tests/unit/infrastructure/adapters/test_tide_calculation_adapter.py`
  - ユニットテスト

### 既存ファイル（影響なし）

- `domain/models/tide.py` - 読み取りのみ
- `domain/models/location.py` - 読み取りのみ

## テスト要件

### ユニットテスト（必須）

1. **正常系**
   - 1日分の潮汐計算が正常に完了すること
   - 返り値が24個のデータポイントを含むこと
   - 各データポイントが有効な時刻と潮位を持つこと

2. **異常系**
   - 未サポート地点の場合にValueErrorを発生させること
   - 不正な日付の場合にValueErrorを発生させること

3. **境界値**
   - 過去の日付でも計算可能であること
   - 未来の日付でも計算可能であること（予測範囲内）

### 統合テスト（後続タスクで実施）

- 公式潮見表との差分検証（T-007で実施）
- 実際のリポジトリ実装との統合（T-007で実施）

## 実装手順

### Phase 1: 調和定数ファイルの生成（手動・1回のみ）

1. **実測データの取得**
   - 気象庁の潮汐観測データを取得（スクリプトまたは手動）
   - 過去1年分以上を推奨（精度向上のため）

2. **調和解析スクリプトの作成**
   - `scripts/generate_harmonics.py` を作成
   - UTide の `solve()` を使用
   - 結果を `config/harmonics/{location_id}.json` に保存

3. **検証**
   - 公式潮見表との差分確認
   - 許容差以内（目標: ±10cm）であることを確認

### Phase 2: アダプターの実装（このタスク）

1. **ディレクトリ構造の準備**
   - `config/harmonics/` ディレクトリを作成
   - サンプル調和定数ファイルを配置

2. **TideCalculationAdapterの実装**
   - JSONファイルの読み込み機能
   - UTide の `reconstruct()` による予測
   - エラーハンドリング

3. **ユニットテストの実装**
   - `tests/unit/infrastructure/adapters/test_tide_calculation_adapter.py`
   - 正常系・異常系・境界値のテスト

4. **品質チェック**
   - ruff format
   - ruff check
   - pyright
   - pytest（カバレッジ100%を目指す）

## 技術補足

### UTideライブラリの使用方法

#### ステップ1: 調和解析（開発時・1回のみ）

```python
import utide
import pandas as pd
import numpy as np

# 実測データの読み込み（例: 気象庁データ）
# time: datetime配列、height: 潮位の配列
observed_times = pd.date_range('2025-01-01', '2026-01-01', freq='H')
observed_heights = [...]  # 実測潮位データ

# 調和解析
coef = utide.solve(
    observed_times,
    observed_heights,
    lat=35.0,  # 地点の緯度
    verbose=False
)

# 結果の保存（JSON形式）
harmonics = {
    "location_id": "tokyo_bay",
    "latitude": 35.0,
    "longitude": 139.8,
    "constituents": coef.name.tolist(),  # 分潮名（M2, S2, K1, O1など）
    "amplitudes": coef.A.tolist(),       # 振幅
    "phases": coef.g.tolist(),           # 位相
    "analyzed_period": {
        "start": "2025-01-01",
        "end": "2026-01-01"
    }
}
```

#### ステップ2: 潮汐予測（アダプターで実行）

```python
import utide
import pandas as pd
import json

# 調和定数の読み込み
with open('config/harmonics/tokyo_bay.json', 'r') as f:
    harmonics = json.load(f)

# 予測時刻の生成（1時間刻み、24時間分）
predict_times = pd.date_range(
    start='2026-02-08 00:00',
    end='2026-02-08 23:00',
    freq='H',
    tz='Asia/Tokyo'
)

# UTideの係数オブジェクトを再構築
coef = utide.reconstruct(
    predict_times,
    coef={
        'name': harmonics['constituents'],
        'A': harmonics['amplitudes'],
        'g': harmonics['phases']
    }
)

# 潮位の取得
tide_heights = coef.h  # numpy配列

# 結果の変換
result = [
    (t.to_pydatetime(), float(h))
    for t, h in zip(predict_times, tide_heights)
]
```

### 調和定数データについて

- **分潮（constituents）**: M2（半日周潮）、S2（太陽半日周潮）、K1（日周潮）など
- **振幅（amplitude）**: 各分潮の振幅（cm単位）
- **位相（phase）**: 各分潮の位相角（度単位）

主要な分潮（最低限必要）:
- M2: 月の主太陰半日周潮（最も重要）
- S2: 太陽半日周潮
- K1: 日月合成日周潮
- O1: 月の主太陰日周潮

### データソース候補

1. **気象庁 潮位観測データ**
   - https://www.data.jma.go.jp/gmd/kaiyou/db/tide/genbo/index.php
   - 過去データのダウンロード可能（要確認）

2. **海上保安庁 海洋情報部**
   - 潮汐観測データの公開（要利用規約確認）

3. **バックアップ**: サンプルデータ生成
   - 理論値から簡易的な調和定数を生成

## 依存関係

- **前提タスク**: T-002（リポジトリインターフェース定義）✅ 完了
- **後続タスク**: T-007（TideDataRepository実装）でこのアダプターを使用

## 参照

- [実装計画書 T-006](../implementation_plan.md#t-006-潮汐計算ライブラリアダプター)
- [UTide公式ドキュメント](https://github.com/wesleybowman/UTide)
- [潮汐調和定数について](https://www.data.jma.go.jp/gmd/kaiyou/db/tide/knowledge/tide_knowledge.html)

---

## 実装結果・変更点

### 成果物

#### 新規作成ファイル

1. **`src/fishing_forecast_gcal/infrastructure/adapters/tide_calculation_adapter.py`** (292行)
   - `TideCalculationAdapter` クラス: pickle 形式の調和定数を読み込み、UTide `reconstruct()` で 24 時間分の潮位予測を実行
   - `generate_harmonics()` 関数: UTide `solve()` で観測データから調和定数を算出し pickle 保存
   - 調和定数キャッシュ、バリデーション、詳細なエラーハンドリング

2. **`scripts/fetch_jma_tide_data.py`** (555行)
   - 気象庁の潮汐観測データ（毎時潮位テキスト、137文字固定長）をダウンロード・パース
   - UTide 調和解析を実行し pickle ファイルを生成
   - 17 地点の JMA 観測地点をサポート（TK=東京, MR=布良, etc.）
   - CLI: `--station`, `--year`, `--months`, `--list-stations`
   - データソース: https://www.data.jma.go.jp/kaiyou/db/tide/genbo/index.php
   - 参考: [JMAtide](https://github.com/hydrocoast/JMAtide) (MATLAB, MIT License)

3. **`tests/unit/infrastructure/adapters/test_tide_calculation_adapter.py`** (413行)
   - 22 テストケース（Init: 3, CalculateTide: 10, Cache: 2, Validation: 2, Harmonics: 5）

4. **`config/harmonics/README.md`** - 調和定数ディレクトリの説明と使い方

#### 変更ファイル

- **`pyproject.toml`** - UTide v0.3.1 依存関係を追加
- **`.gitignore`** - `config/harmonics/*.pkl` を除外に追加

#### 削除ファイル

- **`config/harmonics/tokyo_bay.json`** - AI が捏造した調和定数データ（実際の JMA 値と不一致）を削除

### 計画からの変更点

| 項目 | 当初計画 | 実装結果 | 理由 |
|------|---------|---------|------|
| 調和定数フォーマット | JSON | pickle (.pkl) | UTide の coef オブジェクト（Bunch 型）を完全に保存するため。JSON では `aux` フィールド等の内部状態が欠落する |
| データ取得方法 | 手動/未定 | `scripts/fetch_jma_tide_data.py` | JMA の URL パターンを JMAtide リポジトリから特定。自動化可能 |
| スクリプト名 | `generate_harmonics.py` | `fetch_jma_tide_data.py` | データ取得→解析→保存の一連の処理を 1 スクリプトに統合 |
| 対応地点数 | 1 地点（東京湾） | 17 地点 | JMA 主要観測地点を網羅 |

### 品質チェック結果

| 種別 | 結果 |
|------|------|
| ruff format | ✅ Pass |
| ruff check | ✅ Pass |
| pyright (strict) | ✅ 0 errors |
| pytest | ✅ 127 passed |
