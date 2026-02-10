"""parse_jma_hourly_text() のユニットテスト."""

from datetime import timedelta, timezone

from fishing_forecast_gcal.infrastructure.jma.hourly_text_parser import (
    DIGITS_PER_HOUR,
    HOURS_PER_DAY,
    LINE_LENGTH,
    parse_jma_hourly_text,
)

JST = timezone(timedelta(hours=9))


def _build_line(
    heights: list[int | None],
    year: int = 2025,
    month: int = 6,
    day: int = 15,
    station: str = "TK",
) -> str:
    """Build a single JMA fixed-width line for testing.

    テスト用に JMA フォーマットの1行(137文字)を生成します。

    Args:
        heights: 24 hourly heights (cm).  None → blank (missing).
                 (24時間分の潮位。None は欠測)
        year: Year (4-digit; lower 2 digits used).
              (年、4桁; 下2桁を使用)
        month: Month.
               (月)
        day: Day.
             (日)
        station: Station code.
                 (地点記号)

    Returns:
        A 137-character fixed-width line.
        (137文字の固定長文字列)
    """
    # カラム 1-72: 3桁 × 24
    hourly_part = ""
    for h in heights:
        if h is None:
            hourly_part += "   "
        else:
            hourly_part += f"{h:3d}"
    # 24時間分が足りなければ空白で埋める
    while len(hourly_part) < HOURS_PER_DAY * DIGITS_PER_HOUR:
        hourly_part += "   "
    hourly_part = hourly_part[: HOURS_PER_DAY * DIGITS_PER_HOUR]

    # カラム 73-80: YYMM DD SS (年下2桁, 月, 日, 地点コード)
    meta = f"{year % 100:02d}{month:02d}{day:02d}{station:2s}"

    # カラム 81-137: ダミー (スペース埋め)
    remaining = LINE_LENGTH - len(hourly_part) - len(meta)
    line = hourly_part + meta + " " * remaining

    assert len(line) == LINE_LENGTH, f"Line length {len(line)} != {LINE_LENGTH}"
    return line


class TestParseJmaHourlyText:
    """parse_jma_hourly_text() tests."""

    def test_single_line_full(self) -> None:
        """Parse a line with all 24 hours present."""
        heights = list(range(100, 124))  # 100, 101, ..., 123
        line = _build_line(heights)
        result = parse_jma_hourly_text(line, "TK")

        assert len(result) == 24
        for i, (dt, val) in enumerate(result):
            assert dt.hour == i
            assert val == heights[i]
            assert dt.tzinfo == JST

    def test_single_line_with_newline(self) -> None:
        """Parse text containing newline separators."""
        heights = [150] * 24
        text = _build_line(heights) + "\n"
        result = parse_jma_hourly_text(text, "TK")
        assert len(result) == 24

    def test_missing_values_excluded(self) -> None:
        """Missing values (None) should be excluded from results."""
        heights: list[int | None] = [100, None, 102] + [None] * 21
        line = _build_line(heights)
        result = parse_jma_hourly_text(line, "TK")

        assert len(result) == 2
        assert result[0][1] == 100.0
        assert result[1][1] == 102.0

    def test_date_parsed_correctly(self) -> None:
        """Verify date fields are extracted correctly."""
        heights = [200] * 24
        line = _build_line(heights, year=2024, month=12, day=31)
        result = parse_jma_hourly_text(line, "TK")

        dt = result[0][0]
        assert dt.year == 2024
        assert dt.month == 12
        assert dt.day == 31

    def test_multiple_lines(self) -> None:
        """Parse multiple lines (days)."""
        lines = []
        for day in range(1, 4):
            lines.append(_build_line([100] * 24, day=day))
        text = "\n".join(lines)
        result = parse_jma_hourly_text(text, "TK")

        assert len(result) == 72  # 3 days × 24 hours

    def test_empty_text_returns_empty(self) -> None:
        """Empty string should return empty list."""
        result = parse_jma_hourly_text("", "TK")
        assert result == []

    def test_short_lines_skipped(self) -> None:
        """Lines shorter than 80 chars should be silently skipped."""
        text = "short line\nanother short"
        result = parse_jma_hourly_text(text, "TK")
        assert result == []

    def test_utc_offset(self) -> None:
        """Returned datetimes must be JST (UTC+9)."""
        heights = [100] * 24
        line = _build_line(heights)
        result = parse_jma_hourly_text(line, "TK")

        dt = result[0][0]
        assert dt.utcoffset() == timedelta(hours=9)

    def test_no_newline_concatenated_format(self) -> None:
        """Parse concatenated text without newlines (137-char chunk split)."""
        line1 = _build_line([100] * 24, day=1)
        line2 = _build_line([200] * 24, day=2)
        text = line1 + line2  # 改行なし連結
        result = parse_jma_hourly_text(text, "TK")

        assert len(result) == 48
        # 1日目は100, 2日目は200
        assert result[0][1] == 100.0
        assert result[24][1] == 200.0

    def test_station_code_mismatch_still_parses(self) -> None:
        """Station code mismatch in data should not raise, only log.

        地点コード不一致は debug ログ出力のみで、データはパースされる。
        """
        heights = [100] * 24
        line = _build_line(heights, station="AB")
        result = parse_jma_hourly_text(line, "TK")
        # データはパースされる
        assert len(result) == 24
