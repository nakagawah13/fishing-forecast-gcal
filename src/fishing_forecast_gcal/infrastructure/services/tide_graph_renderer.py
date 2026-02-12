"""Tide graph image renderer (matplotlib implementation).

潮汐データからタイドグラフ画像を生成する Infrastructure サービス。
matplotlib + seaborn + matplotlib-fontja を使用し、
スマホ表示に最適化されたダークモード基調の画像を出力します。

Domain 層の ``ITideGraphService`` Protocol を実装しています。
"""

import logging
import tempfile
from datetime import date, datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib_fontja
import numpy as np
import seaborn as sns
from numpy.typing import NDArray

from fishing_forecast_gcal.domain.models.tide import TideEvent, TideType

# numpy array type alias for pyright compatibility
type FloatArray = NDArray[np.float64]

logger = logging.getLogger(__name__)

# matplotlib バックエンドを非表示に設定（サーバー環境対応）
matplotlib.use("Agg")

# seaborn テーマ適用後に日本語フォントを再適用
sns.set_theme(style="darkgrid")
matplotlib_fontja.japanize()


class _DarkPalette:
    """Dark mode color palette for tide graph.

    ダークモード基調のカラーパレット定数。
    Issue #76 POC で策定した配色に基づく。
    """

    BACKGROUND = "#0d1117"
    TIDE_CURVE = "#58a6ff"
    FILL_ALPHA = 0.15
    HIGH_TIDE_MARKER = "#f0883e"
    LOW_TIDE_MARKER = "#3fb950"
    PRIME_TIME_BAND = "#d29922"
    PRIME_TIME_ALPHA = 0.15
    GRID = "#30363d"
    TEXT = "#c9d1d9"
    TITLE = "#f0f6fc"


class TideGraphRenderer:
    """Tide graph image renderer using matplotlib.

    潮汐データからタイドグラフ PNG 画像を生成します。
    スマホ表示に最適化されたスクエア・ダークモード仕様。

    Implements: ``ITideGraphService`` Protocol (domain layer).

    Attributes:
        DPI: Output resolution (dots per inch).
        FIGSIZE: Image size (width, height) in inches. (6, 6) = 900x900px @150dpi.
    """

    DPI: int = 150
    FIGSIZE: tuple[int, int] = (6, 6)

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

        潮汐データからダークモード基調のタイドグラフ画像を生成し、
        PNG ファイルのパスを返します。

        Args:
            target_date: Target date for the graph.
            hourly_heights: Time-height pairs where time is hours (0.0-24.0)
                and height is cm.
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
        if not hourly_heights:
            raise ValueError("hourly_heights must not be empty")

        logger.info(
            "タイドグラフ画像を生成: %s %s (%s)",
            location_name,
            target_date,
            tide_type.value,
        )

        # 出力先の決定
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix="tide_graph_"))
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"tide_graph_{location_id}_{target_date.strftime('%Y%m%d')}.png"
        output_path = output_dir / filename

        # データ準備
        hours = np.array([h for h, _ in hourly_heights])
        heights = np.array([ht for _, ht in hourly_heights])

        # 描画
        fig, ax = self._create_figure()
        self._plot_tide_curve(ax, hours, heights)
        self._plot_tide_events(ax, tide_events, target_date)
        self._plot_prime_time_bands(ax, prime_times, target_date)
        self._configure_axes(ax, heights, target_date, location_name, tide_type)

        # 保存
        fig.savefig(
            output_path,
            dpi=self.DPI,
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
            pad_inches=0.3,
        )
        plt.close(fig)

        file_size_kb = output_path.stat().st_size / 1024
        logger.info(
            "タイドグラフ画像を保存: %s (%.1f KB)",
            output_path,
            file_size_kb,
        )

        return output_path

    def _create_figure(self) -> tuple[plt.Figure, plt.Axes]:
        """Create figure with dark mode styling.

        Returns:
            tuple[Figure, Axes]: Matplotlib figure and axes.
        """
        fig, ax = plt.subplots(figsize=self.FIGSIZE)
        fig.set_facecolor(_DarkPalette.BACKGROUND)
        ax.set_facecolor(_DarkPalette.BACKGROUND)
        return fig, ax  # type: ignore[return-value]

    def _plot_tide_curve(
        self,
        ax: plt.Axes,
        hours: FloatArray,
        heights: FloatArray,
    ) -> None:
        """Plot the tide height curve and fill.

        Args:
            ax: Matplotlib axes.
            hours: Time values in hours (0-24).
            heights: Tide height values in cm.
        """
        ax.plot(  # type: ignore[call-overload]
            hours,
            heights,
            color=_DarkPalette.TIDE_CURVE,
            linewidth=2.5,
            zorder=3,
        )
        ax.fill_between(  # type: ignore[call-overload]
            hours,
            heights,
            alpha=_DarkPalette.FILL_ALPHA,
            color=_DarkPalette.TIDE_CURVE,
            zorder=2,
        )

    def _plot_tide_events(
        self,
        ax: plt.Axes,
        tide_events: list[TideEvent],
        target_date: date,
    ) -> None:
        """Plot high/low tide markers and annotations.

        Args:
            ax: Matplotlib axes.
            tide_events: List of high/low tide events.
            target_date: Target date for filtering events.
        """
        for event in tide_events:
            # 対象日のイベントのみ描画
            if event.time.date() != target_date:
                continue

            hour = event.time.hour + event.time.minute / 60.0
            height = event.height_cm

            if event.event_type == "high":
                color = _DarkPalette.HIGH_TIDE_MARKER
                label_prefix = "満"
                va = "bottom"
                y_offset = 8
            else:
                color = _DarkPalette.LOW_TIDE_MARKER
                label_prefix = "干"
                va = "top"
                y_offset = -8

            # マーカー描画
            ax.plot(  # type: ignore[call-overload]
                hour,
                height,
                "o",
                color=color,
                markersize=10,
                zorder=5,
            )

            # アノテーション（時刻 + 潮位の 2 行ラベル）
            label = f"{label_prefix} {event.time.strftime('%H:%M')}\n{int(event.height_cm)}cm"
            ax.annotate(
                label,
                xy=(hour, height),
                xytext=(0, y_offset),
                textcoords="offset points",
                ha="center",
                va=va,
                fontsize=10,
                fontweight="bold",
                color=color,
                zorder=6,
            )

    def _plot_prime_time_bands(
        self,
        ax: plt.Axes,
        prime_times: list[tuple[datetime, datetime]] | None,
        target_date: date,
    ) -> None:
        """Plot prime time highlight bands.

        Args:
            ax: Matplotlib axes.
            prime_times: List of prime time ranges (start, end) or None.
            target_date: Target date for time calculation.
        """
        if not prime_times:
            return

        label_added = False
        for start, end in prime_times:
            # 時刻を時間単位に変換（対象日内にクリップ）
            start_hour = max(0.0, self._datetime_to_hours(start, target_date))
            end_hour = min(24.0, self._datetime_to_hours(end, target_date))

            if start_hour >= end_hour:
                continue

            ax.axvspan(
                start_hour,
                end_hour,
                alpha=_DarkPalette.PRIME_TIME_ALPHA,
                color=_DarkPalette.PRIME_TIME_BAND,
                zorder=1,
                label="時合い帯" if not label_added else None,
            )
            label_added = True

    def _configure_axes(
        self,
        ax: plt.Axes,
        heights: FloatArray,
        target_date: date,
        location_name: str,
        tide_type: TideType,
    ) -> None:
        """Configure axes styling, labels, and title.

        Args:
            ax: Matplotlib axes.
            heights: Height array for Y-axis range calculation.
            target_date: Target date for title.
            location_name: Location name for title.
            tide_type: Tide type for title emoji.
        """
        # X 軸: 0〜24 時（3 時間刻み）
        ax.set_xlim(0, 24)
        ax.set_xticks(range(0, 25, 3))
        ax.set_xticklabels(
            [f"{h:02d}:00" for h in range(0, 25, 3)],
            fontsize=9,
            color=_DarkPalette.TEXT,
        )

        # Y 軸: 潮位範囲にマージン追加
        height_min = float(np.min(heights))
        height_max = float(np.max(heights))
        margin = (height_max - height_min) * 0.15
        ax.set_ylim(height_min - margin, height_max + margin)
        ax.tick_params(axis="y", colors=_DarkPalette.TEXT, labelsize=9)

        # 軸ラベル
        ax.set_xlabel("時刻", fontsize=11, color=_DarkPalette.TEXT)
        ax.set_ylabel("潮位 (cm)", fontsize=11, color=_DarkPalette.TEXT)

        # グリッド
        ax.grid(True, color=_DarkPalette.GRID, linewidth=0.5, alpha=0.8)

        # スパインの色
        for spine in ax.spines.values():
            spine.set_color(_DarkPalette.GRID)

        # タイトル（絵文字はフォントに含まれない場合があるため、テキストのみ使用）
        title = f"{location_name} {target_date.strftime('%Y年%m月%d日')}  [{tide_type.value}]"
        ax.set_title(
            title,
            fontsize=14,
            fontweight="bold",
            color=_DarkPalette.TITLE,
            pad=15,
        )

    @staticmethod
    def _datetime_to_hours(dt: datetime, target_date: date) -> float:
        """Convert datetime to fractional hours relative to target_date midnight.

        Args:
            dt: Datetime to convert.
            target_date: Reference date (midnight = 0.0h).

        Returns:
            float: Hours from midnight of target_date.
        """
        midnight = datetime.combine(target_date, datetime.min.time(), tzinfo=dt.tzinfo)
        delta = dt - midnight
        return delta.total_seconds() / 3600.0
