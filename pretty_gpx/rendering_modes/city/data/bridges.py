#!/usr/bin/python3
"""Bridges."""
import os
from dataclasses import dataclass

from pretty_gpx.common.data.overpass_processing import process_around_ways_and_relations
from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling

BRIDGES_CACHE = GpxDataCacheHandler(name='bridges', extension='.pkl')

BRIDGES_ARRAY_NAME = "bridges"


@dataclass
class CityBridge:
    """City Bridge Data."""
    name: str
    lat: float
    lon: float


@profile
def prepare_download_city_bridges(query: OverpassQuery, track: GpxTrack) -> None:
    """Add the queries for city bridges inside the global OverpassQuery."""
    cache_pkl = BRIDGES_CACHE.get_path_from_track(track)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(BRIDGES_CACHE.name, cache_file=cache_pkl)
        return

    query.add_around_ways_overpass_query(array_name=BRIDGES_ARRAY_NAME,
                                         query_elements=['wr["name"]["wikidata"]["man_made"="bridge"]'],
                                         gpx_track=track,
                                         radius_m=40)


@profile
def process_city_bridges(query: OverpassQuery,
                         track: GpxTrack) -> list[CityBridge]:
    """Process the overpass API result to get the bridges of a city."""
    if query.is_cached(BRIDGES_CACHE.name):
        cache_file = query.get_cache_file(BRIDGES_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process Bridges"):
        res = query.get_query_result(BRIDGES_ARRAY_NAME)
        bridges = process_around_ways_and_relations(api_result=res)
        bridges_l = []
        for name, (lon,lat) in bridges.items():
            bridges_l.append(CityBridge(name, lat, lon))

    logger.info(f"Found {len(bridges_l)} bridge(s)")
    cache_pkl = BRIDGES_CACHE.get_path_from_track(track)
    write_pickle(cache_pkl, bridges_l)
    query.add_cached_result(BRIDGES_CACHE.name, cache_file=cache_pkl)
    return bridges_l
