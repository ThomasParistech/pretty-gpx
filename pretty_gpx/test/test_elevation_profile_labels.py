"""Regression tests for markers on distance-based elevation profiles."""
import numpy as np
import pytest

from pretty_gpx.common.drawing.components.elevation_profile import ElevationProfile
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint, ScatterPointCategory
from pretty_gpx.common.gpx.gpx_track import GpxTrack


def test_draw_labels_peaks_and_preserves_statistics() -> None:
    from unittest.mock import MagicMock
    from pretty_gpx.rendering_modes.mountain.drawing.mountain_params import MountainParams

    track = GpxTrack(list_lon=[0., 1., 2.], list_lat=[37., 37.1, 37.],
                     list_ele_m=[1000., 2000., 1000.], list_cumul_dist_km=[0., 10., 20.],
                     uphill_m=1000.)
    peak = ScatterPoint(name='Summit\n(2000 m)', lon=1., lat=37.1,
                        category=ScatterPointCategory.MOUNTAIN_PASS)
    start = ScatterPoint(name='Start', lon=0., lat=37., category=ScatterPointCategory.START)
    profile = ElevationProfile.from_track(track.get_bounds(), track, [start, peak], .45)
    drawing = MagicMock()
    profile.draw(drawing, MountainParams.default())
    texts = [call.kwargs['s'] for call in drawing.text.call_args_list]
    assert texts == ['20.00 km - 1000 m D+']
    assert drawing.profile_labels.call_args.kwargs['points'][0][2] == peak.name
    assert profile.peak_labels == [(1, peak.name)]
    assert profile.rel_poly_lat[1] < .9  # Headroom for the summit label.


def test_vertical_profile_labels_do_not_overlap() -> None:
    import matplotlib.pyplot as plt
    from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
    from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
    from pretty_gpx.common.layout.paper_size import PAPER_SIZES
    from pretty_gpx.rendering_modes.mountain.drawing.mountain_params import MountainParams

    x = np.linspace(0, 1, 101)
    track = GpxTrack(list_lon=x.tolist(), list_lat=[37.] * len(x),
                     list_ele_m=(1000 + 1000 * np.sin(np.pi * x)).tolist(),
                     list_cumul_dist_km=(100 * x).tolist())
    points = [ScatterPoint(name=f'Nearby mountain {i}\n(2000 m)', lon=lon, lat=37.,
                            category=ScatterPointCategory.MOUNTAIN_PASS)
              for i, lon in enumerate([.495, .50, .505])]
    bounds = GpxBounds(0., 1., 0., .22)
    profile = ElevationProfile.from_track(bounds, track, points, .45)
    fig, ax = plt.subplots()
    try:
        with DrawingFigure(PAPER_SIZES['A4'], GpxBounds(0., 1., 0., 1.), fig, ax) as drawing:
            profile.draw(drawing, MountainParams.default())
        fig.canvas.draw()
        boxes = [label.get_window_extent(fig.canvas.get_renderer()) for label in ax.texts[:-1]]
        assert len(boxes) == 3
        assert all(label.get_rotation() == 90 for label in ax.texts[:-1])
        assert all(label.arrow_patch is None for label in ax.texts[:-1])
        assert not any(a.overlaps(b) for i, a in enumerate(boxes) for b in boxes[i + 1:])
        ordered = sorted(boxes, key=lambda box: box.x0)
        # At least 2 mm of breathing room on A4, even for almost coincident markers.
        gap_px = 2 / 25.4 * fig.dpi
        assert all(b.x0 - a.x1 >= gap_px - .1 for a, b in zip(ordered, ordered[1:]))
    finally:
        plt.close(fig)
