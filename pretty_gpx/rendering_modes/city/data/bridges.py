#!/usr/bin/python3
"""Bridges."""
import os
from dataclasses import dataclass

from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.gpx.gpx_distance import ListLonLat
from pretty_gpx.common.gpx.gpx_track import GpxTrack
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
def prepare_download_city_bridges(query: OverpassQuery, bounds: GpxBounds) -> None:
    """Add the queries for city bridges inside the global OverpassQuery."""
    cache_pkl = BRIDGES_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(BRIDGES_CACHE.name, cache_file=cache_pkl)
        return

    query.add_overpass_query(array_name=BRIDGES_ARRAY_NAME,
                             query_elements=['wr["name"]["wikidata"]["man_made"="bridge"]'],
                             include_tags=True,
                             return_center_only=True,
                             bounds=bounds,
                             add_relative_margin=0.05)


@profile
def process_city_bridges(query: OverpassQuery,
                         bounds: GpxBounds) -> tuple[ListLonLat, list[str]]:
    """Process the overpass API result to get the bridges of a city."""
    if query.is_cached(BRIDGES_CACHE.name):
        cache_file = query.get_cache_file(BRIDGES_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process Bridges"):
        res = query.get_query_result(BRIDGES_ARRAY_NAME)
        list_wr = res.ways + res.relations
        bridges_lon_lat = [(wr.center_lon, wr.center_lat) for wr in list_wr]
        bridges_names = [wr.tags.get("name") for wr in list_wr]
        named_bridges = (bridges_lon_lat, bridges_names)

    cache_pkl = BRIDGES_CACHE.get_path(bounds)
    write_pickle(cache_pkl, named_bridges)
    query.add_cached_result(BRIDGES_CACHE.name, cache_file=cache_pkl)
    return named_bridges


def get_gpx_track_bridges(bridges_lon_lat: ListLonLat,
                          bridges_name: list[str],
                          gpx: GpxTrack) -> list[CityBridge]:
    """Filter the city bridge that are close to the gpx track."""
    if len(bridges_lon_lat) == 0:
        return []

    distances = gpx.get_distances_m(bridges_lon_lat)

    return [CityBridge(name=name, lon=lon, lat=lat)
            for (lon, lat), name, dist in zip(bridges_lon_lat, bridges_name, distances)
            if dist < 25]
