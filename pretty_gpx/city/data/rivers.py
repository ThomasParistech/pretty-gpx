#!/usr/bin/python3
"""Rivers"""
import os
import numpy as np


from matplotlib.patches import Polygon
from shapely import Polygon as ShapelyPolygon

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.data.overpass_request import overpass_query
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.data.overpass_processing import Surface_Polygons
from pretty_gpx.common.data.overpass_processing import create_patch_collection_from_polygons
from pretty_gpx.common.data.overpass_processing import get_polygons_from_relations
from pretty_gpx.common.data.overpass_processing import get_polygons_from_closed_ways




RIVERS_CACHE = GpxDataCacheHandler(name='rivers', extension='.pkl')


def download_city_rivers(bounds: GpxBounds) -> Surface_Polygons:
    """Download rivers area from OpenStreetMap.

    Args:
        bounds: GPX bounds

    Returns:
        List of ShapelyPolygon of all forests/parks
    """
    cache_pkl = RIVERS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        rivers_patches: Surface_Polygons = read_pickle(cache_pkl)
    else:
        rivers_relation_results = _query_rivers_relations(bounds=bounds)
        rivers_way_results = _query_rivers_ways(bounds=bounds)
        rivers_relations = get_polygons_from_relations(results=rivers_relation_results)
        rivers_ways = get_polygons_from_closed_ways(rivers_way_results.ways)
        logger.info(f"Found {len(rivers_relations)} polygons for rivers with relations and {len(rivers_ways)} with ways")
        rivers = rivers_relations + rivers_ways
        rivers_patches = create_patch_collection_from_polygons(rivers)
        write_pickle(cache_pkl, rivers_patches)
    return rivers_patches


def _query_rivers_relations(bounds: GpxBounds):
    """Query the overpass API to get the rivers of a city using relations."""
    result = overpass_query(['relation["natural"="water"]["water" = "river"]'],
                            bounds,
                            include_way_nodes=True,
                            return_geometry=True)    
    return result


def _query_rivers_ways(bounds: GpxBounds):
    """Query the overpass API to get the rivers of a city using ways."""
    result = overpass_query(['way["natural"="water"]["water" = "river"]'],
                            bounds,
                            include_way_nodes=True,
                            return_geometry=True)    
    return result
