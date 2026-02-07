"""Tide calculation adapter using UTide library.

This module wraps the UTide library to provide tidal predictions
based on harmonic constants derived from observed tidal data.

UTideライブラリをラップし、調和定数に基づく潮汐予測を提供します。
調和定数はUTideのsolve()による解析結果をpickleで保存したものを使用します。
"""

import logging
import pickle
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import utide

from fishing_forecast_gcal.domain.models.location import Location

logger = logging.getLogger(__name__)

# UTide coef の型エイリアス（utide.utilities.Bunch は辞書ライクなオブジェクト）
type UTideCoefficients = dict[str, Any]


class TideCalculationAdapter:
    """Tide calculation adapter using UTide harmonic analysis.

    UTideライブラリの調和定数を使用して潮汐予測を実行するアダプター。
    調和定数はpickleファイルとして保存され、地点ID（location_id）で管理されます。

    Attributes:
        harmonics_dir (Path): Directory containing harmonic coefficient files.
                              (調和定数ファイルの格納ディレクトリ)
    """

    # 予測間隔（分単位）
    PREDICTION_INTERVAL_MINUTES = 60

    # 予測に使用するpickleファイルの拡張子
    HARMONICS_FILE_EXTENSION = ".pkl"

    def __init__(self, harmonics_dir: Path) -> None:
        """Initialize adapter with harmonics directory path.

        Args:
            harmonics_dir (Path): Path to directory containing harmonic
                                  coefficient pickle files.
                                  (調和定数pickleファイルの格納ディレクトリ)

        Raises:
            FileNotFoundError: If harmonics_dir does not exist.
                               (ディレクトリが存在しない場合)
        """
        if not harmonics_dir.exists():
            raise FileNotFoundError(f"調和定数ディレクトリが見つかりません: {harmonics_dir}")
        if not harmonics_dir.is_dir():
            raise NotADirectoryError(f"パスがディレクトリではありません: {harmonics_dir}")
        self._harmonics_dir = harmonics_dir
        self._coef_cache: dict[str, UTideCoefficients] = {}

    @property
    def harmonics_dir(self) -> Path:
        """Return the harmonics directory path."""
        return self._harmonics_dir

    def calculate_tide(
        self,
        location: Location,
        target_date: date,
    ) -> list[tuple[datetime, float]]:
        """Calculate tidal heights for a given location and date.

        指定した地点・日付の潮汐予測を1時間刻みで実行し、
        (時刻, 潮位cm) のリストを返します。

        Args:
            location (Location): Target location with id, lat, lon.
                                 (対象地点情報)
            target_date (date): Target date for prediction.
                                (予測対象日)

        Returns:
            list[tuple[datetime, float]]: List of (timezone-aware datetime, height_cm)
                tuples at hourly intervals (24 data points).
                (時刻と潮位cmのタプルリスト、1時間刻み24データポイント)

        Raises:
            FileNotFoundError: If harmonic coefficient file for the location
                               is not found.
                               (地点の調和定数ファイルが見つからない場合)
            RuntimeError: If tidal prediction fails.
                          (潮汐予測の計算に失敗した場合)
        """
        # 調和定数を読み込み（キャッシュあり）
        coef = self._load_coefficients(location.id)

        # 予測時刻の生成（JST、1時間刻み、24時間分）
        predict_times = pd.date_range(
            start=pd.Timestamp(target_date, tz="Asia/Tokyo"),
            periods=24,
            freq=f"{self.PREDICTION_INTERVAL_MINUTES}min",
        )

        try:
            # UTide reconstruct で潮汐予測を実行
            prediction = utide.reconstruct(
                predict_times.to_numpy(),
                coef,  # type: ignore[arg-type]
            )
        except Exception as e:
            raise RuntimeError(
                f"潮汐予測の計算に失敗しました (地点: {location.id}, 日付: {target_date}): {e}"
            ) from e

        # 結果をリストに変換
        tide_heights: np.ndarray[Any, np.dtype[np.floating[Any]]] = prediction.h
        mean_height: float = float(coef.get("mean", 0.0))

        result: list[tuple[datetime, float]] = []
        for timestamp, height in zip(predict_times, tide_heights, strict=True):
            # UTideの出力は平均値からの偏差なので、平均潮位を加算
            absolute_height = float(height) + mean_height
            aware_dt: datetime = timestamp.to_pydatetime()
            result.append((aware_dt, absolute_height))

        logger.info(
            "潮汐予測完了: 地点=%s, 日付=%s, データ数=%d",
            location.id,
            target_date,
            len(result),
        )

        return result

    def _load_coefficients(self, location_id: str) -> UTideCoefficients:
        """Load harmonic coefficients from pickle file with caching.

        調和定数をpickleファイルから読み込みます。
        一度読み込んだ調和定数はキャッシュに保持し、再利用します。

        Args:
            location_id (str): Location identifier matching the pickle filename.
                               (pickleファイル名に対応する地点ID)

        Returns:
            UTideCoefficients: UTide harmonic coefficients (Bunch object).
                               (UTide調和定数オブジェクト)

        Raises:
            FileNotFoundError: If the pickle file does not exist.
                               (pickleファイルが存在しない場合)
            RuntimeError: If the pickle file is corrupted or has invalid format.
                          (pickleファイルが破損・不正な場合)
        """
        # キャッシュチェック
        if location_id in self._coef_cache:
            logger.debug("キャッシュから調和定数を取得: %s", location_id)
            return self._coef_cache[location_id]

        # ファイルパスの構築
        coef_path = self._harmonics_dir / f"{location_id}{self.HARMONICS_FILE_EXTENSION}"

        if not coef_path.exists():
            raise FileNotFoundError(
                f"調和定数ファイルが見つかりません: {coef_path}. "
                f"地点 '{location_id}' の調和解析を事前に実行してください。"
            )

        try:
            with open(coef_path, "rb") as f:
                coef: UTideCoefficients = pickle.load(f)  # noqa: S301
        except (pickle.UnpicklingError, EOFError, ModuleNotFoundError) as e:
            raise RuntimeError(f"調和定数ファイルの読み込みに失敗しました: {coef_path}: {e}") from e

        # 最低限の妥当性チェック
        self._validate_coefficients(coef, location_id)

        # キャッシュに保持
        self._coef_cache[location_id] = coef
        logger.info(
            "調和定数を読み込みました: 地点=%s, 分潮数=%d",
            location_id,
            len(coef.get("name", [])),
        )

        return coef

    def _validate_coefficients(
        self,
        coef: UTideCoefficients,
        location_id: str,
    ) -> None:
        """Validate that loaded coefficients have required fields.

        読み込んだ調和定数にreconstructに必要なフィールドが含まれているか検証します。

        Args:
            coef (UTideCoefficients): Loaded coefficient data.
                                      (読み込まれた調和定数)
            location_id (str): Location identifier for error messages.
                               (エラーメッセージ用の地点ID)

        Raises:
            RuntimeError: If required fields are missing.
                          (必須フィールドが欠落している場合)
        """
        required_keys = ("name", "A", "g", "aux", "mean")
        missing = [k for k in required_keys if k not in coef]
        if missing:
            raise RuntimeError(
                f"調和定数ファイルに必須フィールドが不足しています "
                f"(地点: {location_id}): {missing}. "
                f"UTide solve() で生成された正しいcoefを使用してください。"
            )

    def clear_cache(self) -> None:
        """Clear the cached harmonic coefficients.

        キャッシュされた調和定数をすべてクリアします。
        調和定数ファイルを更新した場合に呼び出してください。
        """
        self._coef_cache.clear()
        logger.debug("調和定数キャッシュをクリアしました")


def generate_harmonics(
    observed_times: np.ndarray[Any, np.dtype[np.datetime64]],
    observed_heights: np.ndarray[Any, np.dtype[np.floating[Any]]],
    latitude: float,
    output_path: Path,
) -> None:
    """Generate harmonic coefficients from observed tidal data.

    実測潮汐データからUTide solve()で調和解析を行い、
    結果をpickleファイルとして保存します。
    このファイルはTideCalculationAdapterで読み込んで予測に使用します。

    Args:
        observed_times: Array of observation timestamps.
                        (観測時刻の配列)
        observed_heights: Array of observed tide heights in cm.
                          (観測潮位の配列、cm単位)
        latitude (float): Latitude of the observation station.
                          (観測地点の緯度)
        output_path (Path): Path to save the pickle file.
                            (pickle保存先パス)

    Raises:
        ValueError: If input data is insufficient or invalid.
                    (入力データが不足または不正な場合)
        RuntimeError: If harmonic analysis fails.
                      (調和解析に失敗した場合)
    """
    # 入力データの検証
    if len(observed_times) < 168:  # 最低1週間分（168時間）
        raise ValueError(
            f"観測データが不足しています: {len(observed_times)}点 (最低168点=1週間分が必要)"
        )

    if len(observed_times) != len(observed_heights):
        raise ValueError(
            f"観測時刻と潮位の配列長が一致しません: "
            f"times={len(observed_times)}, heights={len(observed_heights)}"
        )

    if not (-90 <= latitude <= 90):
        raise ValueError(f"緯度が範囲外です: {latitude} (有効範囲: -90 ~ 90)")

    try:
        coef = utide.solve(
            observed_times,
            observed_heights,
            lat=latitude,
            verbose=False,
        )
    except Exception as e:
        raise RuntimeError(f"調和解析に失敗しました: {e}") from e

    # pickleで保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(coef, f)

    logger.info(
        "調和定数を生成しました: 出力=%s, 分潮数=%d, 平均潮位=%.2f cm",
        output_path,
        len(coef["name"]),
        coef["mean"],
    )
