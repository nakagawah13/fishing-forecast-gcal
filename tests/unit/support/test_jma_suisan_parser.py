"""Unit tests for JMA suisan parser.

JMA推算テキストパーサーの単体テストです。
"""

from __future__ import annotations

from datetime import date, time

import pytest

from tests.support.jma_suisan_parser import JMASuisanDaily, parse_jma_suisan_text


class TestJMASuisanDaily:
    """Tests for JMASuisanDaily dataclass."""

    def test_instantiation(self) -> None:
        """Test JMASuisanDaily can be instantiated correctly."""
        target_date = date(2024, 11, 3)
        station_id = "TK"
        highs = [(time(6, 12), 162), (time(18, 34), 158)]
        lows = [(time(0, 15), 58), (time(12, 45), 62)]

        daily = JMASuisanDaily(
            date=target_date,
            station_id=station_id,
            highs=highs,
            lows=lows,
        )

        assert daily.date == target_date
        assert daily.station_id == station_id
        assert len(daily.highs) == 2
        assert len(daily.lows) == 2
        assert daily.highs[0] == (time(6, 12), 162)
        assert daily.lows[0] == (time(0, 15), 58)

    def test_immutability(self) -> None:
        """Test JMASuisanDaily is frozen (immutable)."""
        daily = JMASuisanDaily(
            date=date(2024, 11, 3),
            station_id="TK",
            highs=[(time(6, 12), 162)],
            lows=[(time(0, 15), 58)],
        )

        with pytest.raises(AttributeError):
            daily.date = date(2024, 11, 4)  # type: ignore[misc]


class TestParseJMASuisanText:
    """Tests for parse_jma_suisan_text function."""

    def test_parse_single_day_normal_case(self) -> None:
        """Test parsing a single day with 2 highs and 2 lows."""
        # JMA suisan text format (simplified)
        # Position 72-74: year (24), 74-76: month (11), 76-78: day (03), 78-80: station (TK)
        # Position 80-108: high tide block (4 entries x 7 chars)
        # Position 108-136: low tide block (4 entries x 7 chars)
        # Each entry: HHMM (4 chars) + height in cm (3 chars) = 7 chars
        line = (
            " " * 72  # Hourly data (not used)
            + "241103TK"  # Year, month, day, station
            + "0612162"  # High 1: 06:12 (162cm)
            + "0634158"  # High 2: 06:34 (158cm)
            + "9999999" * 2  # Empty highs slots
            + "0015058"  # Low 1: 00:15 (58cm)
            + "1245045"  # Low 2: 12:45 (45cm)
            + "9999999" * 2  # Empty lows slots
        )

        result = parse_jma_suisan_text(line, "TK")

        assert len(result) == 1
        target_date = date(2024, 11, 3)
        assert target_date in result

        daily = result[target_date]
        assert daily.station_id == "TK"
        assert len(daily.highs) == 2
        assert len(daily.lows) == 2

        # Check high tides
        assert daily.highs[0] == (time(6, 12), 162)
        assert daily.highs[1] == (time(6, 34), 158)

        # Check low tides
        assert daily.lows[0] == (time(0, 15), 58)
        assert daily.lows[1] == (time(12, 45), 45)

    def test_parse_empty_text(self) -> None:
        """Test parsing empty text returns empty dict."""
        result = parse_jma_suisan_text("", "TK")
        assert len(result) == 0

    def test_parse_invalid_line_too_short(self) -> None:
        """Test parsing line that is too short is skipped."""
        short_line = " " * 100  # Less than required length
        result = parse_jma_suisan_text(short_line, "TK")
        assert len(result) == 0

    def test_parse_missing_date_fields(self) -> None:
        """Test parsing line with missing date fields is skipped."""
        line = " " * 72 + "  1103TK" + " " * 56  # Missing year
        result = parse_jma_suisan_text(line, "TK")
        assert len(result) == 0

    def test_parse_invalid_date_values(self) -> None:
        """Test parsing line with invalid date values is skipped."""
        line = " " * 72 + "249903TK" + " " * 56  # Invalid month (99)
        result = parse_jma_suisan_text(line, "TK")
        assert len(result) == 0

    def test_parse_different_station_filtered(self) -> None:
        """Test parsing filters out different station."""
        line = (
            " " * 72
            + "241103OS"  # Station OS, not TK
            + "0612162"
            + "9999999" * 3
            + "0015058"
            + "9999999" * 3
        )
        result = parse_jma_suisan_text(line, "TK")
        assert len(result) == 0

    def test_parse_missing_data_marker(self) -> None:
        """Test parsing skips missing data markers (9999/999)."""
        line = (
            " " * 72
            + "241103TK"
            + "0612162"  # One valid high
            + "9999999" * 3  # Rest missing (9999 time + 999 height)
            + "0015058"  # One valid low
            + "9999999" * 3  # Rest missing
        )

        result = parse_jma_suisan_text(line, "TK")

        assert len(result) == 1
        daily = result[date(2024, 11, 3)]
        assert len(daily.highs) == 1
        assert len(daily.lows) == 1
        assert daily.highs[0] == (time(6, 12), 162)
        assert daily.lows[0] == (time(0, 15), 58)

    def test_parse_multiple_days(self) -> None:
        """Test parsing multiple days in text."""
        line1 = (
            " " * 72
            + "241103TK"
            + "0612162"
            + "9999999" * 3
            + "0015058"
            + "9999999" * 3
        )
        line2 = (
            " " * 72
            + "241104TK"
            + "0712165"
            + "9999999" * 3
            + "0115060"
            + "9999999" * 3
        )
        text = line1 + "\n" + line2

        result = parse_jma_suisan_text(text, "TK")

        assert len(result) == 2
        assert date(2024, 11, 3) in result
        assert date(2024, 11, 4) in result

        daily1 = result[date(2024, 11, 3)]
        assert len(daily1.highs) == 1
        assert daily1.highs[0] == (time(6, 12), 162)

        daily2 = result[date(2024, 11, 4)]
        assert len(daily2.highs) == 1
        assert daily2.highs[0] == (time(7, 12), 165)

    def test_parse_invalid_time_values_skipped(self) -> None:
        """Test parsing skips invalid time values."""
        line = (
            " " * 72
            + "241103TK"
            + "2512162"  # Invalid hour (25)
            + "0661158"  # Invalid minute (61)
            + "9999999" * 2
            + "0015058"
            + "9999999" * 3
        )

        result = parse_jma_suisan_text(line, "TK")

        assert len(result) == 1
        daily = result[date(2024, 11, 3)]
        # Invalid times should be skipped
        assert len(daily.highs) == 0
        assert len(daily.lows) == 1
