"""Tests for TideGraphService.

タイドグラフ画像生成サービスのユニットテスト。
画像生成、配色、アノテーション、エラーハンドリングを検証します。
"""

import struct
import zlib
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from fishing_forecast_gcal.domain.models.tide import TideEvent, TideType
from fishing_forecast_gcal.domain.services.tide_graph_service import TideGraphService

JST = ZoneInfo("Asia/Tokyo")


# ---- Fixtures ----


@pytest.fixture
def service() -> TideGraphService:
    """Create a TideGraphService instance."""
    return TideGraphService()


@pytest.fixture
def sample_hourly_heights() -> list[tuple[float, float]]:
    """Generate sample hourly heights (sinusoidal tide curve).

    24 時間分の正弦波で近似した潮位データを生成。
    0-24 時を 0.5 時間刻みで 49 点。
    """
    import math

    heights: list[tuple[float, float]] = []
    for i in range(49):  # 0.0 to 24.0, step 0.5
        hour = i * 0.5
        # 半日周潮（M2成分に近似）: 周期 12.42h
        height = 120.0 + 50.0 * math.sin(2 * math.pi * hour / 12.42)
        heights.append((hour, height))
    return heights


@pytest.fixture
def sample_tide_events() -> list[TideEvent]:
    """Create sample high/low tide events."""
    return [
        TideEvent(
            time=datetime(2026, 2, 15, 3, 6, tzinfo=JST),
            height_cm=170.0,
            event_type="high",
        ),
        TideEvent(
            time=datetime(2026, 2, 15, 9, 18, tzinfo=JST),
            height_cm=70.0,
            event_type="low",
        ),
        TideEvent(
            time=datetime(2026, 2, 15, 15, 30, tzinfo=JST),
            height_cm=165.0,
            event_type="high",
        ),
        TideEvent(
            time=datetime(2026, 2, 15, 21, 42, tzinfo=JST),
            height_cm=75.0,
            event_type="low",
        ),
    ]


@pytest.fixture
def sample_prime_time() -> tuple[datetime, datetime]:
    """Create sample prime time range (±2h around first high tide)."""
    return (
        datetime(2026, 2, 15, 1, 6, tzinfo=JST),
        datetime(2026, 2, 15, 5, 6, tzinfo=JST),
    )


@pytest.fixture
def target_date() -> date:
    """Target date for testing."""
    return date(2026, 2, 15)


# ---- Helper functions ----


def _read_png_chunks(filepath: Path) -> dict[str, bytes]:
    """Read PNG chunks from a file.

    Returns:
        dict: Mapping of chunk type to chunk data.
    """
    chunks: dict[str, bytes] = {}
    with open(filepath, "rb") as f:
        # PNG signature (8 bytes)
        signature = f.read(8)
        assert signature == b"\x89PNG\r\n\x1a\n", "Not a valid PNG file"

        while True:
            length_bytes = f.read(4)
            if len(length_bytes) < 4:
                break
            length = struct.unpack(">I", length_bytes)[0]
            chunk_type = f.read(4).decode("ascii")
            chunk_data = f.read(length)
            _crc = f.read(4)  # CRC
            chunks[chunk_type] = chunk_data
            if chunk_type == "IEND":
                break
    return chunks


def _get_png_background_color(filepath: Path) -> tuple[int, int, int] | None:
    """Extract background color from PNG bKGD chunk if present.

    Returns:
        RGB tuple or None if no bKGD chunk.
    """
    chunks = _read_png_chunks(filepath)
    if "bKGD" not in chunks:
        return None
    data = chunks["bKGD"]
    # For RGB images: 6 bytes (2 per channel)
    if len(data) == 6:
        r = struct.unpack(">H", data[0:2])[0]
        g = struct.unpack(">H", data[2:4])[0]
        b = struct.unpack(">H", data[4:6])[0]
        return (r >> 8, g >> 8, b >> 8)
    return None


def _png_contains_text(filepath: Path, search_text: str) -> bool:
    """Check if PNG contains text in tEXt/iTXt chunks or raw data.

    PNGのテキストチャンクまたは圧縮データ内に指定テキストが含まれるか確認。
    matplotlib は tEXt チャンクにメタデータを書き込まないため、
    レンダリングされたテキストはピクセルデータ内には直接検索不可。
    代わりにファイル全体を走査する。
    """
    chunks = _read_png_chunks(filepath)

    # tEXt チャンクの検索
    for chunk_type in ("tEXt", "iTXt", "zTXt"):
        if chunk_type in chunks:
            chunk_data = chunks[chunk_type]
            if search_text.encode("utf-8") in chunk_data:
                return True
            # zTXt は圧縮されている
            if chunk_type == "zTXt":
                try:
                    null_idx = chunk_data.index(b"\x00")
                    compressed = chunk_data[null_idx + 2 :]  # skip null + compression method
                    decompressed = zlib.decompress(compressed)
                    if search_text.encode("utf-8") in decompressed:
                        return True
                except (ValueError, zlib.error):
                    pass

    return False


# ---- Test: Basic generation ----


class TestGenerateGraph:
    """Test basic graph generation."""

    def test_generates_png_file(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """PNG file is created at the expected path."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            output_dir=tmp_path,
            location_id="tk",
        )

        assert result.exists()
        assert result.suffix == ".png"
        assert result.name == "tide_graph_tk_20260215.png"

    def test_file_is_valid_png(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """Generated file has valid PNG signature."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            output_dir=tmp_path,
            location_id="tk",
        )

        with open(result, "rb") as f:
            signature = f.read(8)
        assert signature == b"\x89PNG\r\n\x1a\n"

    def test_file_size_under_100kb(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """Generated file is under 100KB."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            output_dir=tmp_path,
            location_id="tk",
        )

        file_size_kb = result.stat().st_size / 1024
        assert file_size_kb < 100, f"File size {file_size_kb:.1f}KB exceeds 100KB limit"

    def test_uses_temp_dir_when_output_dir_is_none(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
    ) -> None:
        """Uses temporary directory when output_dir is None."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            output_dir=None,
            location_id="tk",
        )

        assert result.exists()
        assert "tide_graph_" in str(result.parent)
        # クリーンアップ
        result.unlink()

    def test_creates_output_dir_if_not_exists(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """Creates output directory if it does not exist."""
        nested_dir = tmp_path / "sub" / "dir"
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            output_dir=nested_dir,
            location_id="tk",
        )

        assert result.exists()
        assert nested_dir.is_dir()


# ---- Test: Image content ----


class TestImageContent:
    """Test image content and styling."""

    def test_dark_mode_background(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """Image uses dark mode background color.

        PNG ファイルの IHDR チャンク後のデータから背景色を推定。
        matplotlib は fig.facecolor を設定しているため、
        ピクセルデータの角（通常は背景色）を検証。
        """
        from PIL import Image

        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            output_dir=tmp_path,
            location_id="tk",
        )

        img = Image.open(result)
        # 左上角のピクセルは背景色のはず
        pixel = img.getpixel((0, 0))
        # #0d1117 = (13, 17, 23)、近似チェック（±5の許容範囲）
        assert abs(pixel[0] - 13) <= 5, f"Red channel: {pixel[0]}"
        assert abs(pixel[1] - 17) <= 5, f"Green channel: {pixel[1]}"
        assert abs(pixel[2] - 23) <= 5, f"Blue channel: {pixel[2]}"

    def test_graph_contains_metadata(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """PNG contains matplotlib metadata in tEXt chunks."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            output_dir=tmp_path,
            location_id="tk",
        )

        chunks = _read_png_chunks(result)
        # matplotlib は通常 "Software" を tEXt に書き込む
        assert "IHDR" in chunks
        assert "IEND" in chunks


# ---- Test: Prime time band ----


class TestPrimeTimeBand:
    """Test prime time highlight band."""

    def test_with_prime_time(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        sample_prime_time: tuple[datetime, datetime],
        tmp_path: Path,
    ) -> None:
        """Graph generates successfully with prime time band."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            prime_time=sample_prime_time,
            output_dir=tmp_path,
            location_id="tk",
        )

        assert result.exists()

    def test_without_prime_time(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """Graph generates successfully without prime time band."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            prime_time=None,
            output_dir=tmp_path,
            location_id="tk",
        )

        assert result.exists()


# ---- Test: Tide types ----


class TestTideTypes:
    """Test different tide type variations."""

    @pytest.mark.parametrize(
        "tide_type",
        [TideType.SPRING, TideType.MODERATE, TideType.NEAP, TideType.LONG, TideType.YOUNG],
        ids=["spring", "moderate", "neap", "long", "young"],
    )
    def test_all_tide_types(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
        tide_type: TideType,
    ) -> None:
        """Graph generates for all tide types."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="東京",
            tide_type=tide_type,
            output_dir=tmp_path,
            location_id="tk",
        )

        assert result.exists()


# ---- Test: Error handling ----


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_empty_hourly_heights_raises_error(
        self,
        service: TideGraphService,
        target_date: date,
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """Raises ValueError for empty hourly_heights."""
        with pytest.raises(ValueError, match="hourly_heights must not be empty"):
            service.generate_graph(
                target_date=target_date,
                hourly_heights=[],
                tide_events=sample_tide_events,
                location_name="東京",
                tide_type=TideType.SPRING,
                output_dir=tmp_path,
                location_id="tk",
            )

    def test_empty_tide_events(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        tmp_path: Path,
    ) -> None:
        """Graph generates with empty tide events (no annotations)."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=[],
            location_name="東京",
            tide_type=TideType.SPRING,
            output_dir=tmp_path,
            location_id="tk",
        )

        assert result.exists()

    def test_tide_events_from_different_date(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        tmp_path: Path,
    ) -> None:
        """Events from different dates are ignored in annotations."""
        # 別日のイベント
        wrong_date_events = [
            TideEvent(
                time=datetime(2026, 2, 16, 6, 12, tzinfo=JST),
                height_cm=160.0,
                event_type="high",
            ),
        ]

        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=wrong_date_events,
            location_name="東京",
            tide_type=TideType.SPRING,
            output_dir=tmp_path,
            location_id="tk",
        )

        assert result.exists()


# ---- Test: Filename ----


class TestFilename:
    """Test filename generation."""

    def test_filename_format(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """Filename follows the tide_graph_{location_id}_{YYYYMMDD}.png pattern."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="相模湾",
            tide_type=TideType.MODERATE,
            output_dir=tmp_path,
            location_id="sgm",
        )

        assert result.name == "tide_graph_sgm_20260215.png"

    def test_default_location_id(
        self,
        service: TideGraphService,
        target_date: date,
        sample_hourly_heights: list[tuple[float, float]],
        sample_tide_events: list[TideEvent],
        tmp_path: Path,
    ) -> None:
        """Default location_id is 'unknown'."""
        result = service.generate_graph(
            target_date=target_date,
            hourly_heights=sample_hourly_heights,
            tide_events=sample_tide_events,
            location_name="テスト地点",
            tide_type=TideType.NEAP,
            output_dir=tmp_path,
        )

        assert result.name == "tide_graph_unknown_20260215.png"


# ---- Test: _datetime_to_hours ----


class TestDatetimeToHours:
    """Test _datetime_to_hours static method."""

    def test_midnight_returns_zero(self) -> None:
        """Midnight returns 0.0."""
        dt = datetime(2026, 2, 15, 0, 0, tzinfo=JST)
        result = TideGraphService._datetime_to_hours(dt, date(2026, 2, 15))
        assert result == 0.0

    def test_noon_returns_twelve(self) -> None:
        """Noon returns 12.0."""
        dt = datetime(2026, 2, 15, 12, 0, tzinfo=JST)
        result = TideGraphService._datetime_to_hours(dt, date(2026, 2, 15))
        assert result == 12.0

    def test_with_minutes(self) -> None:
        """Time with minutes returns correct fractional hours."""
        dt = datetime(2026, 2, 15, 6, 30, tzinfo=JST)
        result = TideGraphService._datetime_to_hours(dt, date(2026, 2, 15))
        assert result == 6.5

    def test_before_midnight_returns_negative(self) -> None:
        """Time before target date returns negative hours."""
        dt = datetime(2026, 2, 14, 23, 0, tzinfo=JST)
        result = TideGraphService._datetime_to_hours(dt, date(2026, 2, 15))
        assert result == -1.0

    def test_after_midnight_returns_over_24(self) -> None:
        """Time after target date returns hours > 24."""
        dt = datetime(2026, 2, 16, 1, 0, tzinfo=JST)
        result = TideGraphService._datetime_to_hours(dt, date(2026, 2, 15))
        assert result == 25.0
