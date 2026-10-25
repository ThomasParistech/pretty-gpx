"""Regression tests for markers on distance-based elevation profiles."""
import numpy as np
import pytest

from pretty_gpx.common.drawing.components.elevation_profile import ElevationProfile
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint, ScatterPointCategory
from pretty_gpx.common.gpx.gpx_track import GpxTrack


@pytest.mark.parametrize('n_points', [20, 1000])
def test_marker_uses_distance_with_uneven_recording(n_points: int) -> None:
    distances = np.linspace(0, 1, 100) ** 3
    track = GpxTrack(list_lon=distances.tolist(), list_lat=[37.] * 100,
                     list_ele_m=(1000 + distances * 100).tolist(),
                     list_cumul_dist_km=(distances * 90).tolist())
    point = ScatterPoint(name='Peak', lon=track.list_lon[70], lat=37.,
                         category=ScatterPointCategory.MOUNTAIN_PASS)
    profile = ElevationProfile.from_track(track.get_bounds(), track, [point], .45, n_points=n_points)
    index = profile.scatter_indices[point.category][0]
    assert abs(profile.rel_poly_lon[index] - distances[70]) <= 1 / min(n_points, 100)

