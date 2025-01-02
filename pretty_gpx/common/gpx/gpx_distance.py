#!/usr/bin/python3
"""GPX Distance."""
from dataclasses import dataclass
from typing import overload

import numpy as np

from pretty_gpx.common.utils.asserts import assert_eq
from pretty_gpx.common.utils.asserts import assert_np_shape
from pretty_gpx.common.utils.asserts import assert_np_shape_endswith
from pretty_gpx.common.utils.utils import EARTH_RADIUS_M

ListLonLat = list[tuple[float, float]]


@dataclass
class LocalProjectionXY:
    """Projection of lon/lat points to local XY coordinates."""
    lonlat_ref: np.ndarray  # (2,)

    @staticmethod
    def fit(*, lon_lat: np.ndarray) -> 'LocalProjectionXY':
        """Use the mean of the lon/lat points as the reference point."""
        assert_np_shape(lon_lat, (None, 2))
        return LocalProjectionXY(lonlat_ref=np.mean(lon_lat, axis=0))

    @overload
    def transform(self, *, lon_lat: tuple[float, float]) -> tuple[float, float]: ...
    @overload
    def transform(self, *,  lon_lat: np.ndarray) -> np.ndarray: ...

    def transform(self, *,  lon_lat: np.ndarray | tuple[float, float]) -> np.ndarray | tuple[float, float]:
        """Transform lon/lat points to local XY coordinates."""
        if isinstance(lon_lat, np.ndarray):
            assert_np_shape(lon_lat, (None, 2))

        lon_lat_np = np.asarray(lon_lat)
        local_xy = get_delta_xy(lonlat_1=lon_lat_np, lonlat_2=self.lonlat_ref[None, :])
        # N.B. We need the signed difference, because we can get points below the reference point

        if isinstance(lon_lat, tuple):
            return float(local_xy[0]), float(local_xy[1])

        return local_xy


@overload
def latlon_aspect_ratio(*, lat: float) -> float: ...
@overload
def latlon_aspect_ratio(*, lat: np.ndarray) -> np.ndarray: ...


def latlon_aspect_ratio(*, lat: float | np.ndarray) -> float | np.ndarray:
    """Aspect ratio of the lat/lon map."""
    res = 1.0/np.cos(np.deg2rad(lat))
    return res if isinstance(lat, np.ndarray) else float(res)


def get_delta_xy(*, lonlat_1: np.ndarray, lonlat_2: np.ndarray) -> np.ndarray:
    """Signed Difference X/Y between two lon/lat arrays of points in meters, i.e. lonlat_1 - lonlat_2."""
    assert_np_shape_endswith(lonlat_1, (2,))
    assert_np_shape_endswith(lonlat_2, (2,))
    assert_eq(lonlat_2.ndim, lonlat_1.ndim)

    lonlat_1 = lonlat_1.astype(float)
    lonlat_2 = lonlat_2.astype(float)
    diffs_xy = EARTH_RADIUS_M*np.deg2rad(lonlat_1 - lonlat_2)
    diffs_xy[..., 0] /= latlon_aspect_ratio(lat=lonlat_1[..., 1])

    return diffs_xy


@overload
def get_distance_m(*, lonlat_1: tuple[float, float], lonlat_2: tuple[float, float]) -> float: ...
@overload
def get_distance_m(*, lonlat_1: np.ndarray, lonlat_2: tuple[float, float]) -> np.ndarray: ...
@overload
def get_distance_m(*, lonlat_1: tuple[float, float], lonlat_2: np.ndarray) -> np.ndarray: ...
@overload
def get_distance_m(*, lonlat_1: np.ndarray, lonlat_2: np.ndarray) -> np.ndarray: ...


def get_distance_m(*,
                   lonlat_1: tuple[float, float] | np.ndarray,
                   lonlat_2: tuple[float, float] | np.ndarray) -> float | np.ndarray:
    """Element-wise XY Distance between two lon/lat points in meters."""
    # Reshape to allow broadcasting
    lonlat_1_np = np.array(lonlat_1).reshape(-1, 2)  # (N, 2)
    lonlat_2_np = np.array(lonlat_2).reshape(-1, 2)  # (N, 2)

    diffs_xy = get_delta_xy(lonlat_1=lonlat_1_np, lonlat_2=lonlat_2_np)  # (N, 2)

    distances_m = np.linalg.norm(diffs_xy, axis=-1)  # (N,)

    if isinstance(lonlat_1, tuple) and isinstance(lonlat_2, tuple):  # (1, 1)
        return float(distances_m[0])

    return distances_m  # (N,)


def get_pairwise_distance_m(*, lonlat_1: np.ndarray, lonlat_2: np.ndarray | None = None) -> np.ndarray:
    """Pairwise distance between two sets of lon/lat points in meters."""
    if lonlat_2 is None:
        lonlat_2 = lonlat_1
    assert_np_shape(lonlat_1, (None, 2))  # (N, 2)
    assert_np_shape(lonlat_2, (None, 2))  # (M, 2)

    diffs_xy = get_delta_xy(lonlat_1=lonlat_1[:, None, :], lonlat_2=lonlat_2[None, :, :])  # (N, M,2)

    grid_dist_m = np.linalg.norm(diffs_xy, axis=-1)  # (N, M)
    assert_np_shape(grid_dist_m, (len(lonlat_1), len(lonlat_2)))

    return grid_dist_m  # (N, M)
