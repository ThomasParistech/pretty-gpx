#!/usr/bin/python3
"""Rivers."""
import os

import numpy as np

from pretty_gpx.common.data.overpass_processing import create_patch_collection_from_polygons
from pretty_gpx.common.data.overpass_processing import get_polygons_from_closed_ways
from pretty_gpx.common.data.overpass_processing import get_polygons_from_relations
from pretty_gpx.common.data.overpass_processing import get_rivers_polygons_from_lines
from pretty_gpx.common.data.overpass_processing import SurfacePolygons
from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import EARTH_RADIUS_M

RIVERS_CACHE = GpxDataCacheHandler(name='rivers', extension='.pkl')

RIVERS_WAYS_ARRAY_NAME = "rivers_ways"
RIVERS_RELATIONS_ARRAY_NAME = "rivers_relations"
RIVERS_LINE_WAYS_ARRAY_NAME = "rivers_line_ways"

RIVER_LINE_WIDTH_M = 8
RIVER_LINE_WIDTH = np.rad2deg(RIVER_LINE_WIDTH_M/EARTH_RADIUS_M)


@profile
def prepare_download_city_rivers(query: OverpassQuery, bounds: GpxBounds) -> None:
    """Add the queries for city rivers inside the global OverpassQuery."""
    cache_pkl = RIVERS_CACHE.get_path_from_bounds(bounds)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(RIVERS_CACHE.name, cache_file=cache_pkl)
        return

    min_len = bounds.diagonal_m*0.01
    natural_water_l = ["reservoir", "canal", "stream_pool", "lagoon", "oxbow", "river", "lake", "pond"]
    join_character = '|'
    query.add_overpass_query(array_name=RIVERS_RELATIONS_ARRAY_NAME,
                             query_elements=['relation["natural"="water"]'
                                             f'["water"~"({join_character.join(natural_water_l)})"]',
                                             'relation["natural"="wetland"]["wetland" = "tidal"]',
                                             'relation["natural"="bay"]'],
                             bounds=bounds,
                             include_way_nodes=True,
                             include_relation_members_nodes=True,
                             return_geometry=True)
    query.add_overpass_query(array_name=RIVERS_WAYS_ARRAY_NAME,
                             query_elements=['way["natural"="water"]["water"~'
                                             f'"({join_character.join(natural_water_l)})"]',
                                             f'way["natural"="water"][!"water"](if: length() > {min_len})',
                                             'way["natural"="wetland"]["wetland" = "tidal"]',
                                             'way["natural"="bay"]'],
                             bounds=bounds,
                             include_way_nodes=True,
                             return_geometry=True)
    query.add_overpass_query(array_name=RIVERS_LINE_WAYS_ARRAY_NAME,
                             query_elements=['way["waterway"~"(river|fairway|flowline|stream|canal)"]'
                                             '["tunnel"!~".*"]'],
                             bounds=bounds,
                             include_way_nodes=True,
                             return_geometry=False)


@profile
def process_city_rivers(query: OverpassQuery,
                        bounds: GpxBounds) -> SurfacePolygons:
    """Process the overpass API result to get the rivers of a city."""
    if query.is_cached(RIVERS_CACHE.name):
        cache_file = query.get_cache_file(RIVERS_CACHE.name)
        return read_pickle(cache_file)

    with Profiling.Scope("Process Rivers"):
        rivers_relation_results = query.get_query_result(RIVERS_RELATIONS_ARRAY_NAME)
        rivers_way_results = query.get_query_result(RIVERS_WAYS_ARRAY_NAME)
        rivers_line_results = query.get_query_result(RIVERS_LINE_WAYS_ARRAY_NAME)
        rivers_relations = get_polygons_from_relations(results=rivers_relation_results)
        rivers_ways = get_polygons_from_closed_ways(rivers_way_results.ways)
        rivers = rivers_relations + rivers_ways
        rivers_lines_polygons = get_rivers_polygons_from_lines(api_result=rivers_line_results,
                                                               width=RIVER_LINE_WIDTH)
        rivers = rivers_lines_polygons + rivers
        logger.info(f"Found {len(rivers_relations)} polygons for rivers "
                    f"with relations and {len(rivers_ways)} with ways and"
                    f" {len(rivers_lines_polygons)} created with river main line")
        rivers_patches = create_patch_collection_from_polygons(rivers)

    cache_pkl = RIVERS_CACHE.get_path_from_bounds(bounds)
    write_pickle(cache_pkl, rivers_patches)
    query.add_cached_result(RIVERS_CACHE.name, cache_file=cache_pkl)
    return rivers_patches
