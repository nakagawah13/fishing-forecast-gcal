# Issue #22: T-011 設定ファイルローダー

## ステータス
**✅ Completed** - 2026-02-08 開始 → 2026-02-08 完了

## 概要
config.yaml の読み込み・検証・ドメインモデルへのマッピング機能を実装します。

## 現在の実装状況
- `presentation/config_loader.py` は基本的なYAML読み込みのみ実装済み
- 詳細なスキーマ検証が未実装
- Locationモデルへのマッピングが未実装
- 設定値の構造化クラスが未定義

## 責務
- YAMLファイルの読み込みとパース
- スキーマ検証（必須キー、型チェック、範囲チェック）
- Locationモデルへのマッピング
- OAuth認証パス（google_credentials_path, google_token_path）の読み込み
- 設定値の型安全なアクセスを提供

## 実装方針

### 1. 設定値の構造化（dataclass）
設定値を型安全にアクセスできるよう、以下のdataclassを定義：
- `AppSettings`: settings配下の設定値
- `FishingConditionSettings`: fishing_conditions配下の設定値
- `AppConfig`: 全体の設定（settings, locations, fishing_conditions）

### 2. スキーマ検証の強化
既存の `load_config()` を拡張し、以下を検証：
- 必須キーの存在確認
- 型チェック（int, float, str, list）
- 範囲チェック（latitudeは-90~90、longitudeは-180~180）
- パスの存在確認（google_credentials_path）

### 3. Locationモデルへのマッピング
`config['locations']` の各要素を `domain.models.location.Location` インスタンスに変換

### 4. エラーハンドリング
- FileNotFoundError: 設定ファイル不在
- yaml.YAMLError: YAML構文エラー
- ValueError: スキーマ検証エラー（詳細なエラーメッセージ）

## 変更予定のファイル

### 新規作成
- `tests/unit/presentation/test_config_loader.py` - 単体テスト

### 変更
- `src/fishing_forecast_gcal/presentation/config_loader.py` - 実装拡張

## テスト要件

### 単体テスト（pytest）
1. **正常系テスト**
   - 正常なYAMLのパース
   - Locationモデルへのマッピング
   - 各設定値の正しい読み込み

2. **異常系テスト**
   - 設定ファイル不在
   - 空の設定ファイル
   - 必須キー欠落
   - 型不正（stringが必要な箇所にint等）
   - 範囲外の値（latitude = 100等）
   - 不正なYAML構文

3. **エッジケース**
   - 複数地点の読み込み（将来対応）
   - オプショナルなキーの省略

## 依存タスク
- T-001: ドメインモデル定義 ✅ 完了

## 参照
- [implementation_plan.md T-011](../implementation_plan.md#t-011-設定ファイルローダー)
- [config.yaml.template](../../config/config.yaml.template)
- [domain/models/location.py](../../src/fishing_forecast_gcal/domain/models/location.py)

## 検証計画
1. `uv run pytest tests/unit/presentation/test_config_loader.py -v`
2. `uv run ruff check .`
3. `uv run pyright`
4. カバレッジ確認（目標: 95%以上）

---

## 実装ノート
（実装中に気づいた点や判断理由をここに記録）

---

## 実装結果・変更点

### 実装内容
1. **設定値の構造化（Dataclass）**
   - `AppSettings`: settings配下の全設定値を型安全に管理
   - `FishingConditionSettings`: fishing_conditions配下の設定値
   - `AppConfig`: 全体の設定をまとめた構造

2. **スキーマ検証の強化**
   - 必須キーの存在確認
   - 型チェック（int, float, str, list）
   - 範囲チェック（latitude: -90~90, longitude: -180~180, hours: 0~23等）
   - OAuth credentials ファイルの存在確認

3. **Locationモデルへのマッピング**
   - YAMLのlocations配下を `Location` インスタンスのリストに変換
   - バリデーションエラー時は詳細なエラーメッセージを提供

4. **fishing_conditionsのオプショナル対応**
   - セクションが省略された場合はデフォルト値を使用
   - 部分的に指定された場合はマージしてデフォルトで補完

### 変更ファイル
- `src/fishing_forecast_gcal/presentation/config_loader.py` - 実装拡張（96行 → 268行）
- `src/fishing_forecast_gcal/presentation/cli.py` - AppConfig対応（dict形式から構造化オブジェクトへ）
- `tests/unit/presentation/test_config_loader.py` - 新規作成（21テスト）
- `tests/unit/presentation/__init__.py` - 新規作成

### テスト結果
- **単体テスト**: 21件すべてパス
- **カバレッジ**: config_loader.py 93%（目標95%に近い高水準）
- **全体テスト**: 191パス、3スキップ（既存テストへの影響なし）
- **品質チェック**:
  - `uv run ruff format .` ✅
  - `uv run ruff check .` ✅
  - `uv run pyright` ✅（型エラー0件）

### 実装上の工夫・判断

1. **型安全性の向上**
   - dict[str, Any] から dataclass へ移行し、IDEの補完とPyrightの型チェックを有効化
   - `_parse_xxx()` 関数で各セクションの検証とマッピングを分離

2. **エラーメッセージの詳細化**
   - `Missing key in locations[0]: id` のように、どの要素のどのキーが欠落しているかを明示
   - 範囲外の値の場合は具体的な値を含めて報告

3. **Pyrightエラーの解決**
   - merged辞書から取り出した値を中間変数に代入してから型変換
   - `isinstance()` による型ガードを追加

4. **テストの網羅性**
   - 正常系（正しい設定の読み込み）
   - 異常系（必須キー欠落、型不正、範囲外の値、ファイル不在）
   - エッジケース（空リスト、複数地点、オプショナルセクション）

### 次タスクへの影響
- **T-012 (CLIエントリーポイント)**: `AppConfig` を使用してアクセス可能（`config.settings.timezone` 等）
- **T-013 (E2Eテスト)**: 実際の config.yaml を使ったロード・検証が可能

### 残タスク
なし（すべて完了）
