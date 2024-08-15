#!/usr/bin/python3
"""Vertical Layout."""
from dataclasses import dataclass

import numpy as np

from pretty_gpx.gpx.gpx_bounds import GpxBounds
from pretty_gpx.gpx.gpx_track import GpxTrack
from pretty_gpx.layout.paper_size import PaperSize


@dataclass
class VerticalLayout:
    """Vertical Layout.

    ┌────────────────────────────────────────┐   ▲
    │                                        │   │
    │                                        │   │
    │                 Title                  │   │   title_relative_h
    │                                        │   │
    ├───────────────────┬────────────────────┤   ▼
    │                   │  margin_rel_h      │   ▲
    │                   ▼                    │   |
    │                 xxxxxxxxxxxxxxx        │   │
    │                   xx           xxx     │   │
    │                      x           x◄────┤   │
    │                    xxxxx      xxxx     │   │
    │ margin_rel_w     xxx        xx         │   │
    ├────►xxxxxxxxxxxxxx            xx       │   │    map_relative_h
    │     x                      xx          │   │
    │     x                  xxxx            │   │
    │     xxxxxxxxxxxx      xx               │   │
    │                xxxxxxxx                │   │
    │                   ▲                    │   │
    │                   │                    │   ▼
    ├───────────────────┴────────────────────┤   ▲
    │         xxx          xxx         xx    │   |
    │  xxx  xxx  xx      xx  xx      xx xx   │   │   elevation_relative_h
    │xxx xxxx     xxxxxxx     xxxxxxxx   xxxx│   │
    ├────────────────────────────────────────┤   ▼
    │                                        │
    │           100km - 1000m D+             │
    │                                        │
    └────────────────────────────────────────┘
    """
    margin_relative_w: float = 0.08
    margin_relative_h: float = 0.08

    title_relative_h: float = 0.18
    map_relative_h: float = 0.6
    elevation_relative_h: float = 0.1

    def __post_init__(self) -> None:
        assert self.title_relative_h + self.map_relative_h + self.elevation_relative_h <= 0.9


def get_bounds(gpx_track: GpxTrack, layout: VerticalLayout, paper: PaperSize) -> tuple[GpxBounds, float]:
    """Get GPX bounds around the GPX track to match the input vertical layout and paper size."""
    bounds = GpxBounds.from_list(list_lon=gpx_track.list_lon,
                                 list_lat=gpx_track.list_lat)

    # Compute the aspect ratio of the lat/lon map
    avg_lat = 0.5*(bounds.lat_min + bounds.lat_max)
    latlon_aspect_ratio = 1.0/np.cos(np.deg2rad(avg_lat))

    target_w_mm = paper.w_mm * latlon_aspect_ratio
    target_h_mm = paper.h_mm

    # Compute the optimal bounds
    map_w_mm = target_w_mm * (1. - 2.*layout.margin_relative_w)
    map_h_mm = target_h_mm * (layout.map_relative_h - 2*layout.margin_relative_h)

    deg_per_mm = max((bounds.lon_max - bounds.lon_min)/map_w_mm,
                     (bounds.lat_max - bounds.lat_min)/map_h_mm)

    lon_center = 0.5*(bounds.lon_max + bounds.lon_min)
    lat_center = 0.5*(bounds.lat_max + bounds.lat_min)

    new_dlon = deg_per_mm * target_w_mm
    new_dlat = deg_per_mm * target_h_mm

    new_lon_min = lon_center - new_dlon * 0.5
    new_lat_min = lat_center - new_dlat * (1. - (layout.title_relative_h + 0.5*layout.map_relative_h))

    optimal_bounds = GpxBounds(lon_min=new_lon_min,
                               lon_max=new_lon_min + new_dlon,
                               lat_min=new_lat_min,
                               lat_max=new_lat_min + new_dlat)

    return optimal_bounds, latlon_aspect_ratio
