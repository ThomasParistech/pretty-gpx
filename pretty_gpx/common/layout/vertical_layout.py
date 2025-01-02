#!/usr/bin/python3
"""Vertical Layout centered on a GPX Track."""
from dataclasses import dataclass

from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.asserts import assert_in_range


@dataclass(kw_only=True)
class VerticalLayout:
    """Vertical Layout centered on a GPX Track.

    ┌────────────────────────────────────────┐   ▲
    │                                        │   │   Top Ratio
    ├───────────────────┬────────────────────┤   ▼
    │                   │  margin_ratio      │   
    │                   ▼                    │   
    │                 ...............        │   
    │                   ..           ...     │   
    │                      .           .◄────┤   
    │                    .....      ....     │   
    │ margin_ratio     ...        ..         │   
    ├────►..............    GPX     ..       │   
    │     .                     ...          │   
    │     ............       ..              │   
    │                ........                │   
    │                   ▲                    │   
    │                   │                    │   
    ├───────────────────┴────────────────────┤   ▲
    │                                        │   │
    │                                        │   │   Bot Ratio
    │                                        │   │
    └────────────────────────────────────────┘   ▼
    """
    background_bounds: GpxBounds
    top_ratio: float
    bot_ratio: float

    @property
    def top_bounds(self) -> GpxBounds:
        """GPX Bounds for the Top Area."""
        top_mid_lat = self.background_bounds.lat_max - self.top_ratio*self.background_bounds.dlat
        return GpxBounds(lon_min=self.background_bounds.lon_min, lon_max=self.background_bounds.lon_max,
                         lat_min=top_mid_lat, lat_max=self.background_bounds.lat_max)

    @property
    def mid_bounds(self) -> GpxBounds:
        """GPX Bounds for the Middle Area."""
        top_mid_lat = self.background_bounds.lat_max - self.top_ratio*self.background_bounds.dlat
        bot_mid_lat = self.background_bounds.lat_min + self.bot_ratio*self.background_bounds.dlat
        return GpxBounds(lon_min=self.background_bounds.lon_min, lon_max=self.background_bounds.lon_max,
                         lat_min=bot_mid_lat, lat_max=top_mid_lat)

    @property
    def bot_bounds(self) -> GpxBounds:
        """GPX Bounds for the Bottom Area."""
        bot_mid_lat = self.background_bounds.lat_min + self.bot_ratio*self.background_bounds.dlat
        return GpxBounds(lon_min=self.background_bounds.lon_min, lon_max=self.background_bounds.lon_max,
                         lat_min=self.background_bounds.lat_min, lat_max=bot_mid_lat)

    @staticmethod
    def from_track(gpx_track: GpxTrack,
                   paper: PaperSize,
                   top_ratio: float,
                   bot_ratio: float,
                   margin_ratio: float) -> 'VerticalLayout':
        """Find the Background Bounds to center the GPX Track based on the specified top, bottom and margin ratios."""
        # Remove the margins
        background_w_mm = (paper.w_mm - 2*paper.margin_mm)
        background_h_mm = (paper.h_mm - 2*paper.margin_mm)

        # Track area
        middle_ratio = 1. - top_ratio - bot_ratio
        assert_in_range(middle_ratio, 0.2, 0.8)
        track_w_mm = background_w_mm
        track_h_mm = background_h_mm * middle_ratio

        # Tight Track area (after removing the margins)
        tight_w_mm = track_w_mm * (1. - 2*margin_ratio)
        tight_h_mm = track_h_mm * (1. - 2*margin_ratio)

        # Analyze the GPX track
        bounds = gpx_track.get_bounds()

        # Aspect ratio of the lat/lon map
        latlon_aspect_ratio = bounds.latlon_aspect_ratio

        # Tight fit
        lat_deg_per_mm = max(
            bounds.dlon / (tight_w_mm * latlon_aspect_ratio),  # Track touching left/right of tight area
            bounds.dlat / tight_h_mm  # Track touching bot/top of tight area
        )

        # Compute the Background Bounds
        background_dlon = background_w_mm * lat_deg_per_mm * latlon_aspect_ratio
        background_dlat = background_h_mm * lat_deg_per_mm

        lat_offset = background_dlat*((top_ratio+0.5*middle_ratio) - 0.5)

        background_bounds = GpxBounds.from_center(lon_center=bounds.lon_center, dlon=background_dlon,
                                                  lat_center=bounds.lat_center + lat_offset, dlat=background_dlat)

        return VerticalLayout(background_bounds=background_bounds, top_ratio=top_ratio, bot_ratio=bot_ratio)


@dataclass
class VerticalLayoutUnion:
    """Union of Vertical Layouts for different Paper Sizes."""
    layouts: dict[PaperSize, VerticalLayout]
    union_bounds: GpxBounds

    @staticmethod
    def from_track(gpx_track: GpxTrack,
                   *,
                   top_ratio: float,
                   bot_ratio: float,
                   margin_ratio: float) -> 'VerticalLayoutUnion':
        """Store the Vertical Layouts for different Paper Sizes and take the union of the Background Bounds."""
        layouts = {paper: VerticalLayout.from_track(gpx_track, paper, top_ratio, bot_ratio, margin_ratio)
                   for paper in PAPER_SIZES.values()}
        return VerticalLayoutUnion(layouts=layouts,
                                   union_bounds=GpxBounds.union([layout.background_bounds
                                                                 for layout in layouts.values()]))
