#!/usr/bin/python3
"""Mountain Passes."""
import os

import numpy as np

from pretty_gpx.common.drawing.utils.scatter_point import ScatterPoint
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.common.gpx.gpx_distance import get_distance_m
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.request.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling

MOUNTAIN_PASSES_ARRAY_NAME = "mountain_passes"


MOUNTAIN_PASS_CACHE = GpxDataCacheHandler(name='mountain_pass', extension='.pkl')


@profile
def prepare_download_mountain_passes(query: OverpassQuery, gpx_track: GpxTrack) -> None:
    """Add the queries for mountain passes inside the global OverpassQuery."""
    cache_pkl = MOUNTAIN_PASS_CACHE.get_path(gpx_track)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(MOUNTAIN_PASS_CACHE.name, cache_file=cache_pkl)
        return

    # See https://www.openstreetmap.org/node/4977980007 (Col du Galibier)
    # See https://www.openstreetmap.org/node/12068789882 (Col de la Vanoise)
    # See https://www.openstreetmap.org/node/34975894 (Pic du Cabaliros)
    query.add_overpass_query(array_name=MOUNTAIN_PASSES_ARRAY_NAME,
                             query_elements=["node['natural'='saddle']",
                                             "node['natural'='peak']",
                                             "node['natural'='volcano']",
                                             "node['mountain_pass'='yes']",
                                             "node['hiking'='yes']['tourism'='information']",
                                             "node['hiking'='yes']['information'='guidepost']"],
                             include_tags=True,
                             return_center_only=True,
                             bounds=gpx_track.get_bounds(),
                             add_relative_margin=0.05)


@profile
def process_mountain_passes(query: OverpassQuery, gpx_track: GpxTrack) -> list[ScatterPoint]:
    """Process the overpass API result to get the mountain passes."""
    if query.is_cached(MOUNTAIN_PASS_CACHE.name):
        cache_file = query.get_cache_file(MOUNTAIN_PASS_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process Mountain Passes"):
        results = query.get_query_result(MOUNTAIN_PASSES_ARRAY_NAME)

        # Get Candidate Mountain Passes
        candidates: list[ScatterPoint] = []
        for node in results.nodes:
            if "name" in node.tags and "ele" in node.tags:
                ele = str(node.tags["ele"])
                if ele.isnumeric():
                    name = str(node.tags["name"])
                    if "hiking" in node.tags and node.tags["hiking"] == "yes":
                        if not name.lower().startswith(("col ", "golet ", "pic ", "mont ")):
                            continue

                    candidates.append(ScatterPoint(name=f"{name}\n({int(ele)} m)",
                                                   lon=float(node.lon),
                                                   lat=float(node.lat),
                                                   category=ScatterPointCategory.MOUNTAIN_PASS))

        passes: list[ScatterPoint] = []
        if len(candidates) != 0:
            # Keep only the ones close to the GPX track
            distances_m = gpx_track.get_distances_m(targets_lon_lat=[(pt.lon, pt.lat) for pt in candidates])
            candidates = [pt for pt, d_m in zip(candidates, distances_m) if d_m < 50]

            if len(candidates) != 0:
                # Remove duplicates
                for pt in candidates:
                    if len(passes) == 0 or np.min(get_distance_m(lonlat_1=(pt.lon, pt.lat),
                                                                 lonlat_2=np.array([[m.lon, m.lat]
                                                                                    for m in passes]))) > 200:
                        passes.append(pt)

    cache_pkl = MOUNTAIN_PASS_CACHE.get_path(gpx_track)
    write_pickle(cache_pkl, passes)
    query.add_cached_result(MOUNTAIN_PASS_CACHE.name, cache_file=cache_pkl)

    return passes
