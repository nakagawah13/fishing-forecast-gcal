"""harmonic_analysis モジュールのユニットテスト."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest

from fishing_forecast_gcal.infrastructure.jma.harmonic_analysis import (
    JMA_OBS_URL_TEMPLATE,
    fetch_monthly_data,
    run_harmonic_analysis,
)

JST = timezone(timedelta(hours=9))


def _make_observation_data(
    n_points: int = 720,
) -> list[tuple[datetime, float]]:
    """Generate synthetic observation data for testing.

    テスト用に合成潮位データを生成します (30日分, 毎時)。

    Args:
        n_points: Number of hourly data points.
                  (データポイント数)

    Returns:
        List of (datetime, height_cm) pairs.
        (時刻と潮位のペアリスト)
    """
    base = datetime(2025, 1, 1, 0, 0, 0, tzinfo=JST)
    data: list[tuple[datetime, float]] = []
    for i in range(n_points):
        dt = base + timedelta(hours=i)
        # M2 分潮風の周期性を持つ合成データ
        height = 120.0 + 72.5 * np.cos(2 * np.pi * i / 12.42)
        data.append((dt, float(height)))
    return data


class TestFetchMonthlyData:
    """fetch_monthly_data() tests."""

    def test_url_construction(self) -> None:
        """Verify URL template produces correct URL."""
        url = JMA_OBS_URL_TEMPLATE.format(year=2025, month=6, station="TK")
        assert "2025" in url
        assert "202506" in url
        assert "TK" in url
        assert url.startswith("https://www.data.jma.go.jp/")

    def test_successful_fetch(self) -> None:
        """fetch_monthly_data returns text on successful HTTP call."""
        mock_response = MagicMock()
        mock_response.text = "dummy text data"
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        result = fetch_monthly_data("TK", 2025, 6, mock_client)
        assert result == "dummy text data"
        mock_client.get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    def test_http_error_propagates(self) -> None:
        """HTTP errors from JMA should propagate."""
        import httpx

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            fetch_monthly_data("XX", 2025, 1, mock_client)


class TestRunHarmonicAnalysis:
    """run_harmonic_analysis() tests."""

    def test_insufficient_data_raises(self, tmp_path: Path) -> None:
        """Raise ValueError when observation data < 168 points."""
        short_data = _make_observation_data(n_points=100)
        output = tmp_path / "coef.pkl"

        with pytest.raises(ValueError, match="168"):
            run_harmonic_analysis(short_data, 35.65, output)

    def test_successful_analysis_creates_pickle(self, tmp_path: Path) -> None:
        """Verify pickle file is created on successful analysis."""
        obs_data = _make_observation_data(n_points=720)
        output = tmp_path / "harmonics" / "test.pkl"

        coef = run_harmonic_analysis(obs_data, 35.65, output)

        assert output.exists()
        assert "name" in coef
        assert "mean" in coef
        assert len(coef["name"]) > 0

    def test_output_directory_created(self, tmp_path: Path) -> None:
        """Parent directories should be automatically created."""
        obs_data = _make_observation_data(n_points=720)
        output = tmp_path / "deep" / "nested" / "coef.pkl"

        run_harmonic_analysis(obs_data, 35.65, output)
        assert output.exists()

    def test_pickle_loadable(self, tmp_path: Path) -> None:
        """Saved pickle should be loadable and contain valid coefficients."""
        import pickle

        obs_data = _make_observation_data(n_points=720)
        output = tmp_path / "coef.pkl"

        run_harmonic_analysis(obs_data, 35.65, output)

        with open(output, "rb") as f:
            loaded: dict[str, Any] = pickle.load(f)  # noqa: S301

        assert "name" in loaded
        assert "A" in loaded
        assert isinstance(loaded["mean"], float)
