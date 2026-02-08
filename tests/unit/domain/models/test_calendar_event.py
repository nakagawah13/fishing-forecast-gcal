"""カレンダーイベントモデルのテスト"""

import dataclasses
import hashlib
from datetime import date

import pytest

from fishing_forecast_gcal.domain.models.calendar_event import CalendarEvent


class TestCalendarEvent:
    """CalendarEventモデルのテスト"""

    def test_create_valid_calendar_event(self) -> None:
        """正常なカレンダーイベントを作成できること"""
        description = """[TIDE]
- 満潮: 06:12 (162cm)
- 干潮: 12:34 (58cm)

[FORECAST]
- 風速: 5m/s

[NOTES]
メモ
"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description=description,
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        assert event.event_id == "test_event_123"
        assert event.title == "潮汐 東京湾 (大潮)"
        assert event.date == date(2026, 2, 8)
        assert event.location_id == "tokyo_bay"

    def test_empty_event_id_raises_error(self) -> None:
        """空のevent_idでエラーが発生すること"""
        with pytest.raises(ValueError, match="event_id must not be empty"):
            CalendarEvent(
                event_id="",
                title="潮汐 東京湾 (大潮)",
                description="test",
                date=date(2026, 2, 8),
                location_id="tokyo_bay",
            )

    def test_whitespace_only_event_id_raises_error(self) -> None:
        """空白のみのevent_idでエラーが発生すること"""
        with pytest.raises(ValueError, match="event_id must not be empty"):
            CalendarEvent(
                event_id="   ",
                title="潮汐 東京湾 (大潮)",
                description="test",
                date=date(2026, 2, 8),
                location_id="tokyo_bay",
            )

    def test_empty_title_raises_error(self) -> None:
        """空のtitleでエラーが発生すること"""
        with pytest.raises(ValueError, match="title must not be empty"):
            CalendarEvent(
                event_id="test_event_123",
                title="",
                description="test",
                date=date(2026, 2, 8),
                location_id="tokyo_bay",
            )

    def test_title_over_50_chars_raises_error(self) -> None:
        """50文字を超えるtitleでエラーが発生すること"""
        long_title = "a" * 51
        with pytest.raises(ValueError, match="title must be 50 characters or less"):
            CalendarEvent(
                event_id="test_event_123",
                title=long_title,
                description="test",
                date=date(2026, 2, 8),
                location_id="tokyo_bay",
            )

    def test_title_at_50_chars_is_valid(self) -> None:
        """50文字のtitleが有効であること"""
        title_50 = "a" * 50
        event = CalendarEvent(
            event_id="test_event_123",
            title=title_50,
            description="test",
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        assert len(event.title) == 50

    def test_empty_location_id_raises_error(self) -> None:
        """空のlocation_idでエラーが発生すること"""
        with pytest.raises(ValueError, match="location_id must not be empty"):
            CalendarEvent(
                event_id="test_event_123",
                title="潮汐 東京湾 (大潮)",
                description="test",
                date=date(2026, 2, 8),
                location_id="",
            )

    def test_has_valid_sections_with_all_sections(self) -> None:
        """全セクションが存在する場合、has_valid_sectionsがTrueを返すこと"""
        description = """[TIDE]
- 満潮: 06:12 (162cm)

[FORECAST]
- 風速: 5m/s

[NOTES]
メモ
"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description=description,
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        assert event.has_valid_sections() is True

    def test_has_valid_sections_with_missing_section(self) -> None:
        """セクションが欠落している場合、has_valid_sectionsがFalseを返すこと"""
        description = """[TIDE]
- 満潮: 06:12 (162cm)

[FORECAST]
- 風速: 5m/s
"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description=description,
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        assert event.has_valid_sections() is False

    def test_extract_section_tide(self) -> None:
        """TIDEセクションを正しく抽出できること"""
        description = """[TIDE]
- 満潮: 06:12 (162cm)
- 干潮: 12:34 (58cm)

[FORECAST]
- 風速: 5m/s

[NOTES]
メモ
"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description=description,
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        tide_section = event.extract_section("TIDE")
        assert tide_section is not None
        assert "満潮: 06:12 (162cm)" in tide_section
        assert "干潮: 12:34 (58cm)" in tide_section

    def test_extract_section_forecast(self) -> None:
        """FORECASTセクションを正しく抽出できること"""
        description = """[TIDE]
- 満潮: 06:12 (162cm)

[FORECAST]
- 風速: 5m/s
- 風向: 北

[NOTES]
メモ
"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description=description,
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        forecast_section = event.extract_section("FORECAST")
        assert forecast_section is not None
        assert "風速: 5m/s" in forecast_section
        assert "風向: 北" in forecast_section

    def test_extract_section_notes(self) -> None:
        """NOTESセクションを正しく抽出できること"""
        description = """[TIDE]
- 満潮: 06:12 (162cm)

[FORECAST]
- 風速: 5m/s

[NOTES]
手動メモ
"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description=description,
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        notes_section = event.extract_section("NOTES")
        assert notes_section is not None
        assert "手動メモ" in notes_section

    def test_extract_section_non_existent(self) -> None:
        """存在しないセクションを抽出するとNoneを返すこと"""
        description = """[TIDE]
- 満潮: 06:12 (162cm)
"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description=description,
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        section = event.extract_section("NONEXISTENT")
        assert section is None

    def test_update_section_forecast(self) -> None:
        """FORECASTセクションを更新できること"""
        description = """[TIDE]
- 満潮: 06:12 (162cm)

[FORECAST]
- 風速: 5m/s

[NOTES]
メモ
"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description=description,
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )

        new_forecast = "- 風速: 10m/s\n- 風向: 南"
        updated_event = event.update_section("FORECAST", new_forecast)

        # 元のイベントは変更されていない（不変性）
        assert "風速: 5m/s" in event.description

        # 新しいイベントは更新されている
        forecast_section = updated_event.extract_section("FORECAST")
        assert forecast_section is not None
        assert "風速: 10m/s" in forecast_section
        assert "風向: 南" in forecast_section

        # 他のセクションは保持されている
        assert "[TIDE]" in updated_event.description
        assert "[NOTES]" in updated_event.description

    def test_update_section_non_existent_raises_error(self) -> None:
        """存在しないセクションを更新しようとするとエラーが発生すること"""
        description = """[TIDE]
- 満潮: 06:12 (162cm)
"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description=description,
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )

        with pytest.raises(ValueError, match="Section \\[FORECAST\\] does not exist"):
            event.update_section("FORECAST", "新しい内容")

    def test_calendar_event_is_immutable(self) -> None:
        """CalendarEventが不変であること"""
        event = CalendarEvent(
            event_id="test_event_123",
            title="潮汐 東京湾 (大潮)",
            description="test",
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.title = "新しいタイトル"  # type: ignore


class TestCalendarEventGenerateEventId:
    """CalendarEvent.generate_event_id のテスト"""

    def test_generate_event_id_idempotent(self) -> None:
        """同じ入力から同じIDが生成される（冪等性）"""
        location_id = "yokosuka"
        target_date = date(2026, 2, 8)

        id1 = CalendarEvent.generate_event_id(location_id, target_date)
        id2 = CalendarEvent.generate_event_id(location_id, target_date)

        assert id1 == id2

    def test_generate_event_id_different_dates(self) -> None:
        """異なる日付から異なるIDが生成される"""
        location_id = "yokosuka"

        id1 = CalendarEvent.generate_event_id(location_id, date(2026, 2, 8))
        id2 = CalendarEvent.generate_event_id(location_id, date(2026, 2, 9))

        assert id1 != id2

    def test_generate_event_id_different_locations(self) -> None:
        """異なる地点から異なるIDが生成される"""
        target_date = date(2026, 2, 8)

        id1 = CalendarEvent.generate_event_id("yokosuka", target_date)
        id2 = CalendarEvent.generate_event_id("tokyo_bay", target_date)

        assert id1 != id2

    def test_generate_event_id_format(self) -> None:
        """Google Calendar API 制約に準拠した形式であること"""
        event_id = CalendarEvent.generate_event_id("yokosuka", date(2026, 2, 8))

        # MD5ハッシュは32文字
        assert len(event_id) == 32

        # 英数字のみ（16進数）
        assert event_id.isalnum()

        # Google Calendar APIの制約（5-1024文字）に準拠
        assert 5 <= len(event_id) <= 1024

    def test_generate_event_id_matches_md5(self) -> None:
        """生成されるIDがMD5ハッシュと一致"""
        location_id = "yokosuka"
        target_date = date(2026, 2, 8)

        event_id = CalendarEvent.generate_event_id(location_id, target_date)

        source = f"{location_id}_{target_date.isoformat()}"
        expected_id = hashlib.md5(source.encode("utf-8")).hexdigest()

        assert event_id == expected_id
