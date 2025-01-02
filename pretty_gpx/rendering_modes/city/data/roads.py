#!/usr/bin/python3
"""Roads."""
import os
from enum import auto
from enum import Enum

from tqdm import tqdm

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_distance import ListLonLat
from pretty_gpx.common.request.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.request.overpass_processing import get_ways_coordinates_from_results
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling

ROADS_CACHE = GpxDataCacheHandler(name='roads', extension='.pkl')


class CityRoadType(Enum):
    """City Road Type."""
    HIGHWAY = auto()
    SECONDARY_ROAD = auto()
    STREET = auto()
    ACCESS_ROAD = auto()


HIGHWAY_TAGS_PER_CITY_ROAD_TYPE = {
    CityRoadType.HIGHWAY: ["motorway", "trunk", "primary"],
    CityRoadType.SECONDARY_ROAD: ["tertiary", "secondary"],
    CityRoadType.STREET: ["residential", "living_street"],
    CityRoadType.ACCESS_ROAD: ["unclassified", "service"]
}

QUERY_NAME_PER_CITY_ROAD_TYPE = {
    CityRoadType.HIGHWAY: "highway",
    CityRoadType.SECONDARY_ROAD: "secondary_roads",
    CityRoadType.STREET: "street",
    CityRoadType.ACCESS_ROAD: "access_roads"
}

assert HIGHWAY_TAGS_PER_CITY_ROAD_TYPE.keys() == QUERY_NAME_PER_CITY_ROAD_TYPE.keys()

CityRoads = dict[CityRoadType, list[ListLonLat]]


@profile
def prepare_download_city_roads(query: OverpassQuery,
                                bounds: GpxBounds) -> None:
    """Download roads map from OpenStreetMap.

    Args:
        query: OverpassQuery class that merge all queries into a single one
        bounds: GPX bounds

    Returns:
        List of roads (sequence of lon, lat coordinates) for each road type
    """
    cache_pkl = ROADS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(ROADS_CACHE.name, cache_file=cache_pkl)
        return

    for city_road_type in tqdm(CityRoadType):
        highway_tags_str = "|".join(HIGHWAY_TAGS_PER_CITY_ROAD_TYPE[city_road_type])
        query.add_overpass_query(QUERY_NAME_PER_CITY_ROAD_TYPE[city_road_type],
                                 [f"way['highway'~'({highway_tags_str})']"],
                                 bounds,
                                 include_way_nodes=True,
                                 add_relative_margin=None)


@profile
def process_city_roads(query: OverpassQuery,
                       bounds: GpxBounds) -> dict[CityRoadType, list[ListLonLat]]:
    """Query the overpass API to get the roads of a city."""
    if query.is_cached(ROADS_CACHE.name):
        cache_file = query.get_cache_file(ROADS_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process City Roads"):
        roads = dict()
        for city_road_type, query_name in QUERY_NAME_PER_CITY_ROAD_TYPE.items():
            logger.debug(f"Query name : {query_name}")
            result = query.get_query_result(query_name)
            roads[city_road_type] = get_ways_coordinates_from_results(result)

    cache_pkl = ROADS_CACHE.get_path(bounds)
    write_pickle(cache_pkl, roads)
    query.add_cached_result(ROADS_CACHE.name, cache_file=cache_pkl)

    return roads
