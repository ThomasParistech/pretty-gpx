#!/usr/bin/python3
"""GPX Distance."""
from typing import overload

import numpy as np

from pretty_gpx.common.utils.asserts import assert_np_shape
from pretty_gpx.common.utils.utils import EARTH_RADIUS_M


def latlon_aspect_ratio(lat: float) -> float:
    """Aspect ratio of the lat/lon map."""
    return 1.0/np.cos(np.deg2rad(lat))


@overload
def get_delta_xy(latlon_1: tuple[float, float], latlon_2: tuple[float, float]) -> tuple[float, float]: ...


@overload
def get_delta_xy(latlon_1: tuple[float, float], latlon_2: np.ndarray) -> tuple[np.ndarray, np.ndarray]: ...


def get_delta_xy(latlon_1: tuple[float, float],
                 latlon_2: tuple[float, float] | np.ndarray) -> tuple[float, float] | tuple[np.ndarray, np.ndarray]:
    """Difference X/Y between two lat/lon points in meters."""
    if isinstance(latlon_2, np.ndarray):
        assert_np_shape(latlon_2, (None, 2))

    latlon_1_np = np.array(latlon_1).reshape(-1, 2)
    latlon_2_np = np.array(latlon_2).reshape(-1, 2)

    dy = EARTH_RADIUS_M*np.deg2rad(np.abs(latlon_1_np[:, 0]-latlon_2_np[:, 0]))
    dx = EARTH_RADIUS_M*np.deg2rad(np.abs(latlon_1_np[:, 1]-latlon_2_np[:, 1])) / latlon_aspect_ratio(0.5*latlon_1[0])

    if isinstance(latlon_2, tuple):
        return float(dx[0]), float(dy[0])

    return dx, dy


@overload
def get_distance_m(latlon_1: tuple[float, float], latlon_2: tuple[float, float]) -> float: ...


@overload
def get_distance_m(latlon_1: tuple[float, float], latlon_2: np.ndarray) -> np.ndarray: ...


def get_distance_m(latlon_1: tuple[float, float], latlon_2: tuple[float, float] | np.ndarray) -> float | np.ndarray:
    """XY Distance between two lat/lon points in meters."""
    if isinstance(latlon_2, tuple):
        dx, dy = get_delta_xy(latlon_1, latlon_2)
        return float(np.linalg.norm([dx, dy]))

    dx_np, dy_np = get_delta_xy(latlon_1, latlon_2)
    return np.linalg.norm(np.stack((dx_np, dy_np), axis=-1), axis=-1)
