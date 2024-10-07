#!/usr/bin/python3
"""Railways."""
import os

import numpy as np

from pretty_gpx.common.data.overpass_processing import get_ways_coordinates_from_results
from pretty_gpx.common.data.overpass_processing import merge_ways
from pretty_gpx.common.data.overpass_request import ListLonLat
from pretty_gpx.common.data.overpass_request import OverpassQuery
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_data_cache_handler import GpxDataCacheHandler
from pretty_gpx.common.utils.pickle_io import read_pickle
from pretty_gpx.common.utils.pickle_io import write_pickle
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import EARTH_RADIUS_M

RAILWAYS_CACHE = GpxDataCacheHandler(name='railways', extension='.pkl')


RAILWAYS_ARRAY_NAME = "railways"


@profile
def prepare_download_city_railways(query: OverpassQuery,
                                   bounds: GpxBounds) -> None:
    """Download railways from OpenStreetMap.

    Args:
        query: OverpassQuery class that merge all queries into a single one
        bounds: GPX bounds

    Returns:
        List of roads (sequence of lon, lat coordinates) for each road type
    """
    cache_pkl = RAILWAYS_CACHE.get_path(bounds)

    if os.path.isfile(cache_pkl):
        query.add_cached_result(RAILWAYS_CACHE.name, cache_file=cache_pkl)
    else:
        query.add_overpass_query(RAILWAYS_ARRAY_NAME,
                                 ["way['railway'~'rail'][!'tunnel']['usage'='main']"],
                                 bounds,
                                 include_way_nodes=True,
                                 add_relative_margin=None)


@profile
def process_city_railways(query: OverpassQuery,
                          bounds: GpxBounds,
                          latlon_aspect_ratio: float) -> tuple[list[ListLonLat],list[ListLonLat]]:
    """Query the overpass API to get the roads of a city."""
    if query.is_cached(RAILWAYS_CACHE.name):
        cache_file = query.get_cache_file(RAILWAYS_CACHE.name)
        railways, sleepers = read_pickle(cache_file)
    else:
        with Profiling.Scope("Process railways"):
            result = query.get_query_result(RAILWAYS_ARRAY_NAME)
            railways = get_ways_coordinates_from_results(result)
            railways = merge_ways(railways,eps=1e-6)
            sleepers = []
            # To calculate the size of the sleeper and the distance between sleepers
            # We need to have a caracteristic length in the picture
            caracteristic_length = (bounds.dx_m**2 + bounds.dy_m**2)**0.5
            sleeper_length = caracteristic_length*1.25e-6
            sleeper_distance = sleeper_length*50
            with Profiling.Scope("Generate sleepers"):
                for railway in railways:
                    sleepers += generate_evenly_spaced_sleepers(railway,
                                                                lat_lon_aspect_ratio=latlon_aspect_ratio,
                                                                sleeper_distance=sleeper_distance,
                                                                sleeper_length=sleeper_length)
        cache_pkl = RAILWAYS_CACHE.get_path(bounds)
        write_pickle(cache_pkl, (railways, sleepers))
        query.add_cached_result(RAILWAYS_CACHE.name, cache_file=cache_pkl)
    return railways, sleepers



def generate_evenly_spaced_sleepers(coordinates: list[tuple[float, float]],
                                    lat_lon_aspect_ratio: float,
                                    sleeper_distance: float=0.5,
                                    sleeper_length: float=0.1) -> list[ListLonLat]:
    """Generate sleepers to distinguish rails from roads.
    
    For railways, sleepers are created so that railways are distinguished on the map,
    They are evenly spaced by sleeper_distance in meters and sleeper_length in meters.
    """
    # Convert meters to the lat lon degrees
    meters_to_degrees = 180.0/(EARTH_RADIUS_M*np.pi)
    degrees_to_meters = 1/meters_to_degrees

    segments: list[ListLonLat] = []
    total_distance = 0
    next_sleeper_distance = sleeper_distance*meters_to_degrees
    sleeper_length = sleeper_length*meters_to_degrees

    for i in range(1, len(coordinates)):
        # Extract the longitude and latitude values from the coordinate tuple
        x1, y1 = coordinates[i - 1]
        x2, y2 = coordinates[i]

        # Compute distance between consecutive points
        dx = (x2 - x1)*degrees_to_meters/lat_lon_aspect_ratio
        dy = (y2 - y1)*degrees_to_meters
        distance = np.hypot(dx, dy)
        total_distance += distance

        while total_distance >= next_sleeper_distance:
            # interpolate along the segment
            t = (next_sleeper_distance - (total_distance - distance)) / distance
            sleeper_x = x1 + t * (x2 - x1)
            sleeper_y = y1 + t * (y2 - y1)

            # Get the perpendicular direction
            dx_grad = np.gradient([x[0] for x in coordinates])[i]/lat_lon_aspect_ratio
            dy_grad = np.gradient([x[1] for x in coordinates])[i]
            length  = np.hypot(dx_grad, dy_grad)
            if length != 0:
                perp_dx = -dy_grad / length * sleeper_length
                perp_dy = dx_grad / length * sleeper_length

                segments.append([(sleeper_x - perp_dx, sleeper_y - perp_dy),
                                 (sleeper_x + perp_dx, sleeper_y + perp_dy)])

            # Update the distance for the next sleeper
            next_sleeper_distance += sleeper_distance

    return segments
