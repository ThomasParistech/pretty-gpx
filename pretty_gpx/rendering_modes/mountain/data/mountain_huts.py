#!/usr/bin/python3
"""Huts."""
import os
from dataclasses import dataclass

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling


@dataclass
class MountainHut:
    """Mountain Hut Data."""
    name: str | None
    lon: float
    lat: float


MOUNTAIN_HUTS_CACHE = GpxDataCacheHandler(name='huts', extension='.pkl')
MOUNTAIN_HUTS_ARRAY_NAME = "mountain_huts"


@profile
def prepare_download_mountain_huts(query: OverpassQuery, bounds: GpxBounds) -> None:
    """Add the queries for mountain huts inside the global OverpassQuery."""
    cache_pkl = MOUNTAIN_HUTS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(MOUNTAIN_HUTS_CACHE.name, cache_file=cache_pkl)
        return

    # See https://www.openstreetmap.org/way/112147855 (Refuge Plan-Sec)
    # See https://www.openstreetmap.org/node/451703419 (Refuge des Barmettes)
    query.add_overpass_query(array_name=MOUNTAIN_HUTS_ARRAY_NAME,
                             query_elements=["nw['tourism'='alpine_hut']",
                                             "nw['tourism'='wilderness_hut']",
                                             "nw['tourism'='camp_site']"],
                             tags=True,
                             return_center_only=True,
                             bounds=bounds,
                             add_relative_margin=0.05)


@profile
def process_mountain_huts(query: OverpassQuery, bounds: GpxBounds) -> list[MountainHut]:
    """Process the overpass API result to get the mountain huts."""
    if query.is_cached(MOUNTAIN_HUTS_CACHE.name):
        cache_file = query.get_cache_file(MOUNTAIN_HUTS_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process Huts"):
        results = query.get_query_result(MOUNTAIN_HUTS_ARRAY_NAME)

        node_huts = [MountainHut(name=str(node.tags.get("name")),
                                 lon=float(node.lon),
                                 lat=float(node.lat))
                     for node in results.nodes
                     if "name" in node.tags]

        way_huts = [MountainHut(name=str(way.tags.get("name")),
                                lon=float(way.center_lon),
                                lat=float(way.center_lat))
                    for way in results.ways
                    if "name" in way.tags]
        huts = node_huts + way_huts
        logger.info(f"Found {len(huts)} candidate mountain huts")

    cache_pkl = MOUNTAIN_HUTS_CACHE.get_path(bounds)
    write_pickle(cache_pkl, huts)
    query.add_cached_result(MOUNTAIN_HUTS_CACHE.name, cache_file=cache_pkl)
    return huts
