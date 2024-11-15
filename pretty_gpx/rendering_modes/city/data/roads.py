#!/usr/bin/python3
"""Roads."""
import os

from tqdm import tqdm

from pretty_gpx.common.data.overpass_processing import get_ways_coordinates_from_results
from pretty_gpx.common.data.overpass_request import get_count
from pretty_gpx.common.data.overpass_request import ListLonLat
from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.rendering_modes.city.data.city_road_types import CityRoadType
from pretty_gpx.rendering_modes.city.data.city_road_types import get_city_roads_with_priority_better_than
from pretty_gpx.rendering_modes.city.data.city_road_types import ROAD_TYPE_DATA

ROADS_CACHE = GpxDataCacheHandler(name='roads', extension='.pkl')

def get_downloadable_road_types(bounds: GpxBounds) -> list[CityRoadType]:
    """Get the roads types to download depending on the density of roads on the map."""
    queries = dict()
    for road_type, data in ROAD_TYPE_DATA.items():
        tag_pattern = "|".join(data.tags)
        queries[road_type] = [f"way['highway'~'({tag_pattern})']"]
    count_total = get_count(query_elements=queries,
                            bounds=bounds,
                            include_way_nodes=True)
    # Check that the result is ordered so we can calculate cumulative sum
    sorted_road_types = sorted(ROAD_TYPE_DATA.keys(), key=lambda road_type: ROAD_TYPE_DATA[road_type].priority)
    assert list(count_total.keys()) == sorted_road_types
    cum_sum: dict[int, tuple[int, int]] = dict()
    last_item = []
    cum_sum_previous_nodes = 0
    cum_sum_previous_ways = 0
    for road_type, count in count_total.items():
        last_item.append(road_type)
        cum_sum_previous_nodes += count["nodes"]
        cum_sum_previous_ways += count["ways"]
        cum_sum[ROAD_TYPE_DATA[road_type].priority] = (cum_sum_previous_nodes, cum_sum_previous_ways)

    # Now check the sums to apply a criteria
    for priority, (cum_nodes, cum_ways)  in cum_sum.items():
        if cum_ways > 7500000 or cum_nodes > 30000000:
            return get_city_roads_with_priority_better_than(priority)
    # Return all roads
    return list(ROAD_TYPE_DATA.keys())

@profile
def prepare_download_city_roads(query: OverpassQuery,
                                bounds: GpxBounds,
                                roads_to_plot: list[CityRoadType]) -> list[CityRoadType]:
    """Download roads map from OpenStreetMap."""
    cache_pkl = ROADS_CACHE.get_path(bounds)
    if os.path.isfile(cache_pkl):
        cityroads_cache: dict[CityRoadType, list[ListLonLat]] = read_pickle(file_path=cache_pkl)
        roads_types_cache = list(cityroads_cache.keys())
        query.add_cached_result(ROADS_CACHE.name, cache_file=cache_pkl)
        if all(key in roads_types_cache for key in roads_to_plot):
            logger.debug("Roads needed already downloaded")
            roads_to_plot = []
        else:
            logger.debug("Downloading additionnal roads")
            roads_to_plot = [key for key in roads_to_plot if key not in roads_types_cache]
    if len(roads_to_plot) > 0:
        for city_road_type in tqdm(roads_to_plot):
            highway_tags_str = "|".join(ROAD_TYPE_DATA[city_road_type].tags)
            query_name = ROAD_TYPE_DATA[city_road_type].query_name
            query.add_overpass_query(query_name,
                                     [f"way['highway'~'({highway_tags_str})']"],
                                     bounds,
                                     include_way_nodes=True,
                                     add_relative_margin=None)
    return roads_to_plot

@profile
def process_city_roads(query: OverpassQuery,
                       bounds: GpxBounds,
                       city_roads_downloaded: list[CityRoadType]) -> dict[CityRoadType,list[ListLonLat]]:
    """Query the overpass API to get the roads of a city."""
    if len(city_roads_downloaded) > 0:
        # We need to process some downloaded road types.
        if query.is_cached(ROADS_CACHE.name):
            cache_file = query.get_cache_file(ROADS_CACHE.name)
            roads = read_pickle(cache_file)
        else:
            roads = dict()
        with Profiling.Scope("Process City Roads"):
            for city_road_type in city_roads_downloaded:
                query_name = ROAD_TYPE_DATA[city_road_type].query_name
                result = query.get_query_result(query_name)
                roads[city_road_type] = get_ways_coordinates_from_results(result)
        cache_pkl = ROADS_CACHE.get_path(bounds)
        write_pickle(cache_pkl, roads)
        query.add_cached_result(ROADS_CACHE.name, cache_file=cache_pkl)
        return roads
    elif query.is_cached(ROADS_CACHE.name):
        cache_file = query.get_cache_file(ROADS_CACHE.name)
        return read_pickle(cache_file)
    else:
        raise FileNotFoundError("Query is supposed to be cached but it is not.")
