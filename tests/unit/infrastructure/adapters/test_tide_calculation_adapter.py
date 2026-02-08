"""TideCalculationAdapter のユニットテスト"""

import pickle
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest
import utide

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.infrastructure.adapters.tide_calculation_adapter import (
    TideCalculationAdapter,
    generate_harmonics,
)

JST = ZoneInfo("Asia/Tokyo")


def _create_sample_coefficients(
    latitude: float = 35.654,
) -> dict[str, Any]:
    """Generate sample harmonic coefficients for testing.

    合成潮汐データからUTide solve()で調和解析を行い、
    完全なcoefオブジェクトを返します。
    """
    np.random.seed(42)

    # 1年分の合成潮汐データ（1時間刻み）
    times = pd.date_range("2025-01-01", "2026-01-01", freq="h", tz="Asia/Tokyo")
    hours = np.arange(len(times), dtype=float)

    # 主要4分潮による合成潮位
    heights = (
        72.5 * np.cos(2 * np.pi * hours / 12.42 + np.radians(145.2))  # M2
        + 28.3 * np.cos(2 * np.pi * hours / 12.0 + np.radians(178.5))  # S2
        + 18.6 * np.cos(2 * np.pi * hours / 23.93 + np.radians(298.7))  # K1
        + 12.4 * np.cos(2 * np.pi * hours / 25.82 + np.radians(265.4))  # O1
        + 120.0  # 平均潮位（オフセット）
        + np.random.normal(0, 2, len(times))  # ノイズ
    )

    coef: dict[str, Any] = utide.solve(
        times.to_numpy(),
        heights,
        lat=latitude,
        verbose=False,
    )
    return coef


@pytest.fixture
def sample_coef() -> dict[str, Any]:
    """Return sample harmonic coefficients."""
    return _create_sample_coefficients()


@pytest.fixture
def harmonics_dir(tmp_path: Path, sample_coef: dict[str, Any]) -> Path:
    """Return a tmp directory with a harmonic coefficient pickle file."""
    harmonics_path = tmp_path / "harmonics"
    harmonics_path.mkdir()

    # tokyo_bay.pkl を作成
    with open(harmonics_path / "tokyo_bay.pkl", "wb") as f:
        pickle.dump(sample_coef, f)

    return harmonics_path


@pytest.fixture
def tokyo_bay_location() -> Location:
    """Return a test Location for Tokyo Bay."""
    return Location(
        id="tokyo_bay",
        name="東京湾",
        latitude=35.654,
        longitude=139.7795,
        station_id="tokyo_bay",
    )


class TestTideCalculationAdapterInit:
    """TideCalculationAdapter.__init__ のテスト."""

    def test_init_with_valid_dir(self, harmonics_dir: Path) -> None:
        """有効なディレクトリで初期化できること."""
        adapter = TideCalculationAdapter(harmonics_dir)
        assert adapter.harmonics_dir == harmonics_dir

    def test_init_with_nonexistent_dir(self, tmp_path: Path) -> None:
        """存在しないディレクトリで FileNotFoundError が発生すること."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(FileNotFoundError, match="調和定数ディレクトリが見つかりません"):
            TideCalculationAdapter(nonexistent)

    def test_init_with_file_path(self, tmp_path: Path) -> None:
        """ファイルパスで NotADirectoryError が発生すること."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("dummy")
        with pytest.raises(NotADirectoryError, match="パスがディレクトリではありません"):
            TideCalculationAdapter(file_path)


class TestCalculateTide:
    """TideCalculationAdapter.calculate_tide のテスト."""

    def test_returns_expected_data_points(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """分単位のデータポイント数を返すこと."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))

        expected_points = (24 * 60) // adapter.PREDICTION_INTERVAL_MINUTES + 2
        assert len(result) == expected_points

    def test_returns_timezone_aware_datetimes(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """タイムゾーン付きのdatetimeを返すこと."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))

        for dt, _height in result:
            assert dt.tzinfo is not None

    def test_returns_minute_intervals(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """分単位の時刻間隔を返すこと."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))

        for i in range(1, len(result)):
            diff = (result[i][0] - result[i - 1][0]).total_seconds()
            assert diff == adapter.PREDICTION_INTERVAL_MINUTES * 60

    def test_includes_non_zero_minutes(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """分が00固定にならないこと."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))

        assert any(dt.minute != 0 for dt, _height in result)

    def test_starts_at_midnight_jst(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """日付境界の補助点を含むこと."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))

        first_dt = result[0][0]
        interval_minutes = adapter.PREDICTION_INTERVAL_MINUTES
        expected_start = datetime(2026, 2, 8, 0, 0, tzinfo=JST) - timedelta(
            minutes=interval_minutes
        )
        assert first_dt == expected_start

        midnight_dt = result[1][0]
        assert midnight_dt.hour == 0
        assert midnight_dt.minute == 0

    def test_heights_are_realistic(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """潮位が現実的な範囲にあること（-100cm ～ 500cm）."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))

        for _dt, height in result:
            assert -100.0 <= height <= 500.0, f"Unrealistic height: {height}"

    def test_heights_vary(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """潮位が1日の中で変動すること（定数ではない）."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))

        heights = [h for _, h in result]
        assert max(heights) - min(heights) > 10.0  # 最低10cm以上の変動

    def test_different_dates_produce_different_results(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """異なる日付で異なる結果を返すこと."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result_day1 = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))
        result_day2 = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 15))

        heights_day1 = [h for _, h in result_day1]
        heights_day2 = [h for _, h in result_day2]

        # 7日離れた日で完全に同じ結果にはならない
        assert heights_day1 != heights_day2

    def test_past_date_works(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """過去の日付でも計算可能であること."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result = adapter.calculate_tide(tokyo_bay_location, date(2020, 1, 1))

        expected_points = (24 * 60) // adapter.PREDICTION_INTERVAL_MINUTES + 2
        assert len(result) == expected_points

    def test_future_date_works(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """未来の日付でも計算可能であること."""
        adapter = TideCalculationAdapter(harmonics_dir)
        result = adapter.calculate_tide(tokyo_bay_location, date(2030, 12, 31))

        expected_points = (24 * 60) // adapter.PREDICTION_INTERVAL_MINUTES + 2
        assert len(result) == expected_points

    def test_unknown_location_raises_file_not_found(
        self,
        harmonics_dir: Path,
    ) -> None:
        """未知の地点IDで FileNotFoundError が発生すること."""
        adapter = TideCalculationAdapter(harmonics_dir)
        unknown_location = Location(
            id="unknown_bay",
            name="未知の湾",
            latitude=35.0,
            longitude=139.0,
            station_id="unknown_bay",
        )

        with pytest.raises(FileNotFoundError, match="調和定数ファイルが見つかりません"):
            adapter.calculate_tide(unknown_location, date(2026, 2, 8))


class TestCoefficientsCache:
    """調和定数キャッシュのテスト."""

    def test_caches_coefficients(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """2回目以降の呼び出しでキャッシュが使用されること."""
        adapter = TideCalculationAdapter(harmonics_dir)

        # 1回目：ファイルから読み込み
        adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))
        assert "tokyo_bay" in adapter._coef_cache  # noqa: SLF001

        # pickleファイルを削除しても2回目は成功（キャッシュ使用）
        (harmonics_dir / "tokyo_bay.pkl").unlink()
        result = adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 9))
        expected_points = (24 * 60) // adapter.PREDICTION_INTERVAL_MINUTES + 2
        assert len(result) == expected_points

    def test_clear_cache(
        self,
        harmonics_dir: Path,
        tokyo_bay_location: Location,
    ) -> None:
        """clear_cache でキャッシュがクリアされること."""
        adapter = TideCalculationAdapter(harmonics_dir)
        adapter.calculate_tide(tokyo_bay_location, date(2026, 2, 8))

        assert len(adapter._coef_cache) > 0  # noqa: SLF001
        adapter.clear_cache()
        assert len(adapter._coef_cache) == 0  # noqa: SLF001


class TestLoadCoefficientsValidation:
    """調和定数ファイルのバリデーションテスト."""

    def test_corrupted_pickle_raises_runtime_error(self, tmp_path: Path) -> None:
        """破損したpickleファイルで RuntimeError が発生すること."""
        harmonics_path = tmp_path / "harmonics"
        harmonics_path.mkdir()

        # 不正なpickleデータを書き込み
        with open(harmonics_path / "broken.pkl", "wb") as f:
            f.write(b"not a valid pickle data")

        adapter = TideCalculationAdapter(harmonics_path)
        location = Location(
            id="broken",
            name="壊れたデータ",
            latitude=35.0,
            longitude=139.0,
            station_id="broken",
        )

        with pytest.raises(RuntimeError, match="調和定数ファイルの読み込みに失敗しました"):
            adapter.calculate_tide(location, date(2026, 2, 8))

    def test_incomplete_coef_raises_runtime_error(self, tmp_path: Path) -> None:
        """必須フィールドが不足したcoefで RuntimeError が発生すること."""
        harmonics_path = tmp_path / "harmonics"
        harmonics_path.mkdir()

        # 必須フィールドが欠落した辞書を保存
        incomplete_coef = {"name": ["M2"], "A": [72.5]}
        with open(harmonics_path / "incomplete.pkl", "wb") as f:
            pickle.dump(incomplete_coef, f)

        adapter = TideCalculationAdapter(harmonics_path)
        location = Location(
            id="incomplete",
            name="不完全データ",
            latitude=35.0,
            longitude=139.0,
            station_id="incomplete",
        )

        with pytest.raises(RuntimeError, match="必須フィールドが不足しています"):
            adapter.calculate_tide(location, date(2026, 2, 8))


class TestGenerateHarmonics:
    """generate_harmonics 関数のテスト."""

    def test_generates_pickle_file(self, tmp_path: Path) -> None:
        """pickleファイルが正常に生成されること."""
        np.random.seed(42)

        # 1ヶ月分の合成データ（最低要件以上）
        times = pd.date_range("2025-01-01", periods=720, freq="h", tz="Asia/Tokyo")
        hours = np.arange(len(times), dtype=float)
        heights = (
            72.5 * np.cos(2 * np.pi * hours / 12.42)
            + 28.3 * np.cos(2 * np.pi * hours / 12.0)
            + 120.0
            + np.random.normal(0, 2, len(times))
        )

        output_path = tmp_path / "harmonics" / "test_location.pkl"

        generate_harmonics(
            observed_times=times.to_numpy(),
            observed_heights=heights,
            latitude=35.654,
            output_path=output_path,
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_generated_file_is_usable(self, tmp_path: Path) -> None:
        """生成されたpickleがTideCalculationAdapterで使用可能なこと."""
        np.random.seed(42)

        times = pd.date_range("2025-01-01", periods=720, freq="h", tz="Asia/Tokyo")
        hours = np.arange(len(times), dtype=float)
        heights = (
            72.5 * np.cos(2 * np.pi * hours / 12.42)
            + 28.3 * np.cos(2 * np.pi * hours / 12.0)
            + 120.0
            + np.random.normal(0, 2, len(times))
        )

        harmonics_path = tmp_path / "harmonics"
        output_path = harmonics_path / "generated_bay.pkl"

        generate_harmonics(
            observed_times=times.to_numpy(),
            observed_heights=heights,
            latitude=35.654,
            output_path=output_path,
        )

        # 生成結果を使って予測
        adapter = TideCalculationAdapter(harmonics_path)
        location = Location(
            id="generated_bay",
            name="生成テスト",
            latitude=35.654,
            longitude=139.78,
            station_id="generated_bay",
        )
        result = adapter.calculate_tide(location, date(2026, 2, 8))

        expected_points = (24 * 60) // adapter.PREDICTION_INTERVAL_MINUTES + 2
        assert len(result) == expected_points

    def test_insufficient_data_raises_value_error(self, tmp_path: Path) -> None:
        """データ不足で ValueError が発生すること."""
        # 1週間未満（100点のみ）
        times = pd.date_range("2025-01-01", periods=100, freq="h", tz="Asia/Tokyo")
        heights = np.random.normal(120, 50, len(times))

        output_path = tmp_path / "harmonics" / "insufficient.pkl"

        with pytest.raises(ValueError, match="観測データが不足しています"):
            generate_harmonics(
                observed_times=times.to_numpy(),
                observed_heights=heights,
                latitude=35.654,
                output_path=output_path,
            )

    def test_mismatched_array_lengths_raises_value_error(self, tmp_path: Path) -> None:
        """配列長の不一致で ValueError が発生すること."""
        times = pd.date_range("2025-01-01", periods=720, freq="h", tz="Asia/Tokyo")
        heights = np.random.normal(120, 50, 500)  # 異なる長さ

        output_path = tmp_path / "harmonics" / "mismatched.pkl"

        with pytest.raises(ValueError, match="配列長が一致しません"):
            generate_harmonics(
                observed_times=times.to_numpy(),
                observed_heights=heights,
                latitude=35.654,
                output_path=output_path,
            )

    def test_invalid_latitude_raises_value_error(self, tmp_path: Path) -> None:
        """不正な緯度で ValueError が発生すること."""
        times = pd.date_range("2025-01-01", periods=720, freq="h", tz="Asia/Tokyo")
        heights = np.random.normal(120, 50, len(times))

        output_path = tmp_path / "harmonics" / "invalid_lat.pkl"

        with pytest.raises(ValueError, match="緯度が範囲外です"):
            generate_harmonics(
                observed_times=times.to_numpy(),
                observed_heights=heights,
                latitude=100.0,  # 範囲外
                output_path=output_path,
            )
