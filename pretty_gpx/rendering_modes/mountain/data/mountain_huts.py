#!/usr/bin/python3
"""Huts."""
import os

import numpy as np

from pretty_gpx.common.data.place_name import get_place_name
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.common.gpx.gpx_distance import get_distance_m
from pretty_gpx.common.gpx.multi_gpx_track import MultiGpxTrack
from pretty_gpx.common.request.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.request.osm_name import get_shortest_name
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import safe

MOUNTAIN_HUTS_CACHE = GpxDataCacheHandler(name='huts', extension='.pkl')
MOUNTAIN_HUTS_ARRAY_NAME = "mountain_huts"


@profile
def prepare_download_mountain_huts(query: OverpassQuery, multi_gpx_track: MultiGpxTrack) -> None:
    """Add the queries for mountain huts inside the global OverpassQuery."""
    cache_pkl = MOUNTAIN_HUTS_CACHE.get_path(multi_gpx_track)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(MOUNTAIN_HUTS_CACHE.name, cache_file=cache_pkl)
        return

    # See https://www.openstreetmap.org/way/112147855 (Refuge Plan-Sec)
    # See https://www.openstreetmap.org/node/451703419 (Refuge des Barmettes)
    query.add_overpass_query(array_name=MOUNTAIN_HUTS_ARRAY_NAME,
                             query_elements=["nw['tourism'='alpine_hut']",
                                             "nw['tourism'='wilderness_hut']",
                                             "nw['tourism'='camp_site']"],
                             include_tags=True,
                             return_center_only=True,
                             bounds=multi_gpx_track.get_bounds(),
                             add_relative_margin=0.05)


@profile
def process_mountain_huts(query: OverpassQuery, multi_gpx_track: MultiGpxTrack) -> list[ScatterPoint]:
    """Process the overpass API result to get the mountain huts."""
    if query.is_cached(MOUNTAIN_HUTS_CACHE.name):
        cache_file = query.get_cache_file(MOUNTAIN_HUTS_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process Huts"):
        results = query.get_query_result(MOUNTAIN_HUTS_ARRAY_NAME)

        # Get Candidate Mountain Huts
        node_candidates = [ScatterPoint(name=safe(get_shortest_name(node)),
                                        lon=float(node.lon),
                                        lat=float(node.lat),
                                        category=ScatterPointCategory.MOUNTAIN_HUT)
                           for node in results.nodes
                           if "name" in node.tags]

        way_candidates = [ScatterPoint(name=safe(get_shortest_name(way)),
                                       lon=float(way.center_lon),
                                       lat=float(way.center_lat),
                                       category=ScatterPointCategory.MOUNTAIN_HUT)
                          for way in results.ways
                          if "name" in way.tags]
        candidates = node_candidates + way_candidates

        # Get Huts
        huts: list[ScatterPoint] = []
        candidates_lonlat_np = np.array([[h.lon, h.lat] for h in candidates])
        for i in range(len(multi_gpx_track) - 1):
            crt_track = multi_gpx_track.tracks[i]
            next_track = multi_gpx_track.tracks[i+1]
            hut_lon = 0.5*(crt_track.list_lon[-1] + next_track.list_lon[0])
            hut_lat = 0.5*(crt_track.list_lat[-1] + next_track.list_lat[0])

            distances_m = get_distance_m(lonlat_1=(hut_lon, hut_lat), lonlat_2=candidates_lonlat_np)
            closest_idx = int(np.argmin(distances_m))
            closest_distance = distances_m[closest_idx]
            if closest_distance < 300:
                huts.append(candidates.pop(closest_idx))
            else:
                name = get_place_name(lon=hut_lon, lat=hut_lat)
                # name  = None
                huts.append(ScatterPoint(name=name, lat=hut_lat, lon=hut_lon,
                                         category=ScatterPointCategory.MOUNTAIN_HUT))

        logger.info(f"Huts: {', '.join([h.name if h.name is not None else '?' for h in huts if h.name])}")

    cache_pkl = MOUNTAIN_HUTS_CACHE.get_path(multi_gpx_track)
    write_pickle(cache_pkl, huts)
    query.add_cached_result(MOUNTAIN_HUTS_CACHE.name, cache_file=cache_pkl)
    return huts
