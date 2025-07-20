#!/usr/bin/python3
"""Roads."""
import os
from enum import IntEnum

from tqdm import tqdm

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_distance import ListLonLat
from pretty_gpx.common.request.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.request.overpass_processing import get_ways_coordinates_from_results
from pretty_gpx.common.request.overpass_request import OverpassQuery
from pretty_gpx.common.utils.asserts import assert_same_keys
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling

ROADS_CACHE = GpxDataCacheHandler(name='roads', extension='.pkl')


class CityRoadPrecision(IntEnum):
    """Enum defining different road precision levels."""
    VERY_HIGH = 3  # Access roads
    HIGH = 2  # Streets
    MEDIUM = 1  # Secondary roads
    LOW = 0  # Highways

    @property
    def pretty_name(self) -> str:
        """Human-friendly name, e.g. 'Very-High'."""
        return self.name.replace("_", "-").title()

    @staticmethod
    def coarse_to_fine() -> list["CityRoadPrecision"]:
        """Return the list of road precision from coarse to fine."""
        return sorted(CityRoadPrecision, key=lambda p: p.value)


ROAD_HIGHWAY_TAGS: dict[CityRoadPrecision, list[str]] = {
    CityRoadPrecision.LOW: ["motorway", "trunk", "primary"],
    CityRoadPrecision.MEDIUM: ["tertiary", "secondary"],
    CityRoadPrecision.HIGH: ["residential", "living_street"],
    CityRoadPrecision.VERY_HIGH: ["unclassified", "service"]
}

assert_same_keys(ROAD_HIGHWAY_TAGS, CityRoadPrecision)


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

    for city_road_precision in tqdm(CityRoadPrecision):
        highway_tags_str = "|".join(ROAD_HIGHWAY_TAGS[city_road_precision])
        query.add_overpass_query(city_road_precision.name,
                                 [f"way['highway'~'({highway_tags_str})']"],
                                 bounds,
                                 include_way_nodes=True,
                                 add_relative_margin=None)


@profile
def process_city_roads(query: OverpassQuery,
                       bounds: GpxBounds) -> dict[CityRoadPrecision, list[ListLonLat]]:
    """Query the overpass API to get the roads of a city."""
    if query.is_cached(ROADS_CACHE.name):
        cache_file = query.get_cache_file(ROADS_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process City Roads"):
        roads = dict()
        for city_road_precision in CityRoadPrecision:
            logger.debug(f"Query precision : {city_road_precision.name}")
            result = query.get_query_result(city_road_precision.name)
            roads[city_road_precision] = get_ways_coordinates_from_results(result)

    cache_pkl = ROADS_CACHE.get_path(bounds)
    write_pickle(cache_pkl, roads)
    query.add_cached_result(ROADS_CACHE.name, cache_file=cache_pkl)

    return roads
