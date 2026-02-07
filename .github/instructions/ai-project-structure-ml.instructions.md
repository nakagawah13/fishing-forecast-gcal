---
applyTo: "**"
---

# AIプロジェクト構造保護ガイドライン（ML/AI特有）

## 概要

このファイルは、ML/AIプロジェクト特有のディレクトリ構造保護ルールを定義します。機械学習・AI開発における実験管理、モデル成果物、データパイプラインの適切な配置を規定します。

## 関連ガイドライン

- [ai-project-structure-core.instructions.md](./ai-project-structure-core.instructions.md): コア・必須ルール
- [ai-project-structure-maintenance.instructions.md](./ai-project-structure-maintenance.instructions.md): 保守・修正プロセス

## ML/AIプロジェクト特有の構造保護ルール

### 1. 実験管理の一元化（MUST）

ML/AIプロジェクトでは実験管理を**一箇所に集約**すること。

```
✅ 推奨パターン
experiments/
  exp_001_baseline/
    config.yaml
    results.json
    model.onnx
  exp_002_feature_engineering/
    config.yaml
    results.json
    model.onnx

❌ 禁止パターン
src/
  experiments/          # 分散している
models/
  experiments/          # 同じ目的で複数存在
python-trainer/
  my_experiments/       # 命名も不統一
```

**ルール**:
- 実験結果は `experiments/` または `mlruns/` に統一
- 実験IDは連番または日付ベースで統一
- 各実験に設定ファイルと結果ファイルを必ず含める

### 2. モデル成果物の分離（MUST）

学習済みモデルと学習コードは**明確に分離**すること。

```
✅ 推奨パターン
models/
  current/              # 現在使用中のモデル
    model_v1.2.3.onnx
  archive/              # 過去のモデル
    model_v1.2.2.onnx
    model_v1.2.1.onnx
python-trainer/
  src/
    trainer/            # 学習コード
      model_trainer.py

❌ 禁止パターン
python-trainer/
  models/               # 学習コードとモデルが混在
    model_v1.onnx
  src/
    model_trainer.py
```

**ルール**:
- モデルファイル (.onnx, .pkl, .h5等) は `models/` に配置
- バージョン管理を明確にする（`current/`, `archive/`）
- 学習コードは `python-trainer/src/` に配置
- モデルとコードの依存関係をドキュメント化

### 3. データパイプラインの統一（MUST）

データ処理パイプラインは**一貫した構造**を維持すること。

```
✅ 推奨パターン
data/
  input/                # 生データ（読み取り専用）
    raw_sensor_data.csv
  output/               # 処理済みデータ
    processed_data.csv
    predictions.csv
  README.md             # データ仕様

❌ 禁止パターン
data/
  input/
  output/
src/
  data/                 # dataディレクトリと重複
python-trainer/
  dataset/              # さらに別のデータディレクトリ
```

**ルール**:
- 入力データは `data/input/` に統一
- 出力データは `data/output/` に統一
- 中間データが必要な場合は `data/intermediate/` を追加
- データディレクトリは複数作成しない

### 4. 設定ファイルの一元管理（MUST）

ML/AIプロジェクトの設定は**一箇所に集約**すること。

```
✅ 推奨パターン
config/
  app_settings.json     # アプリケーション設定
  schema.json           # データスキーマ
  model_config.yaml     # モデル設定

❌ 禁止パターン
config/
  app_settings.json
python-trainer/
  config.yaml           # 設定が分散
java-app/
  settings.json         # さらに分散
```

**ルール**:
- すべての設定ファイルは `config/` に配置
- 技術スタック間で設定を共有する場合は同一ファイルを参照
- 環境別設定は `config/dev/`, `config/prod/` で管理

## ML/AIプロジェクト特有チェックリスト

ML/AIプロジェクトの場合、以下を確認:

- [ ] 実験管理は一元化されているか（`experiments/` または `mlruns/`）
- [ ] モデルファイルは `models/` に配置されているか
- [ ] 学習コードとモデル成果物は分離されているか
- [ ] データディレクトリは統一されているか（`data/input/`, `data/output/`）
- [ ] 設定ファイルは `config/` に集約されているか

## エラーパターン: ML/AI特有構造の無視

**症状**:
- モデルファイルと学習コードが混在
- 実験管理が分散
- データディレクトリが複数存在

**対処法**:
1. ML/AIプロジェクト特有ルールを確認
2. 実験管理は一元化
3. モデル成果物は分離

**予防策**: ML/AIプロジェクト特有の構造保護ルールを遵守
