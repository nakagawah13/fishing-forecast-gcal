"""Tide graph service interface (Protocol).

タイドグラフ画像生成サービスのインターフェース定義。
Domain 層では Protocol のみを定義し、実装は Infrastructure 層に配置します。

実装クラス: ``infrastructure.services.tide_graph_renderer.TideGraphRenderer``
"""

from datetime import date, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from fishing_forecast_gcal.domain.models.tide import TideEvent, TideType


@runtime_checkable
class ITideGraphService(Protocol):
    """Interface for tide graph image generation.

    潮汐データからタイドグラフ PNG 画像を生成するサービスの Protocol。
    Infrastructure 層で具象クラスを実装すること。
    """

    def generate_graph(
        self,
        target_date: date,
        hourly_heights: list[tuple[float, float]],
        tide_events: list[TideEvent],
        location_name: str,
        tide_type: TideType,
        prime_times: list[tuple[datetime, datetime]] | None = None,
        output_dir: Path | None = None,
        location_id: str = "unknown",
    ) -> Path:
        """Generate a tide graph PNG image.

        Args:
            target_date: Target date for the graph.
            hourly_heights: Time-height pairs (hours 0.0-24.0, height cm).
            tide_events: High/low tide events for annotation.
            location_name: Location display name for title.
            tide_type: Tide type for title display.
            prime_times: List of prime time ranges (start, end) or None.
            output_dir: Output directory. Uses temp dir if None.
            location_id: Location ID for filename.

        Returns:
            Path to the generated PNG file.

        Raises:
            ValueError: If hourly_heights is empty or invalid.
        """
        ...
