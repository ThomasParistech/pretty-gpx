#!/usr/bin/python3
"""Vertical Layout."""
from dataclasses import dataclass
import numpy as np

from pretty_gpx.common.layout.base_vertical_layout import BaseVerticalLayout
from pretty_gpx.common.layout.base_vertical_layout import RelativeYBounds
from pretty_gpx.common.layout.base_vertical_layout import PaperSize
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.utils.utils import lat_lon_to_mercator


@dataclass(kw_only=True)
class CityVerticalLayout(BaseVerticalLayout):
    """City Vertical Layout.

    ┌────────────────────────────────────────┐   ▲
    │                 Title                  │   │   title_relative_h
    ├───────────────────┬────────────────────┤   ▼
    │                   │  margin_rel_h      │   ▲
    │                   ▼                    │   |
    │                 xxxxxxxxxxxxxxx        │   │
    │                   xx           xxx     │   │
    │                      x           x◄────┤   │
    │                    xxxxx      xxxx     │   │
    │ margin_rel_w     xxx        xx         │   │
    ├────►xxxxxxxxxxxxxx            xx       │   │    map_relative_h
    │     x                     xxx          │   │
    │     xxxxxxxxxxxx       xx              │   │
    │                xxxxxxxx                │   │
    │                   ▲                    │   │
    │                   │                    │   ▼
    ├────────────────────────────────────────┤   ▲
    │      Dist / Time / Speed  / Bib        │   │   stats_relative_h
    └────────────────────────────────────────┘   ▼
    """
    title_relative_h: float = 0.18
    map_relative_h: float = 0.7
    stats_relative_h: float = 0.12

    def _get_download_y_bounds(self) -> RelativeYBounds:
        """Get relative Vertical Bounds of the Download Area, e.g. (0.0, 1.0) for the entire paper."""
        # Roads would be hidden by the stats, no need to download this part
        return RelativeYBounds(bot=self.stats_relative_h, top=1.0)

    def _get_track_y_bounds(self) -> RelativeYBounds:
        """Get relative Vertical Bounds of the Track Area."""
        bot = self.stats_relative_h
        return RelativeYBounds(bot=bot, top=bot+self.map_relative_h)

    def _get_track_margin(self) -> float:
        """Get relative Horizonal/Vertical Margin around the Track Area."""
        return 0.08

    def get_download_bounds_mercator(self,
                                     gpx_track: GpxTrack, 
                                     paper: PaperSize) -> tuple[GpxBounds, BaseDrawingFigure]:
        """Get GPX bounds around the GPX track to match the input vertical layout and paper size."""
        # Remove the margins
        paper_w_mm = (paper.w_mm - 2*paper.margin_mm)
        paper_h_mm = (paper.h_mm - 2*paper.margin_mm)

        # Track area
        track_w_mm = paper_w_mm
        track_h_mm = paper_h_mm * self._get_track_y_bounds().height

        # Tight Track area (after removing the margins)
        tight_w_mm = track_w_mm * (1. - 2*self._get_track_margin())
        tight_h_mm = track_h_mm * (1. - 2*self._get_track_margin())
        
        
        bounds = GpxBounds.from_list(list_lon=gpx_track.list_lon,
                                     list_lat=gpx_track.list_lat)

        lat_border = np.array([bounds.lat_min,bounds.lat_max])
        lon_border = np.array([bounds.lon_min,bounds.lon_max])

        x_border,y_border = lat_lon_to_mercator(lat_border,lon_border)

        x_min,x_max = x_border[0],x_border[1]
        y_min,y_max = y_border[0],y_border[1]

        target_w_mm = (paper.w_mm - 2*paper.margin_mm) 
        target_h_mm = (paper.h_mm - 2*paper.margin_mm)

        # Compute the optimal bounds
        map_w_mm = target_w_mm * (1. - 2.*self.margin_relative_w)
        map_h_mm = target_h_mm * (self.map_relative_h - 2*self.margin_relative_h)

        mercator_d_per_mm = max((x_max - x_min)/map_w_mm,
                                (y_max - y_min)/map_h_mm)

        x_center = 0.5*(x_min + x_max)
        y_center = 0.5*(y_min + y_max)

        new_dx = mercator_d_per_mm * target_w_mm
        new_dy = mercator_d_per_mm * target_h_mm

        new_x_min = x_center - new_dx * 0.5
        new_x_max = x_center + new_dx * 0.5
        new_y_min = y_center - new_dy * 0.5*self.map_relative_h
        new_y_max = y_center + new_dy * 0.5*self.map_relative_h


        R = 6378137 #earth radius
        lon_min = (new_x_min / R) * (180 / np.pi)
        lat_min = (np.arctan(np.sinh(new_y_min / R))) * (180 / np.pi)
        lon_max = (new_x_max / R) * (180 / np.pi)
        lat_max = (np.arctan(np.sinh(new_y_max / R))) * (180 / np.pi)

        optimal_bounds = GpxBounds(lon_min=lon_min,
                                   lon_max=lon_max,
                                   lat_min=lat_min,
                                   lat_max=lat_max)

        return optimal_bounds