---
applyTo: "**/*.py,**/*.java,**/*.js,**/*.ts,**/*.tsx,**/*.jsx"
---

# AI Advanced Patterns Reference

このファイルは、[ai-code-writing.instructions.md](./ai-code-writing.instructions.md) の補足資料として、高度な型定義やデザインパターンを提供します。

**注意**: これらのパターンは必要な場合にのみ使用してください。基本的なコードには [ai-code-examples-reference.instructions.md](./ai-code-examples-reference.instructions.md) を参照してください。

---

## 目次

1. [高度な型定義](#高度な型定義)
2. [TypedDict詳細](#typeddict詳細)
3. [Generic型とクラス](#generic型とクラス)
4. [Callable型とコールバック](#callable型とコールバック)
5. [プロトコルとダックタイピング](#プロトコルとダックタイピング)

---

## 高度な型定義

### TypedDict詳細

TypedDictは辞書の構造を型として定義できる機能です。設定ファイルやJSONレスポンスの型定義に有用です。

```python
from typing import TypedDict, List, Optional

class ModelConfig(TypedDict):
    """Configuration for model training.
    
    This TypedDict defines the structure of model configuration dictionaries
    used throughout the training pipeline.
    """
    model_type: str           # Model type: "lightgbm", "xgboost", etc.
    learning_rate: float      # Learning rate for gradient descent
    epochs: int               # Number of training epochs
    batch_size: int           # Batch size for training

class DataPoint(TypedDict, total=False):
    """Data point with optional fields.
    
    Using total=False makes all fields optional. This is useful for
    data that may have incomplete information.
    """
    timestamp: str            # ISO 8601 timestamp
    value: float              # Sensor reading value
    label: Optional[str]      # Optional label for supervised learning

def train_model(config: ModelConfig, data: List[DataPoint]) -> Dict[str, Any]:
    """Train a model with the given configuration.
    
    Args:
        config (ModelConfig): Model configuration dictionary.
        data (List[DataPoint]): Training data points.
    
    Returns:
        Dict[str, Any]: Training results and metrics.
    """
    model = create_model(config["model_type"])
    model.train(data, lr=config["learning_rate"], epochs=config["epochs"])
    return {"accuracy": model.evaluate(), "loss": model.get_loss()}
```

### 部分的に必須なTypedDict

```python
from typing import TypedDict, NotRequired

class ProductionRecord(TypedDict):
    """Production record with required and optional fields."""
    timestamp: str              # Required: Data collection time
    line_id: str                # Required: Production line identifier
    temperature: float          # Required: Temperature reading
    pressure: float             # Required: Pressure reading
    defect_flag: NotRequired[int]  # Optional: Defect indicator (0 or 1)
    operator_id: NotRequired[str]  # Optional: Operator identifier

def validate_record(record: ProductionRecord) -> bool:
    """Validate production record has all required fields.
    
    Args:
        record (ProductionRecord): Production record to validate.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    required_fields = ['timestamp', 'line_id', 'temperature', 'pressure']
    return all(field in record for field in required_fields)
```

---

## Generic型とクラス

Generic型を使用すると、型安全性を保ちながら汎用的なコンテナやユーティリティを作成できます。

### 基本的なGenericクラス

```python
from typing import Generic, TypeVar, List, Optional, Callable

T = TypeVar('T')

class DataContainer(Generic[T]):
    """Generic container for storing and processing data.
    
    This container provides type-safe operations on lists of any type.
    The type parameter T is specified when creating an instance.
    
    Attributes:
        items (List[T]): List of stored items.
    
    Examples:
        >>> int_container = DataContainer[int]()
        >>> int_container.add(42)
        >>> int_container.get(0)
        42
        
        >>> str_container = DataContainer[str]()
        >>> str_container.add("hello")
        >>> str_container.get(0)
        'hello'
    """
    
    def __init__(self) -> None:
        """Initialize an empty container."""
        self.items: List[T] = []
    
    def add(self, item: T) -> None:
        """Add an item to the container.
        
        Args:
            item (T): Item to add.
        """
        self.items.append(item)
    
    def get(self, index: int) -> Optional[T]:
        """Get an item by index.
        
        Args:
            index (int): Index of the item to retrieve.
        
        Returns:
            Optional[T]: Item at the index, or None if out of bounds.
        """
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def filter(self, predicate: Callable[[T], bool]) -> List[T]:
        """Filter items using a predicate function.
        
        Args:
            predicate (Callable[[T], bool]): Function to test each item.
        
        Returns:
            List[T]: Filtered list of items.
        """
        return [item for item in self.items if predicate(item)]
    
    def map(self, transform: Callable[[T], T]) -> 'DataContainer[T]':
        """Apply a transformation to all items.
        
        Args:
            transform (Callable[[T], T]): Transformation function.
        
        Returns:
            DataContainer[T]: New container with transformed items.
        """
        new_container = DataContainer[T]()
        new_container.items = [transform(item) for item in self.items]
        return new_container
```

### 複数の型パラメータを持つGeneric

```python
K = TypeVar('K')
V = TypeVar('V')

class KeyValueStore(Generic[K, V]):
    """Generic key-value store with type-safe operations.
    
    Attributes:
        _data (Dict[K, V]): Internal storage dictionary.
    
    Examples:
        >>> store = KeyValueStore[str, int]()
        >>> store.set("count", 42)
        >>> store.get("count")
        42
    """
    
    def __init__(self) -> None:
        """Initialize an empty key-value store."""
        self._data: Dict[K, V] = {}
    
    def set(self, key: K, value: V) -> None:
        """Set a value for a key.
        
        Args:
            key (K): The key.
            value (V): The value to store.
        """
        self._data[key] = value
    
    def get(self, key: K) -> Optional[V]:
        """Get a value by key.
        
        Args:
            key (K): The key to look up.
        
        Returns:
            Optional[V]: The value if found, None otherwise.
        """
        return self._data.get(key)
    
    def keys(self) -> List[K]:
        """Get all keys.
        
        Returns:
            List[K]: List of all keys.
        """
        return list(self._data.keys())
    
    def values(self) -> List[V]:
        """Get all values.
        
        Returns:
            List[V]: List of all values.
        """
        return list(self._data.values())
```

---

## Callable型とコールバック

Callable型を使用すると、関数を引数として受け取る高階関数を型安全に定義できます。

### 基本的なCallable

```python
from typing import Callable, List, Any, Optional

def apply_transform(
    data: List[float],
    transform_func: Callable[[float], float]
) -> List[float]:
    """Apply a transformation function to each element.
    
    Args:
        data (List[float]): List of values to transform.
        transform_func (Callable[[float], float]): Function that takes a float
            and returns a transformed float.
    
    Returns:
        List[float]: List of transformed values.
    
    Examples:
        >>> data = [1.0, 2.0, 3.0]
        >>> result = apply_transform(data, lambda x: x * 2)
        >>> result
        [2.0, 4.0, 6.0]
    """
    return [transform_func(x) for x in data]

def apply_operation(
    values: List[float],
    operation: Callable[[float, float], float],
    initial: float
) -> float:
    """Apply a binary operation across all values.
    
    Args:
        values (List[float]): List of values to process.
        operation (Callable[[float, float], float]): Binary operation function.
        initial (float): Initial accumulator value.
    
    Returns:
        float: Result of applying operation across all values.
    
    Examples:
        >>> values = [1.0, 2.0, 3.0]
        >>> apply_operation(values, lambda a, b: a + b, 0.0)
        6.0
    """
    result = initial
    for value in values:
        result = operation(result, value)
    return result
```

### コールバック付きデータプロセッサ

```python
def create_processor(
    validator: Callable[[Any], bool],
    transformer: Callable[[Any], Any],
    error_handler: Optional[Callable[[Exception], None]] = None
) -> Callable[[Any], Any]:
    """Create a data processor with validation and transformation.
    
    Args:
        validator (Callable[[Any], bool]): Function to validate input.
        transformer (Callable[[Any], Any]): Function to transform valid input.
        error_handler (Optional[Callable[[Exception], None]], optional): 
            Function to handle errors. Defaults to None.
    
    Returns:
        Callable[[Any], Any]: A processor function that validates and transforms data.
    
    Examples:
        >>> def is_positive(x): return x > 0
        >>> def double(x): return x * 2
        >>> processor = create_processor(is_positive, double)
        >>> processor(5)
        10
    """
    def processor(data: Any) -> Any:
        try:
            if not validator(data):
                raise ValueError(f"バリデーションエラー: {data}")
            return transformer(data)
        except Exception as e:
            if error_handler:
                error_handler(e)
            raise
    
    return processor
```

### 複雑なコールバックパターン

```python
from typing import Callable, Dict, List, Any

class EventEmitter:
    """Event emitter with type-safe callbacks.
    
    イベント駆動型のアーキテクチャで使用するイベントエミッタ。
    型安全なコールバック登録と実行を提供します。
    
    Attributes:
        _listeners (Dict[str, List[Callable]]): Event listeners by event name.
    """
    
    def __init__(self) -> None:
        """Initialize event emitter."""
        self._listeners: Dict[str, List[Callable[..., None]]] = {}
    
    def on(self, event: str, callback: Callable[..., None]) -> None:
        """Register a callback for an event.
        
        Args:
            event (str): Event name.
            callback (Callable[..., None]): Callback function.
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
    
    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event and call all registered callbacks.
        
        Args:
            event (str): Event name.
            *args: Positional arguments for callbacks.
            **kwargs: Keyword arguments for callbacks.
        """
        if event in self._listeners:
            for callback in self._listeners[event]:
                callback(*args, **kwargs)
    
    def off(self, event: str, callback: Callable[..., None]) -> None:
        """Unregister a callback for an event.
        
        Args:
            event (str): Event name.
            callback (Callable[..., None]): Callback function to remove.
        """
        if event in self._listeners:
            self._listeners[event].remove(callback)
```

---

## プロトコルとダックタイピング

Python 3.8以降では、Protocolを使用して構造的部分型（structural subtyping）を定義できます。

### 基本的なProtocol

```python
from typing import Protocol, List

class Drawable(Protocol):
    """Protocol for objects that can be drawn.
    
    このプロトコルを実装するクラスは、draw()メソッドを持つ必要があります。
    明示的な継承は不要で、構造的に互換性があればOKです。
    """
    
    def draw(self) -> str:
        """Draw the object and return its representation.
        
        Returns:
            str: String representation of the drawn object.
        """
        ...

class Circle:
    """Circle class that implicitly implements Drawable protocol."""
    
    def __init__(self, radius: float) -> None:
        """Initialize circle with radius.
        
        Args:
            radius (float): Circle radius.
        """
        self.radius = radius
    
    def draw(self) -> str:
        """Draw the circle.
        
        Returns:
            str: Circle representation.
        """
        return f"Circle(radius={self.radius})"

class Rectangle:
    """Rectangle class that implicitly implements Drawable protocol."""
    
    def __init__(self, width: float, height: float) -> None:
        """Initialize rectangle with dimensions.
        
        Args:
            width (float): Rectangle width.
            height (float): Rectangle height.
        """
        self.width = width
        self.height = height
    
    def draw(self) -> str:
        """Draw the rectangle.
        
        Returns:
            str: Rectangle representation.
        """
        return f"Rectangle(width={self.width}, height={self.height})"

def render_shapes(shapes: List[Drawable]) -> List[str]:
    """Render a list of drawable objects.
    
    Args:
        shapes (List[Drawable]): List of objects implementing Drawable protocol.
    
    Returns:
        List[str]: List of rendered representations.
    """
    return [shape.draw() for shape in shapes]

# 使用例
# CircleとRectangleはDrawableを継承していないが、draw()メソッドがあるので使える
shapes: List[Drawable] = [Circle(5.0), Rectangle(10.0, 20.0)]
rendered = render_shapes(shapes)
```

### データアクセスProtocol

```python
from typing import Protocol, Any, Optional

class DataSource(Protocol):
    """Protocol for data sources that can be queried.
    
    データソースとして機能するクラスが実装すべきインターフェース。
    """
    
    def connect(self) -> None:
        """Establish connection to the data source."""
        ...
    
    def disconnect(self) -> None:
        """Close connection to the data source."""
        ...
    
    def query(self, query_string: str) -> List[Dict[str, Any]]:
        """Execute a query and return results.
        
        Args:
            query_string (str): Query to execute.
        
        Returns:
            List[Dict[str, Any]]: Query results.
        """
        ...

class CSVDataSource:
    """CSV file data source implementing DataSource protocol."""
    
    def __init__(self, file_path: str) -> None:
        """Initialize CSV data source.
        
        Args:
            file_path (str): Path to CSV file.
        """
        self.file_path = file_path
        self.data: Optional[pd.DataFrame] = None
    
    def connect(self) -> None:
        """Load CSV file."""
        self.data = pd.read_csv(self.file_path)
    
    def disconnect(self) -> None:
        """Clear loaded data."""
        self.data = None
    
    def query(self, query_string: str) -> List[Dict[str, Any]]:
        """Query CSV data using pandas query syntax.
        
        Args:
            query_string (str): Pandas query string.
        
        Returns:
            List[Dict[str, Any]]: Query results as list of dictionaries.
        """
        if self.data is None:
            raise RuntimeError("データソースが接続されていません")
        
        result = self.data.query(query_string)
        return result.to_dict('records')

def fetch_data(source: DataSource, query: str) -> List[Dict[str, Any]]:
    """Fetch data from any data source.
    
    Args:
        source (DataSource): Data source implementing DataSource protocol.
        query (str): Query string.
    
    Returns:
        List[Dict[str, Any]]: Query results.
    """
    source.connect()
    try:
        return source.query(query)
    finally:
        source.disconnect()
```

---

## まとめ

これらの高度なパターンは、以下の場合に使用してください:

1. **TypedDict**: 設定ファイルやJSONレスポンスの型定義
2. **Generic型**: 型安全な汎用コンテナやユーティリティの実装
3. **Callable型**: 高階関数やコールバックを多用する場合
4. **Protocol**: ダックタイピングを型安全に行いたい場合

基本的なコードには、これらの高度なパターンは不要です。[ai-code-examples-reference.instructions.md](./ai-code-examples-reference.instructions.md) の基本パターンを優先してください。
