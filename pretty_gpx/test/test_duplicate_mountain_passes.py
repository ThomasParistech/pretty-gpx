"""Offline regression coverage for duplicate mountain-pass entries."""
from unittest.mock import patch

from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.rendering_modes.mountain.data.mountain_passes import process_mountain_passes


def test_same_named_osm_entries_merge_but_distinct_peaks_remain() -> None:
    from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint, ScatterPointCategory
    from pretty_gpx.rendering_modes.mountain.data.mountain_passes import deduplicate_named_passes

    def point(name, lat):
        return ScatterPoint(name=name, lat=lat, lon=-3.65, category=ScatterPointCategory.MOUNTAIN_PASS)

    first = point('Example Pass\n(865 m)', 37.0683)
    closer = point('Example Pass\n(865 m)', 37.0707)
    different = point('Other summit\n(870 m)', 37.071)
    distant = point(first.name, 37.1)
    track = GpxTrack()
    with patch.object(track, 'get_distances_m', return_value=[44., 4., 10., 20.]):
        assert deduplicate_named_passes([first, closer, different, distant], track) == [closer, different, distant]


def test_cached_passes_are_deduplicated(tmp_path) -> None:
    from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint, ScatterPointCategory
    from pretty_gpx.common.utils.pickle_io import write_pickle

    points = [ScatterPoint(name='Same pass\n(865 m)', lat=lat, lon=-3.65,
                           category=ScatterPointCategory.MOUNTAIN_PASS) for lat in [37.0683, 37.0707]]
    cache = tmp_path / 'peaks.pkl'
    write_pickle(str(cache), points)
    query = OverpassQuery(query_cached_results={'mountain_pass': str(cache)})
    track = GpxTrack()
    with patch.object(track, 'get_distances_m', return_value=[44., 4.]):
        assert process_mountain_passes(query, track) == [points[1]]


def test_fresh_passes_keep_closest_entry_before_spatial_filter(tmp_path) -> None:
    from overpy import Node, Result

    result = Result()
    for node_id, lat in enumerate([0., .001], start=1):
        result.append(Node(node_id=node_id, lat=lat, lon=0.,
                           tags={'name': 'Example Pass', 'ele': '1000'},
                           attributes={}, result=result))
    query = OverpassQuery(query_unprocessed_results={'mountain_passes': result})
    track = GpxTrack()
    with patch.object(track, 'get_distances_m', return_value=[40., 4.]):
        with patch('pretty_gpx.rendering_modes.mountain.data.mountain_passes.MOUNTAIN_PASS_CACHE.get_path',
                   return_value=str(tmp_path / 'passes.pkl')):
            points = process_mountain_passes(query, track)
    assert len(points) == 1
    assert points[0].lat == .001
