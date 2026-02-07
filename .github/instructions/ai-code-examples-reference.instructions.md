---
applyTo: "**/*.py,**/*.java,**/*.js,**/*.ts,**/*.tsx,**/*.jsx"
---

# AI Code Examples Reference

このファイルは、[ai-code-writing.instructions.md](./ai-code-writing.instructions.md) の補足資料として、実践的なコード例とベストプラクティスを提供します。

**高度な型定義やデザインパターンについては**: [ai-advanced-patterns.instructions.md](./ai-advanced-patterns.instructions.md)

---

## 目次

1. [Google Style Docstring 実践例](#google-style-docstring-実践例)
2. [ファイル冒頭コメント詳細例](#ファイル冒頭コメント詳細例)
3. [工場データ処理の実例](#工場データ処理の実例)
4. [エラーハンドリングのベストプラクティス](#エラーハンドリングのベストプラクティス)
5. [定数とEnum定義](#定数とenum定義)
6. [ログ出力パターン](#ログ出力パターン)

---

## Google Style Docstring 実践例

### 標準的な関数の例

```python
def calculate_discount(price: float, discount_rate: float, tax_rate: float = 0.1) -> float:
    """Calculate the final price after applying discount and tax.
    
    This function applies a discount rate to the original price and then
    adds the tax rate to compute the final price. The result is rounded
    to two decimal places.
    
    Args:
        price (float): The original price of the product. Must be positive.
        discount_rate (float): The discount rate to apply. Must be between 0.0 and 1.0.
        tax_rate (float, optional): The tax rate to apply. Defaults to 0.1 (10%).
    
    Returns:
        float: The final price after discount and tax, rounded to 2 decimal places.
    
    Raises:
        ValueError: If price is negative or discount_rate is not in range [0.0, 1.0].
    
    Examples:
        >>> calculate_discount(1000, 0.2)
        880.0
        >>> calculate_discount(1000, 0.2, 0.08)
        864.0
    """
    if price < 0:
        raise ValueError("Price must be positive")
    if not 0.0 <= discount_rate <= 1.0:
        raise ValueError("Discount rate must be between 0.0 and 1.0")
    
    discounted_price = price * (1 - discount_rate)
    final_price = discounted_price * (1 + tax_rate)
    return round(final_price, 2)
```

### クラスの詳細例

```python
class DataProcessor:
    """Process and transform data for machine learning.
    
    This class loads data from CSV files and performs preprocessing operations
    including missing value handling, normalization, and feature engineering.
    
    Attributes:
        file_path (str): Path to the CSV file to be processed.
        data (pd.DataFrame): The loaded DataFrame.
        scaler (StandardScaler): Scaler for data normalization.
    
    Examples:
        >>> processor = DataProcessor("data/input.csv")
        >>> processor.load_data()
        >>> processor.handle_missing_values()
        >>> normalized_data = processor.normalize()
    """
    
    def __init__(self, file_path: str) -> None:
        """Initialize the DataProcessor.
        
        Args:
            file_path (str): Path to the CSV file to be processed.
        
        Raises:
            FileNotFoundError: If the specified file does not exist.
        """
        self.file_path = file_path
        self.data = None
        self.scaler = StandardScaler()
    
    def load_data(self) -> pd.DataFrame:
        """Load data from the CSV file.
        
        Returns:
            pd.DataFrame: The loaded DataFrame.
        
        Raises:
            FileNotFoundError: If the file is not found.
            pd.errors.ParserError: If CSV parsing fails.
        """
        try:
            self.data = pd.read_csv(self.file_path)
            return self.data
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.file_path}")
```

### ジェネレータの例

```python
def batch_generator(data: List[Any], batch_size: int = 32) -> Generator[List[Any], None, None]:
    """Generate data in batches for memory-efficient processing.
    
    Split large datasets into smaller batches to enable memory-efficient
    processing of data that might not fit in memory all at once.
    
    Args:
        data (List[Any]): The list of data to be processed.
        batch_size (int, optional): The size of each batch. Defaults to 32.
    
    Yields:
        List[Any]: A list containing batch_size elements. The last batch may
            contain fewer elements if the data length is not evenly divisible.
    
    Examples:
        >>> data = list(range(100))
        >>> for batch in batch_generator(data, batch_size=10):
        ...     process_batch(batch)
    """
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]
```

### 英語+日本語併記の工場データ処理例

```python
class ProductionLineMonitor:
    """Monitor production line status and detect anomalies.
    
    生産ラインの状態を監視し、異常を検出するクラスです。
    リアルタイムデータを受け取り、統計的手法で異常値を判定します。
    
    Attributes:
        line_id (str): Production line identifier.
                      (生産ライン識別子)
        threshold (float): Anomaly detection threshold (z-score).
                          (異常検知閾値(zスコア))
        history (List[float]): Historical data for baseline calculation.
                              (ベースライン計算用の履歴データ)
    
    Examples:
        >>> monitor = ProductionLineMonitor("LINE-A", threshold=3.0)
        >>> monitor.add_measurement(25.5)
        >>> is_anomaly = monitor.check_anomaly(45.2)
        >>> print(is_anomaly)
        True
    """
    
    def __init__(self, line_id: str, threshold: float = 3.0) -> None:
        """Initialize the production line monitor.
        
        Args:
            line_id (str): Production line identifier.
                          (生産ライン識別子)
            threshold (float, optional): Anomaly detection threshold.
                                        Defaults to 3.0.
                                        (異常検知閾値。デフォルトは3.0)
        """
        self.line_id = line_id
        self.threshold = threshold
        self.history: List[float] = []
```

---

## 工場データ処理の実例

### 生産データのバリデーション

```python
import pandas as pd
from typing import List, Dict, Any

def validate_production_data(data: pd.DataFrame) -> None:
    """Validate production data schema and values.
    
    生産データのスキーマと値の範囲を検証します。
    データに問題がある場合は詳細なエラーメッセージを含む例外を発生させます。
    
    Args:
        data (pd.DataFrame): Production data to validate.
                            (検証対象の生産データ)
    
    Raises:
        ValueError: If validation fails with detailed error message.
                   (検証失敗時に詳細なエラーメッセージと共に発生)
    """
    required_columns = ['timestamp', 'temperature', 'pressure', 'defect_flag']
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        raise ValueError(
            f"必須カラムが不足しています: {', '.join(missing_columns)}\n"
            f"必要なカラム: {', '.join(required_columns)}"
        )
    
    if data['temperature'].min() < -50 or data['temperature'].max() > 150:
        raise ValueError(
            "温度の値が有効範囲(-50℃〜150℃)を超えています\n"
            f"最小値: {data['temperature'].min()}℃\n"
            f"最大値: {data['temperature'].max()}℃"
        )
    
    if not data['defect_flag'].isin([0, 1]).all():
        raise ValueError(
            "defect_flagは0または1である必要があります"
        )
```

### 不良品率の計算

```python
def calculate_defect_rate(total_count: int, defect_count: int) -> float:
    """Calculate the defect rate from production counts.
    
    全体の生産数と不良品数から不良品率(%)を計算します。
    結果は小数点以下2桁に丸められます。
    
    Args:
        total_count (int): Total number of products. Must be positive.
                          (全生産数。正の整数である必要があります)
        defect_count (int): Number of defective products. 
                           Must be between 0 and total_count.
                           (不良品数。0以上でtotal_count以下)
    
    Returns:
        float: Defect rate as percentage (0.0 to 100.0).
              (不良品率(パーセント)。0.0から100.0の範囲)
    
    Raises:
        ValueError: If total_count is not positive or defect_count is invalid.
                   (total_countが正でない、またはdefect_countが不正な場合)
    
    Examples:
        >>> calculate_defect_rate(1000, 25)
        2.5
        >>> calculate_defect_rate(500, 0)
        0.0
    """
    if total_count <= 0:
        raise ValueError("total_countは正の整数である必要があります")
    if defect_count < 0 or defect_count > total_count:
        raise ValueError("defect_countは0以上、total_count以下である必要があります")
    
    rate = (defect_count / total_count) * 100
    return round(rate, 2)
```

### 異常検知クラス

```python
import numpy as np
from typing import List

class ProductionLineMonitor:
    """Monitor production line status and detect anomalies.
    
    生産ラインの状態を監視し、異常を検出するクラスです。
    リアルタイムデータを受け取り、統計的手法で異常値を判定します。
    
    Attributes:
        line_id (str): Production line identifier.
                      (生産ライン識別子)
        threshold (float): Anomaly detection threshold (z-score).
                          (異常検知閾値(zスコア))
        history (List[float]): Historical data for baseline calculation.
                              (ベースライン計算用の履歴データ)
    
    Examples:
        >>> monitor = ProductionLineMonitor("LINE-A", threshold=3.0)
        >>> monitor.add_measurement(25.5)
        >>> is_anomaly = monitor.check_anomaly(45.2)
        >>> print(is_anomaly)
        True
    """
    
    def __init__(self, line_id: str, threshold: float = 3.0) -> None:
        """Initialize the production line monitor.
        
        Args:
            line_id (str): Production line identifier.
                          (生産ライン識別子)
            threshold (float, optional): Anomaly detection threshold.
                                        Defaults to 3.0.
                                        (異常検知閾値。デフォルトは3.0)
        """
        self.line_id = line_id
        self.threshold = threshold
        self.history: List[float] = []
    
    def add_measurement(self, value: float) -> None:
        """Add a measurement to the history.
        
        Args:
            value (float): Measurement value to add.
                          (追加する測定値)
        """
        self.history.append(value)
    
    def check_anomaly(self, value: float) -> bool:
        """Check if a value is anomalous based on historical data.
        
        Args:
            value (float): Value to check for anomaly.
                          (異常判定する値)
        
        Returns:
            bool: True if anomalous, False otherwise.
                 (異常ならTrue、そうでなければFalse)
        """
        if len(self.history) < 10:
            return False  # 履歴データが不足している場合は判定しない
        
        mean = np.mean(self.history)
        std = np.std(self.history)
        
        if std == 0:
            return False
        
        z_score = abs((value - mean) / std)
        return z_score > self.threshold
```

---

## ファイル冒頭コメント詳細例

モジュールdocstringには以下を含めてください:
- **1行の簡潔な概要**: ピリオド `.` で終わる（Ruff互換のため必須）
- **詳細な機能説明**: 複数段落で具体的に説明
- **Main Components**: 主要なクラス・関数を箇条書き
- **Project Context**: プロジェクト内での位置づけと役割
- **Example**: 実際の使用例（import文と基本的な使い方）

### データ処理モジュール

```python
"""Data preprocessing and feature engineering module.

This module provides classes and functions for loading, validating, and
transforming raw factory data into features suitable for machine learning.
It handles missing values, applies normalization, and generates time-series
features for production line monitoring.

Main Components:
    - DataLoader: Loads data from CSV files with schema validation
    - FeatureTransformer: Transforms raw data into ML-ready features
    - ValidationError: Custom exception for data validation errors

Project Context:
    Part of the factory-ml-offline-system training pipeline. This module
    is used by the model trainer to prepare data before model training.

Example:
    >>> from preprocessor import DataLoader, FeatureTransformer
    >>> loader = DataLoader("config/schema.json")
    >>> data = loader.load_csv("data/input/raw_data.csv")
    >>> transformer = FeatureTransformer()
    >>> features = transformer.transform(data)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
```

### 機械学習モデルトレーナー

```python
"""Machine learning model training module.

This module implements the complete training pipeline for factory production
prediction models. It handles data preprocessing, model training with
hyperparameter optimization, evaluation, and ONNX export for deployment.

Main Components:
    - ModelTrainer: Main training orchestrator with cross-validation
    - train_model(): Trains a single model with given hyperparameters
    - evaluate_model(): Evaluates model performance on test data
    - export_to_onnx(): Converts trained model to ONNX format

Project Context:
    Core component of the training pipeline. Called by main.py when
    training mode is selected. Outputs trained models to models/current/
    and generates training reports in data/output/reports/.

Example:
    >>> from model_trainer import ModelTrainer
    >>> trainer = ModelTrainer(config_path="config/app_settings.json")
    >>> metrics = trainer.train(data_path="data/input/training_data.csv")
    >>> print(f"Model accuracy: {metrics['accuracy']:.2f}")
"""

import logging
from pathlib import Path
import lightgbm as lgb
```

### ユーティリティモジュール

```python
"""Utility functions for configuration and date parsing.

This module provides helper functions used across the application for
common tasks like loading configuration files and parsing date strings
in various formats.

Main Components:
    - load_config(): Loads and validates JSON configuration files
    - parse_date(): Parses date strings with multiple format support
    - ConfigError: Custom exception for configuration errors

Project Context:
    Shared utility module used by both training and inference components.
    Provides consistent configuration handling across the system.

Example:
    >>> from util import load_config, parse_date
    >>> config = load_config("config/app_settings.json")
    >>> date = parse_date("2025-12-06", format="yyyy-MM-dd")
"""

import json
from datetime import datetime
from typing import Any, Dict
```

---

## エラーハンドリングのベストプラクティス

### 包括的なバリデーションエラー

```python
def validate_production_data(data: pd.DataFrame) -> None:
    """Validate production data schema and values.
    
    Args:
        data (pd.DataFrame): Production data to validate.
    
    Raises:
        ValueError: If validation fails.
    """
    required_columns = ['timestamp', 'temperature', 'pressure', 'defect_flag']
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        raise ValueError(
            f"必須カラムが不足しています: {', '.join(missing_columns)}\n"
            f"必要なカラム: {', '.join(required_columns)}"
        )
    
    if data['temperature'].min() < -50 or data['temperature'].max() > 150:
        raise ValueError(
            "温度の値が有効範囲(-50℃〜150℃)を超えています\n"
            f"最小値: {data['temperature'].min()}℃\n"
            f"最大値: {data['temperature'].max()}℃"
        )
    
    if not data['defect_flag'].isin([0, 1]).all():
        raise ValueError(
            "defect_flagは0または1である必要があります"
        )
```

---

## ログ出力パターン

### モデル訓練のログ例

```python
import logging

logger = logging.getLogger(__name__)

def train_model(data_path: str, output_path: str) -> Dict[str, float]:
    """Train machine learning model.
    
    Args:
        data_path (str): Path to training data.
        output_path (str): Path to save trained model.
    
    Returns:
        Dict[str, float]: Training metrics.
    """
    logger.info(f"モデル訓練を開始します: {data_path}")
    
    try:
        data = load_data(data_path)
        logger.info(f"データ読み込み完了: {len(data)} 件")
        
        model = train_lightgbm(data)
        logger.info("モデル訓練完了")
        
        metrics = evaluate_model(model, data)
        logger.info(
            f"評価結果 - Accuracy: {metrics['accuracy']:.3f}, "
            f"Precision: {metrics['precision']:.3f}, "
            f"Recall: {metrics['recall']:.3f}"
        )
        
        save_model(model, output_path)
        logger.info(f"モデルを保存しました: {output_path}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"モデル訓練中にエラーが発生しました: {str(e)}")
        raise
```

---

## 定数とEnum定義

### 設定クラスでの定数定義

```python
class Config:
    """Application configuration constants.
    
    This class centralizes all configuration constants used throughout
    the application. Values should be modified here rather than hardcoded
    in individual modules.
    """
    
    # Data paths
    INPUT_DATA_DIR: str = "data/input"          # Directory for raw input data
    OUTPUT_DATA_DIR: str = "data/output"        # Directory for processed output
    MODEL_DIR: str = "models/current"           # Directory for trained models
    ARCHIVE_DIR: str = "models/archive"         # Directory for archived models
    
    # Model training parameters
    TRAIN_TEST_SPLIT: float = 0.8               # 80% training, 20% testing
    CROSS_VALIDATION_FOLDS: int = 5             # Number of CV folds
    RANDOM_SEED: int = 42                       # For reproducibility
    
    # Feature engineering
    TIME_WINDOW_SIZE: int = 10                  # Window size for time-series features
    LAG_FEATURES: List[int] = [1, 2, 3, 5]     # Lag periods for lag features
    
    # Data validation
    MAX_MISSING_RATE: float = 0.1               # Maximum 10% missing values allowed
    OUTLIER_STD_THRESHOLD: float = 3.0          # Z-score threshold for outliers
```

### 列挙型（Enum）の定義

```python
from enum import Enum

class ModelType(Enum):
    """Supported machine learning model types.
    
    Each enum value represents a model type that can be trained
    and deployed in the system.
    """
    LIGHTGBM = "lightgbm"        # LightGBM gradient boosting
    XGBOOST = "xgboost"          # XGBoost gradient boosting
    RANDOM_FOREST = "random_forest"  # Scikit-learn Random Forest
    NEURAL_NET = "neural_net"    # Simple feedforward neural network


class DataQuality(Enum):
    """Data quality status codes.
    
    Used to categorize data quality check results.
    """
    GOOD = 0      # Data passes all quality checks
    WARNING = 1   # Data has minor issues but is usable
    ERROR = 2     # Data has critical issues and should not be used
    UNKNOWN = 3   # Data quality cannot be determined
```

### モデル性能閾値の定義

```python
# Model performance thresholds
# Models below these thresholds will trigger retraining alerts
MIN_ACCURACY: float = 0.85  # Minimum acceptable accuracy (85%)
MIN_PRECISION: float = 0.80  # Minimum acceptable precision (80%)
MIN_RECALL: float = 0.75     # Minimum acceptable recall (75%)

# Column names for input data schema
# These columns must exist in all input CSV files
REQUIRED_COLUMNS: List[str] = [
    "timestamp",      # Data collection timestamp (ISO 8601 format)
    "temperature",    # Temperature in Celsius
    "pressure",       # Pressure in kPa
    "humidity",       # Relative humidity (0-100%)
    "defect_flag",    # Binary flag: 1=defect, 0=normal
]
```
