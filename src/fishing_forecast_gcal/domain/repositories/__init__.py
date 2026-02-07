"""Domain層のリポジトリインターフェースを提供

このパッケージは外部データソースへのアクセスを抽象化するインターフェースを定義します。
依存性逆転の原則（DIP）に基づき、Domain層がInfrastructure層に依存しないようにします。
"""

from .calendar_repository import ICalendarRepository
from .tide_data_repository import ITideDataRepository
from .weather_repository import IWeatherRepository

__all__ = [
    "ICalendarRepository",
    "ITideDataRepository",
    "IWeatherRepository",
]
