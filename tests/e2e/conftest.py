"""E2E test configuration and shared fixtures.

E2Eテスト用の共有フィクスチャを定義します。
テスト実行には以下の環境設定が必要です:

- 環境変数 ``E2E_CALENDAR_ID``: テスト専用 Google Calendar ID
- ``config/credentials.json``: OAuth クライアント情報
- ``config/token.json``: OAuth トークン（初回認証後に生成）
- ``config/harmonics/tk.pkl``: 東京の調和定数データ
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.infrastructure.clients.google_calendar_client import (
    GoogleCalendarClient,
)

# プロジェクトルートの参照
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _require_env(name: str) -> str:
    """環境変数を取得し、未設定ならスキップ"""
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"Environment variable {name} is required for E2E tests")
    return value


def _require_file(path: Path, description: str) -> Path:
    """ファイルの存在を確認し、なければスキップ"""
    if not path.exists():
        pytest.skip(f"{description} not found: {path}")
    return path


@pytest.fixture(scope="module")
def e2e_calendar_id() -> str:
    """テスト専用の Google Calendar ID を取得

    ``E2E_CALENDAR_ID`` 環境変数が未設定の場合はスキップされます。
    """
    return _require_env("E2E_CALENDAR_ID")


@pytest.fixture(scope="module")
def credentials_path() -> Path:
    """OAuth クライアント情報ファイルのパスを取得"""
    return _require_file(
        PROJECT_ROOT / "config" / "credentials.json",
        "OAuth credentials file",
    )


@pytest.fixture(scope="module")
def token_path() -> Path:
    """OAuth トークンファイルのパスを取得"""
    return _require_file(
        PROJECT_ROOT / "config" / "token.json",
        "OAuth token file",
    )


@pytest.fixture(scope="module")
def harmonics_dir() -> Path:
    """調和定数ディレクトリのパスを取得"""
    path = PROJECT_ROOT / "config" / "harmonics"
    return _require_file(path, "Harmonics directory")


@pytest.fixture(scope="module")
def tk_harmonics(harmonics_dir: Path) -> Path:
    """東京（TK）の調和定数ファイルを取得"""
    return _require_file(harmonics_dir / "tk.pkl", "Tokyo harmonics file (tk.pkl)")


@pytest.fixture(scope="module")
def tokyo_location() -> Location:
    """東京地点のテスト用 Location"""
    return Location(
        id="tk",
        name="東京",
        latitude=35.650,
        longitude=139.770,
    )


@pytest.fixture(scope="module")
def calendar_client(
    credentials_path: Path,
    token_path: Path,
) -> GoogleCalendarClient:
    """認証済みの GoogleCalendarClient を返す"""
    client = GoogleCalendarClient(
        credentials_path=str(credentials_path),
        token_path=str(token_path),
    )
    client.authenticate()
    return client


@pytest.fixture(scope="module")
def temp_config_file(
    e2e_calendar_id: str,
    credentials_path: Path,
    token_path: Path,
) -> Iterator[Path]:
    """テスト用の一時設定ファイルを生成

    E2Eテスト用に ``config.yaml`` をテンポラリファイルとして作成します。
    テスト終了後に自動削除されます。
    """
    config = {
        "settings": {
            "timezone": "Asia/Tokyo",
            "update_interval_hours": 3,
            "forecast_window_days": 7,
            "tide_register_months": 1,
            "high_priority_hours": [4, 5, 6, 7, 20, 21, 22, 23],
            "google_credentials_path": str(credentials_path),
            "google_token_path": str(token_path),
            "calendar_id": e2e_calendar_id,
        },
        "locations": [
            {
                "id": "tk",
                "name": "東京",
                "latitude": 35.650,
                "longitude": 139.770,
                "port_code": "TK",
            },
        ],
        "fishing_conditions": {
            "prime_time_offset_hours": 2,
            "max_wind_speed_ms": 10,
            "preferred_tide_types": ["大潮", "中潮"],
        },
    }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        prefix="e2e_config_",
        delete=False,
    ) as f:
        yaml.dump(config, f, allow_unicode=True)
        config_path = Path(f.name)

    yield config_path

    # クリーンアップ
    config_path.unlink(missing_ok=True)
