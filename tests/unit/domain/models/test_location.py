"""地点情報モデルのテスト"""

import dataclasses

import pytest

from fishing_forecast_gcal.domain.models.location import Location


class TestLocation:
    """Locationモデルのテスト"""

    def test_create_valid_location(self) -> None:
        """正常な地点情報を作成できること"""
        location = Location(
            id="tokyo_bay",
            name="東京湾",
            latitude=35.6762,
            longitude=139.6503,
            station_id="TK",
        )
        assert location.id == "tokyo_bay"
        assert location.name == "東京湾"
        assert location.latitude == 35.6762
        assert location.longitude == 139.6503
        assert location.station_id == "TK"

    def test_empty_id_raises_error(self) -> None:
        """空のidでエラーが発生すること"""
        with pytest.raises(ValueError, match="id must not be empty"):
            Location(id="", name="東京湾", latitude=35.6762, longitude=139.6503, station_id="TK")

    def test_whitespace_only_id_raises_error(self) -> None:
        """空白のみのidでエラーが発生すること"""
        with pytest.raises(ValueError, match="id must not be empty"):
            Location(
                id="   ",
                name="東京湾",
                latitude=35.6762,
                longitude=139.6503,
                station_id="TK",
            )

    def test_empty_name_raises_error(self) -> None:
        """空のnameでエラーが発生すること"""
        with pytest.raises(ValueError, match="name must not be empty"):
            Location(
                id="tokyo_bay",
                name="",
                latitude=35.6762,
                longitude=139.6503,
                station_id="TK",
            )

    def test_whitespace_only_name_raises_error(self) -> None:
        """空白のみのnameでエラーが発生すること"""
        with pytest.raises(ValueError, match="name must not be empty"):
            Location(
                id="tokyo_bay",
                name="   ",
                latitude=35.6762,
                longitude=139.6503,
                station_id="TK",
            )

    def test_latitude_below_minus_90_raises_error(self) -> None:
        """-90未満の緯度でエラーが発生すること"""
        with pytest.raises(ValueError, match="latitude must be between -90 and 90"):
            Location(
                id="tokyo_bay",
                name="東京湾",
                latitude=-91.0,
                longitude=139.6503,
                station_id="TK",
            )

    def test_latitude_over_90_raises_error(self) -> None:
        """90を超える緯度でエラーが発生すること"""
        with pytest.raises(ValueError, match="latitude must be between -90 and 90"):
            Location(
                id="tokyo_bay",
                name="東京湾",
                latitude=91.0,
                longitude=139.6503,
                station_id="TK",
            )

    def test_longitude_below_minus_180_raises_error(self) -> None:
        """-180未満の経度でエラーが発生すること"""
        with pytest.raises(ValueError, match="longitude must be between -180 and 180"):
            Location(
                id="tokyo_bay",
                name="東京湾",
                latitude=35.6762,
                longitude=-181.0,
                station_id="TK",
            )

    def test_longitude_over_180_raises_error(self) -> None:
        """180を超える経度でエラーが発生すること"""
        with pytest.raises(ValueError, match="longitude must be between -180 and 180"):
            Location(
                id="tokyo_bay",
                name="東京湾",
                latitude=35.6762,
                longitude=181.0,
                station_id="TK",
            )

    def test_latitude_at_boundary_is_valid(self) -> None:
        """緯度の境界値（-90, 90）が有効であること"""
        location_south = Location(
            id="south_pole",
            name="南極",
            latitude=-90.0,
            longitude=0.0,
            station_id="TK",
        )
        assert location_south.latitude == -90.0

        location_north = Location(
            id="north_pole",
            name="北極",
            latitude=90.0,
            longitude=0.0,
            station_id="TK",
        )
        assert location_north.latitude == 90.0

    def test_longitude_at_boundary_is_valid(self) -> None:
        """経度の境界値（-180, 180）が有効であること"""
        location_west = Location(
            id="west_edge",
            name="西端",
            latitude=0.0,
            longitude=-180.0,
            station_id="TK",
        )
        assert location_west.longitude == -180.0

        location_east = Location(
            id="east_edge",
            name="東端",
            latitude=0.0,
            longitude=180.0,
            station_id="TK",
        )
        assert location_east.longitude == 180.0

    def test_location_is_immutable(self) -> None:
        """Locationが不変であること"""
        location = Location(
            id="tokyo_bay",
            name="東京湾",
            latitude=35.6762,
            longitude=139.6503,
            station_id="TK",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            location.name = "相模湾"  # type: ignore

    def test_empty_station_id_raises_error(self) -> None:
        """空のstation_idでエラーが発生すること"""
        with pytest.raises(ValueError, match="station_id must not be empty"):
            Location(
                id="tokyo_bay",
                name="東京湾",
                latitude=35.6762,
                longitude=139.6503,
                station_id="",
            )

    def test_whitespace_only_station_id_raises_error(self) -> None:
        """空白のみのstation_idでエラーが発生すること"""
        with pytest.raises(ValueError, match="station_id must not be empty"):
            Location(
                id="tokyo_bay",
                name="東京湾",
                latitude=35.6762,
                longitude=139.6503,
                station_id="   ",
            )
