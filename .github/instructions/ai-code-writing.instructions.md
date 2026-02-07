---
applyTo: "**/*.py,**/*.java,**/*.js,**/*.ts,**/*.tsx,**/*.jsx"
---

# AIコード執筆ガイドライン

## 概要

このファイルは、AIがコードを執筆する際の指示を定義します。一貫性のある高品質なコードを維持するための必須要件を規定します。

**関連ガイドライン**:
- [ai-code-examples-reference.instructions.md](./ai-code-examples-reference.instructions.md) - 実践的なコード例集
- [ai-advanced-patterns.instructions.md](./ai-advanced-patterns.instructions.md) - 高度な型定義とデザインパターン
- [ai-project-structure-core.instructions.md](./ai-project-structure-core.instructions.md) - プロジェクト構造保護ルール

---

## 最重要ルール (MUST)

### 1. 言語使用の原則

#### コード要素: **必ず英語**
- 関数名、クラス名、変数名、モジュール名
- 理由: 国際標準、AIツールとの親和性、将来的な国際化対応

#### Docstring: **英語 + 日本語併記**
- **1行目の概要**: 英語でピリオド `.` で終わる（Ruff互換のため必須）
- **詳細説明**: 英語で記述し、必要に応じて日本語を括弧書きで補足
- **Args/Returns**: 英語で記述し、重要な部分は日本語を併記

**Ruff互換の重要性**: 日本語の句点 `。` で終わるとD400ルールエラーになる

```python
def calculate_defect_rate(total_count: int, defect_count: int) -> float:
    """Calculate the defect rate from production counts.
    
    全体の生産数と不良品数から不良品率(%)を計算します。
    
    Args:
        total_count (int): Total number of products.
                          (全生産数)
        defect_count (int): Number of defective products.
                           (不良品数)
    
    Returns:
        float: Defect rate as percentage (0.0 to 100.0).
              (不良品率(パーセント))
    """
```

#### その他の言語選択

| 要素 | 言語 | 理由 |
|------|------|------|
| 型ヒント | 英語 | Python標準 |
| インラインコメント | 日本語可 | ドメイン知識の正確な伝達 |
| 定数の説明 | 日本語可 | 設定値の意味を明確化 |
| エラーメッセージ | 日本語 | エンドユーザー向け |
| ログメッセージ | 日本語 | 運用チーム向け |

---

### 2. Google Style Docstring 必須実装

すべてのクラス、関数、メソッドに必ず実装してください。

#### 必要要件

1. **概要(Summary)**: 1行で目的を簡潔に説明。ピリオドで終わる
2. **Args**: すべての引数（形式: `引数名 (型): 説明`）
3. **Returns**: 戻り値の型と意味（戻り値がない場合は省略可）
4. **Raises**: 発生する可能性のある例外
5. **Examples**: 使用例（推奨）

**簡潔な例:**

```python
def validate_input_data(data: pd.DataFrame) -> bool:
    """Validate that input data meets required schema.
    
    Args:
        data (pd.DataFrame): Input data to validate.
    
    Returns:
        bool: True if data is valid, False otherwise.
    """
    required_columns = ["timestamp", "value", "label"]
    return all(col in data.columns for col in required_columns)
```

---

### 3. 型ヒント必須実装

すべての関数・メソッドの引数と戻り値に型ヒントを必ず記述してください。

#### 基本的な型

```python
from typing import List, Dict, Optional

def process_data(
    values: List[int],
    config: Dict[str, Any],
    threshold: Optional[float] = None
) -> Dict[str, float]:
    """Process data with configuration."""
    pass
```

#### よく使う型

- `List[int]`, `Dict[str, Any]`, `Set[str]`, `Tuple[float, float]`
- `Optional[Type]`: None になる可能性がある場合
- `Union[Type1, Type2]`: 複数の型が考えられる場合
- `Iterator[Type]`, `Generator[YieldType, SendType, ReturnType]`: イテレータ・ジェネレータ

---

### 4. ファイル冒頭コメント必須実装

すべてのPythonファイルの冒頭にモジュールdocstringを必ず記述してください。

#### 必要な情報

- ファイルの役割と機能
- 主要なクラスや関数の概要
- プロジェクト内での位置づけ
- 使用方法の簡単な例

#### 重要な注意点

- モジュールdocstringは必ずファイルの最初に配置（shebang/エンコーディング宣言の後）
- 三重引用符(`"""`)で囲む
- 1行目は簡潔な概要で、ピリオドで終わる
- 空行を挟んで詳細説明を記述
- Main Components セクションで主要なコンポーネントを箇条書き
- Project Context セクションでプロジェクト内での役割を説明
- Example セクションで実際の使用例を含める

#### 基本例

```python
"""Data preprocessing and feature engineering module.

This module provides classes and functions for loading, validating, and
transforming raw factory data into features suitable for machine learning.

Main Components:
    - DataLoader: Loads data from CSV files
    - FeatureTransformer: Transforms raw data into ML-ready features

Project Context:
    Part of the factory-ml-offline-system training pipeline.

Example:
    >>> from preprocessor import DataLoader
    >>> loader = DataLoader("config/schema.json")
    >>> data = loader.load_csv("data/input/raw_data.csv")
"""
```

詳細な実装例については [ai-code-examples-reference.instructions.md](./ai-code-examples-reference.instructions.md) のファイル冒頭コメント詳細例を参照

---

## 推奨ルール (SHOULD)

### AI協調のベストプラクティス

#### 命名規則

```python
# Good: AIが目的を理解しやすい
def calculate_average(values: List[float]) -> float:
def validate_input_data(data: pd.DataFrame) -> bool:

defect_count: int = 25
temperature_celsius: float = 45.5

class DataValidator:
class ModelTrainer:

# Avoid: 意味が不明確
def average(values: List[float]) -> float:
x: int = 25
class Helper:
```

#### 説明的なコメント

```python
def detect_anomalies(data: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
    """Detect anomalies using z-score method."""
    
    # Calculate z-score for each data point
    # Z-score = (value - mean) / std
    mean = data['value'].mean()
    std = data['value'].std()
    data['z_score'] = (data['value'] - mean) / std
    
    # Flag values exceeding threshold as anomalies
    # 閾値を超える値を異常値としてフラグ付け
    data['is_anomaly'] = data['z_score'].abs() > threshold
    
    return data
```

### 定数には説明コメント

```python
# Maximum number of retries for API calls before giving up
MAX_RETRIES: int = 3

# Threshold for anomaly detection (z-score)
# Values with z-score above this threshold are flagged as anomalies
ANOMALY_THRESHOLD: float = 3.0

# Column names for input data schema
REQUIRED_COLUMNS: List[str] = [
    "timestamp",      # Data collection timestamp (ISO 8601 format)
    "temperature",    # Temperature in Celsius
    "pressure",       # Pressure in kPa
    "defect_flag",    # Binary flag: 1=defect, 0=normal
]
```

### エラーメッセージは日本語で具体的に

```python
def load_csv_file(file_path: str) -> pd.DataFrame:
    """Load data from CSV file."""
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    
    try:
        data = pd.read_csv(file_path)
    except pd.errors.ParserError as e:
        raise ValueError(
            f"CSVファイルの形式が不正です: {file_path}\n"
            f"詳細: {str(e)}"
        )
    
    if data.empty:
        raise ValueError(f"ファイルにデータが含まれていません: {file_path}")
    
    return data
```

### プライベート関数にも簡潔なdocstring

```python
def _validate_schema(data: pd.DataFrame) -> bool:
    """Validate that input data meets required schema.
    
    Args:
        data (pd.DataFrame): Input data to validate.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    required_columns = ["timestamp", "value"]
    return all(col in data.columns for col in required_columns)
```

---

## 品質チェックリスト

### ドキュメンテーション
- [ ] ファイル冒頭にモジュールdocstring
- [ ] すべての公開クラス・関数にGoogle Style Docstring
- [ ] Docstring 1行目は英語でピリオド終わり
- [ ] Args, Returns, Raises セクション完備

### 型ヒント
- [ ] すべての引数と戻り値に型ヒント
- [ ] Optional, Union を適切に使用
- [ ] コレクション型の内部型も明示 (`List[int]`)

### コード品質
- [ ] 関数は単一責任
- [ ] 変数名・関数名が説明的
- [ ] マジックナンバーを避け定数使用
- [ ] エラーメッセージが明確で具体的

### テスト
- [ ] ユニットテストが実装されている（該当する場合）
- [ ] エッジケースのテストが含まれている
- [ ] 例外処理のテストが含まれている
- [ ] テスト名が明確で意図が理解できる

### パフォーマンスとセキュリティ
- [ ] 不要なループや計算が含まれていない
- [ ] ファイルやリソースが適切にクローズされている
- [ ] 機密情報（パスワード、APIキーなど）がハードコードされていない
- [ ] SQL インジェクションなどのセキュリティリスクがない
- [ ] 入力値の検証が適切に行われている

### プロジェクト固有
- [ ] 設定ファイル (`config/app_settings.json`) を使用
- [ ] ログ出力が適切に実装
- [ ] 既存のユーティリティ関数を再利用

---

## 参考資料

詳細な例と高度なパターンについては以下を参照:
- [ai-code-examples-reference.instructions.md](./ai-code-examples-reference.instructions.md) - 実践的なコード例集
- [ai-advanced-patterns.instructions.md](./ai-advanced-patterns.instructions.md) - 高度な型定義とデザインパターン
