#!/usr/bin/python3
"""Overpass Processing."""

import overpy

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.logger import logger


from pretty_gpx.common.data.overpass_request import ListLonLat


def get_ways_coordinates_from_results(api_result: overpy.Result) -> list[ListLonLat]:
    """Get the lat/lon nodes coordinates of the ways from the overpass API result."""
    ways_coords = []
    for way in api_result.ways:
        road = [(float(node.lon), float(node.lat))
                for node in way.get_nodes(resolve_missing=True)]
        if len(road) > 0:
            ways_coords.append(road)
    return ways_coords
