"""JMAStation / STATIONS のユニットテスト."""

from fishing_forecast_gcal.infrastructure.jma.stations import (
    STATIONS,
    JMAStation,
    _dms,
)


class TestDms:
    """_dms() helper tests."""

    def test_integer_degrees(self) -> None:
        """Convert whole-degree values."""
        assert _dms(45, 0) == 45.0

    def test_typical_conversion(self) -> None:
        """Convert typical degrees-minutes to decimal degrees.

        45°24' → 45 + 24/60 = 45.4
        """
        assert _dms(45, 24) == 45.4

    def test_rounding(self) -> None:
        """Ensure result rounded to 3 decimal places.

        35°39' → 35 + 39/60 = 35.650
        """
        assert _dms(35, 39) == 35.65

    def test_large_minutes(self) -> None:
        """Convert 59 minutes correctly.

        140°59' → 140 + 59/60 ≈ 140.983
        """
        assert _dms(140, 59) == 140.983

    def test_zero(self) -> None:
        """Handle zero degrees and zero minutes."""
        assert _dms(0, 0) == 0.0


class TestJMAStation:
    """JMAStation dataclass tests."""

    def test_frozen(self) -> None:
        """Ensure JMAStation is frozen (immutable)."""
        station = JMAStation("XX", "テスト", 35.0, 140.0, -100.0)
        with __import__("pytest").raises(AttributeError):
            station.name = "変更"  # type: ignore[misc]

    def test_fields(self) -> None:
        """Ensure all fields are accessible."""
        station = JMAStation("TK", "東京", 35.654, 139.77, -124.9)
        assert station.id == "TK"
        assert station.name == "東京"
        assert station.latitude == 35.654
        assert station.longitude == 139.77
        assert station.ref_level_tp_cm == -124.9


class TestStations:
    """STATIONS dictionary tests."""

    def test_total_count(self) -> None:
        """Verify all 70 JMA stations are defined."""
        assert len(STATIONS) == 70

    def test_all_keys_are_two_chars(self) -> None:
        """All station IDs must be 2 characters."""
        for key in STATIONS:
            assert len(key) == 2, f"Station key '{key}' is not 2 characters"

    def test_key_matches_station_id(self) -> None:
        """Dict key must match JMAStation.id."""
        for key, station in STATIONS.items():
            assert key == station.id, f"Key '{key}' != station.id '{station.id}'"

    def test_all_names_are_nonempty(self) -> None:
        """All station names must be non-empty."""
        for key, station in STATIONS.items():
            assert station.name, f"Station '{key}' has empty name"

    def test_latitude_range(self) -> None:
        """All latitudes within Japan range (24-46)."""
        for key, station in STATIONS.items():
            assert 24.0 <= station.latitude <= 46.0, (
                f"Station '{key}' latitude {station.latitude} out of range"
            )

    def test_longitude_range(self) -> None:
        """All longitudes within Japan range (122-154)."""
        for key, station in STATIONS.items():
            assert 122.0 <= station.longitude <= 154.0, (
                f"Station '{key}' longitude {station.longitude} out of range"
            )

    def test_ref_level_is_negative(self) -> None:
        """All ref_level_tp_cm values should be negative.

        観測基準面の標高は T.P. 基準で全地点マイナス値。
        """
        for key, station in STATIONS.items():
            assert station.ref_level_tp_cm < 0, (
                f"Station '{key}' ref_level_tp_cm {station.ref_level_tp_cm} >= 0"
            )

    # --- 固定値スポットチェック ---

    def test_known_station_tokyo(self) -> None:
        """Verify Tokyo station coordinates.

        東京: 35°39'N, 139°46'E, ref=-188.4 (2026年版)
        """
        tk = STATIONS["TK"]
        assert tk.name == "東京"
        assert tk.latitude == _dms(35, 39)
        assert tk.longitude == _dms(139, 46)
        assert tk.ref_level_tp_cm == -188.4

    def test_known_station_naha(self) -> None:
        """Verify Naha station coordinates.

        那覇: 26°13'N, 127°40'E, ref=-258.0 (2026年版)
        """
        nh = STATIONS["NH"]
        assert nh.name == "那覇"
        assert nh.latitude == _dms(26, 13)
        assert nh.longitude == _dms(127, 40)
        assert nh.ref_level_tp_cm == -258.0

    def test_fixed_fk_is_fukaura(self) -> None:
        """FK must be 深浦, not 福岡 (Issue #70 fix).

        FK / HA 取り違えが修正されていることを検証。
        """
        fk = STATIONS["FK"]
        assert fk.name == "深浦"
        # 深浦は東北地方（北緯40°付近）
        assert fk.latitude > 40.0

    def test_fixed_ha_is_hamada(self) -> None:
        """HA must be 浜田, not 博多 (Issue #70 fix).

        FK / HA 取り違えが修正されていることを検証。
        """
        ha = STATIONS["HA"]
        assert ha.name == "浜田"
        # 浜田は島根県（北緯34°付近）
        assert 34.0 < ha.latitude < 36.0

    def test_unique_names(self) -> None:
        """All station names must be unique."""
        names = [s.name for s in STATIONS.values()]
        assert len(names) == len(set(names)), "Duplicate station names found"

    def test_unique_coordinates(self) -> None:
        """All station coordinates must be unique."""
        coords = [(s.latitude, s.longitude) for s in STATIONS.values()]
        assert len(coords) == len(set(coords)), "Duplicate coordinates found"
