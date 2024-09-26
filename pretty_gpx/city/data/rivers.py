#!/usr/bin/python3
"""Rivers."""
import os

import overpy

from pretty_gpx.common.data.overpass_processing import create_patch_collection_from_polygons
from pretty_gpx.common.data.overpass_processing import get_polygons_from_closed_ways
from pretty_gpx.common.data.overpass_processing import get_polygons_from_relations
from pretty_gpx.common.data.overpass_processing import SurfacePolygons
from pretty_gpx.common.data.overpass_request import overpass_query
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling

RIVERS_CACHE = GpxDataCacheHandler(name='rivers', extension='.pkl')


def download_city_rivers(bounds: GpxBounds) -> SurfacePolygons:
    """Download rivers area from OpenStreetMap.

    Args:
        bounds: GPX bounds

    Returns:
        List of ShapelyPolygon of all forests/parks
    """
    cache_pkl = RIVERS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        rivers_patches: SurfacePolygons = read_pickle(cache_pkl)
    else:
        with Profiling.Scope("Download Rivers"):
            rivers_relation_results = _query_rivers_relations(bounds=bounds)
            rivers_way_results = _query_rivers_ways(bounds=bounds)
            rivers_relations = get_polygons_from_relations(results=rivers_relation_results)
            rivers_ways = get_polygons_from_closed_ways(rivers_way_results.ways)
            logger.info(f"Found {len(rivers_relations)} polygons for rivers with relations "
                        f"and {len(rivers_ways)} with ways")
            rivers = rivers_relations + rivers_ways
            rivers_patches = create_patch_collection_from_polygons(rivers)
        write_pickle(cache_pkl, rivers_patches)
    return rivers_patches


@profile
def _query_rivers_relations(bounds: GpxBounds) -> overpy.Result:
    """Query the overpass API to get the rivers of a city using relations."""
    result = overpass_query(['relation["natural"="water"]["water" = "river"]'],
                            bounds,
                            include_way_nodes=True,
                            return_geometry=True)
    return result


@profile
def _query_rivers_ways(bounds: GpxBounds) -> overpy.Result:
    """Query the overpass API to get the rivers of a city using ways."""
    result = overpass_query(['way["natural"="water"]["water" = "river"]'],
                            bounds,
                            include_way_nodes=True,
                            return_geometry=True)
    return result
