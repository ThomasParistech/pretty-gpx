#!/usr/bin/python3
"""Base Vertical Layout."""
from dataclasses import dataclass
from dataclasses import fields
from typing import ClassVar

import matplotlib.pyplot as plt

from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.asserts import assert_float_eq
from pretty_gpx.common.utils.asserts import assert_in_range
from pretty_gpx.common.utils.asserts import assert_lt

DEBUG = False


@dataclass(init=False, kw_only=True)
class BaseVerticalLayout:
    """Abstract Vertical Layout.

    ┌─────────────────────┐ ▲ Paper Area
    │                     │ |
    │─────────────────────│ |   ▲ Download Area
    │                     │ |   |
    │                     │ |   |
    │                     │ |   |
    │─────────────────────│ |   |   ▲ Track Area
    │                     │ |   |   |
    │      GPX Track      │ |   |   |
    │─────────────────────│ |   |   ▼
    │                     │ |   |
    │─────────────────────│ |   ▼
    │                     │ |
    │                     │ |
    └─────────────────────┘ ▼

    The paper is vertically divided into three nested areas:
        - Paper area: Entire surface of the paper, encompassing all other areas
        - Download area: Display area where additional data surrounding the track (elevation, roads) will be downloaded
        - Track area: Area inside the Download Area tighly containing the GPX track

    The `get_download_bounds_and_paper_figure` method determines the largest scale at which the GPX track can be
    displayed while still fitting within the Track area and its relative margin. It then calculates the corresponding
    GPX bounds for the Download and Paper areas based on this scale.

    The areas are parametrized using relative coordinates through methods that must be implemented by the child classes:
        - `_get_download_y_bounds`: Relative Vertical Bounds of the Download Area, e.g. (0.0, 1.0) for the entire paper
        - `_get_track_y_bounds`: Relative Vertical Bounds of the Track Area
        - `_get_track_margin`: Relative Horizonal/Vertical Margin inside the Track Area

    Origin is at the top-left corner of the paper.
    Coordinates are relative w.r.t the paper true shape and range from 0 to 1.

    ▲ Y
    |
    └───► X
    """

    # Class attribute to be defined by child classes
    _LAYOUTS: ClassVar[set[str]] = set()

    @classmethod
    def get_max_download_bounds_across_layouts(cls,
                                               gpx_track: GpxTrack,
                                               paper: PaperSize) -> GpxBounds:
        """Get maximum possible GPX bounds by trying all available layouts, considering X and Y independently."""
        max_dlon = 0.0
        max_dlat = 0.0
        max_x_layout_name = None
        max_y_layout_name = None

        bounds_by_layout = {}

        # Get all layout methods
        layout_methods = {name: getattr(cls, name) for name in cls._LAYOUTS}

        for layout_name, layout_method in layout_methods.items():
            layout : BaseVerticalLayout = layout_method()
            bounds = layout.get_layout_download_bounds(gpx_track, paper)

            bounds_by_layout[layout_name] = bounds

            if bounds.dlon > max_dlon:
                max_dlon = bounds.dlon
                max_x_layout_name = layout_name

            if bounds.dlat > max_dlat:
                max_dlat = bounds.dlat
                max_y_layout_name = layout_name

        if max_x_layout_name is None or max_y_layout_name is None:
            raise ValueError("No valid layouts found")

        # Get the center points from the bounds that gave us max X and Y
        x_center = bounds_by_layout[max_x_layout_name].lon_center
        y_center = bounds_by_layout[max_y_layout_name].lat_center

        # Create the final maximum bounds combining the largest X and Y extents
        max_bounds = GpxBounds.from_center(
            lon_center=x_center,
            lat_center=y_center,
            dlon=max_dlon,
            dlat=max_dlat
        )

        return max_bounds

    ######### METHODS TO IMPLEMENT #########

    def _get_download_y_bounds(self) -> 'RelativeYBounds':
        """Get relative Vertical Bounds of the Download Area, e.g. (0.0, 1.0) for the entire paper."""
        raise NotImplementedError("Subclass must implement this method")

    def _get_track_y_bounds(self) -> 'RelativeYBounds':
        """Get relative Vertical Bounds of the Track Area."""
        raise NotImplementedError("Subclass must implement this method")

    def _get_track_margin(self) -> float:
        """Get relative Horizonal/Vertical Margin inside the Track Area."""
        raise NotImplementedError("Subclass must implement this method")

    #########################################

    def __post_init__(self) -> None:
        """Verify sum of fields is 1.0 and that all layout methods are accounted for."""
        # Check fields sum to 1.0
        sum_fields = 0.0
        for f in fields(self):
            val = getattr(self, f.name)
            assert isinstance(val, float), f"Field {f.name} must be a float"
            sum_fields += val

        assert_float_eq(sum_fields, 1.0, msg="Sum of fields must be 1.0")

        # Verify layouts
        layout_methods = {name for name, method in self.__class__.__dict__.items()
                         if isinstance(method, staticmethod)
                         and name != 'get_layout_with_largest_map_and_title'
                         and not name.startswith('_')}

        missing_layouts = layout_methods - self.__class__._LAYOUTS
        extra_layouts = self.__class__._LAYOUTS - layout_methods

        if missing_layouts:
            raise ValueError(f"Layout methods {missing_layouts} exist but are not included in _LAYOUTS")
        if extra_layouts:
            raise ValueError(f"Layouts {extra_layouts} are included in _LAYOUTS but don't exist as methods")


    def get_layout_download_bounds(self,
                                   gpx_track: GpxTrack,
                                   paper: PaperSize) -> GpxBounds:
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

        # Analyze the GPX track
        bounds = gpx_track.get_bounds()

        # Aspect ratio of the lat/lon map
        latlon_aspect_ratio = bounds.latlon_aspect_ratio

        # Tight fit
        lat_deg_per_mm = max(
            bounds.dlon / (tight_w_mm * latlon_aspect_ratio),  # Track touching left/right of tight area
            bounds.dlat / tight_h_mm  # Track touching bot/top of tight area
        )

        # Compute the Paper Bounds
        paper_dlon = paper_w_mm * lat_deg_per_mm * latlon_aspect_ratio
        paper_dlat = paper_h_mm * lat_deg_per_mm

        # Compute the Download Bounds
        download_dlon = paper_dlon
        download_dlat = paper_dlat * self._get_download_y_bounds().height

        download_lat_offset = paper_dlat*(self._get_download_y_bounds().center - self._get_track_y_bounds().center)
        download_bounds = GpxBounds.from_center(lon_center=bounds.lon_center,
                                                lat_center=bounds.lat_center + download_lat_offset,
                                                dlon=download_dlon,
                                                dlat=download_dlat)

        return download_bounds


    def get_download_bounds_and_paper_figure(self,
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

        # Analyze the GPX track
        bounds = gpx_track.get_bounds()

        # Aspect ratio of the lat/lon map
        latlon_aspect_ratio = bounds.latlon_aspect_ratio

        # Tight fit
        lat_deg_per_mm = max(
            bounds.dlon / (tight_w_mm * latlon_aspect_ratio),  # Track touching left/right of tight area
            bounds.dlat / tight_h_mm  # Track touching bot/top of tight area
        )

        # Compute the Paper Bounds
        paper_dlon = paper_w_mm * lat_deg_per_mm * latlon_aspect_ratio
        paper_dlat = paper_h_mm * lat_deg_per_mm

        paper_lat_offset = paper_dlat*(0.5 - self._get_track_y_bounds().center)
        paper_bounds = GpxBounds.from_center(lon_center=bounds.lon_center,
                                             lat_center=bounds.lat_center + paper_lat_offset,
                                             dlon=paper_dlon,
                                             dlat=paper_dlat)
        drawing_fig = BaseDrawingFigure(paper, latlon_aspect_ratio, paper_bounds)

        # Get the Download Bounds
        download_bounds = self.get_max_download_bounds_across_layouts(gpx_track=gpx_track,
                                                                      paper=paper)

        if DEBUG:
            _debug(self, paper_bounds, download_bounds, bounds, gpx_track, latlon_aspect_ratio)

        return download_bounds, drawing_fig


@dataclass(kw_only=True)
class RelativeYBounds:
    """Relative Y Bounds."""
    bot: float
    top: float

    def __post_init__(self) -> None:
        assert_lt(self.bot, self.top, msg="Invalid YBounds. Y axis is pointing up")
        assert_in_range(self.bot, 0.0, 1.0, msg="Invalid YBounds. Bot must be in [0, 1]")
        assert_in_range(self.top, 0.0, 1.0, msg="Invalid YBounds. Top must be in [0, 1]")

    @property
    def height(self) -> float:
        """Height."""
        return self.top - self.bot

    @property
    def center(self) -> float:
        """Center."""
        return 0.5*(self.top + self.bot)


def _debug(self: BaseVerticalLayout, paper_bounds: GpxBounds, download_bounds: GpxBounds, bounds: GpxBounds,
           gpx_track: GpxTrack, latlon_aspect_ratio: float) -> None:
    def plot_bounds(b: GpxBounds, label: str) -> None:
        """Plot the bounds."""
        plt.plot([b.lon_min, b.lon_max, b.lon_max, b.lon_min, b.lon_min],
                 [b.lat_min, b.lat_min, b.lat_max, b.lat_max, b.lat_min],
                 label=label)

    def plot_y_bounds(y_bounds: 'RelativeYBounds', label: str) -> None:
        """Plot the Y bounds."""
        plt.axhline(y=paper_bounds.lat_min + paper_bounds.dlat*y_bounds.bot, linestyle='--', label=label)
        plt.axhline(y=paper_bounds.lat_min + paper_bounds.dlat*y_bounds.top, linestyle='--', label=label)

    track_dlon = paper_bounds.dlon
    track_dlat = paper_bounds.dlat * self._get_track_y_bounds().height
    track_bounds = GpxBounds.from_center(lon_center=bounds.lon_center,
                                         lat_center=bounds.lat_center,
                                         dlon=track_dlon,
                                         dlat=track_dlat)
    plot_bounds(paper_bounds, "Paper Bounds")
    plot_bounds(download_bounds, "Download Bounds")
    plot_bounds(track_bounds, "Track Bounds")
    plot_bounds(bounds, "GPX Bounds")
    plt.plot(gpx_track.list_lon, gpx_track.list_lat, label="GPX Track")

    plot_y_bounds(self._get_download_y_bounds(), "Download Y Bounds")
    plot_y_bounds(self._get_track_y_bounds(), "Track Y Bounds")

    plt.gca().set_aspect(latlon_aspect_ratio)
    plt.legend()
    plt.show()
