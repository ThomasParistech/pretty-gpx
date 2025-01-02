#!/usr/bin/python3
"""Context Manager handling the Drawing of various elements on a poster."""
from types import TracebackType
from typing import Literal

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.collections import PatchCollection
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties

from pretty_gpx.common.drawing.utils.plt_marker import MarkerType
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_distance import ListLonLat
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.request.overpass_processing import SurfacePolygons
from pretty_gpx.common.utils.asserts import assert_ge
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import mm_to_inch
from pretty_gpx.common.utils.utils import mm_to_point


class A4Float:
    """Scales a millimeter measurement relative to A4 and converts it to points for any paper size."""

    def __init__(self, *, mm: float) -> None:
        self.__val_mm = mm

    def __call__(self, paper_size: PaperSize) -> float:
        """Convert the measurement to points for the given paper size."""
        scale = paper_size.diag_mm/PAPER_SIZES['A4'].diag_mm
        return mm_to_point(self.__val_mm)*scale


class MetersFloat:
    """Scales a meter measurement to points based on paper size and GPX bounds."""

    def __init__(self, *, m: float) -> None:
        self.__val_m = m

    def __call__(self, paper_size: PaperSize, gpx_bounds: GpxBounds) -> float:
        """Convert the measurement to points for the given paper size and GPX bounds."""
        return mm_to_point(self.__val_m * paper_size.diag_mm / gpx_bounds.diagonal_m)


class DrawingFigure:
    """Context Manager handling the Drawing of various elements on a poster."""

    def __init__(self,
                 paper_size: PaperSize,
                 gpx_bounds: GpxBounds,
                 fig: Figure,
                 ax: Axes) -> None:
        self.paper_size = paper_size
        self.__gpx_bounds = gpx_bounds
        self.__fig = fig
        self.__ax = ax
        self.__is_open = False

    @profile
    def __enter__(self) -> 'DrawingFigure':
        """Set up the Drawing Figure from the given Paper Size and GPX Bounds."""
        self.__ax.cla()
        self.__ax.axis('off')

        self.__ax.add_artist(self.__ax.patch)  # Keep the background color if set with self.__ax.set_facecolor
        self.__ax.patch.set_zorder(-1)

        self.__fig.tight_layout(pad=0)

        self.__ax.set_xlim((self.__gpx_bounds.lon_min, self.__gpx_bounds.lon_max))
        self.__ax.set_ylim((self.__gpx_bounds.lat_min, self.__gpx_bounds.lat_max))

        self.__ax.set_aspect(self.__gpx_bounds.latlon_aspect_ratio)

        w_inches = mm_to_inch(self.paper_size.w_mm)
        h_inches = mm_to_inch(self.paper_size.h_mm)

        margin_inches = mm_to_inch(self.paper_size.margin_mm)

        self.__fig.set_size_inches(w_inches, h_inches)

        self.__fig.subplots_adjust(left=margin_inches/w_inches, right=1-margin_inches/w_inches,
                                   bottom=margin_inches/h_inches, top=1-margin_inches/h_inches)

        self.__ax.autoscale(False)

        self.__is_open = True
        return self

    def __exit__(self,
                 exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: TracebackType | None) -> None:
        """Exit the context manager and prevent further drawing."""
        self.__is_open = False

    def _eval(self, val: A4Float | MetersFloat) -> float:
        """Evaluate the given A4Float or MetersFloat for the current paper size and GPX bounds."""
        if isinstance(val, A4Float):
            return val(self.paper_size)
        return val(self.paper_size, self.__gpx_bounds)

    @profile
    def imshow(self, *, img: np.ndarray) -> None:
        """Draw an Image matching the GPX bounds."""
        assert self.__is_open
        ratio_img = img.shape[1]/img.shape[0]
        ratio_bounds = self.__gpx_bounds.dlon/self.__gpx_bounds.dlat
        assert_ge(min(ratio_img/ratio_bounds, ratio_bounds/ratio_img), 0.9,
                  msg=f"Image and GpxBounds have different aspect-ratios: {ratio_img: .2f} and {ratio_bounds: .2f}")
        self.__ax.imshow(img,
                         extent=(self.__gpx_bounds.lon_min, self.__gpx_bounds.lon_max,
                                 self.__gpx_bounds.lat_min, self.__gpx_bounds.lat_max),
                         aspect=self.__gpx_bounds.latlon_aspect_ratio)

    @profile
    def background_color(self, color: str) -> None:
        """Set the Background Color."""
        assert self.__is_open
        self.__ax.set_facecolor(color)

    @profile
    def rectangle(self, *,
                  bounds: GpxBounds,
                  color: str,
                  lw: A4Float | MetersFloat,
                  style: Literal["solid", "dashed", "dashdot", "dotted"] = "solid") -> None:
        """Draw a Rectangle around given GPX Bounds."""
        assert self.__is_open
        self.__ax.plot([bounds.lon_min, bounds.lon_max, bounds.lon_max, bounds.lon_min, bounds.lon_min],
                       [bounds.lat_min, bounds.lat_min, bounds.lat_max, bounds.lat_max, bounds.lat_min],
                       linestyle=style, c=color, lw=self._eval(lw))

    @profile
    def text(self, *,
             lon: float,
             lat: float,
             s: str,
             color: str,
             fontsize: A4Float | MetersFloat,
             font: FontProperties,
             ha: str,
             va: str) -> None:
        """Draw Text."""
        assert self.__is_open
        self.__ax.text(lon, lat, s, c=color, fontsize=self._eval(fontsize), fontproperties=font, ha=ha, va=va)

    @profile
    def polyline(self, *,
                 list_lat: list[float],
                 list_lon: list[float],
                 color: str,
                 lw: A4Float | MetersFloat,
                 style: Literal["solid", "dashed", "dashdot", "dotted"] = "solid") -> None:
        """Draw Polyline."""
        assert self.__is_open
        self.__ax.plot(list_lon, list_lat, c=color, lw=self._eval(lw), linestyle=style)

    @profile
    def scatter(self, *,
                list_lat: list[float] | np.ndarray,
                list_lon: list[float] | np.ndarray,
                color: str,
                marker: MarkerType,
                markersize: A4Float | MetersFloat) -> None:
        """Draw Scatter."""
        # Use plt.plot instead of plt.scatter for cleaner markersize handling:
        # plt.plot scales markersize by diameter, plt.scatter scales by area.
        assert self.__is_open
        self.__ax.plot(list_lon, list_lat, c=color,
                       linestyle='', clip_on=False,  # Allow start/end markers to be drawn outside the plot area
                       markersize=self._eval(markersize), marker=marker.path())

    @profile
    def arrow_to_marker(self, *,
                        begin_lat: float,
                        begin_lon: float,
                        marker_lat: float,
                        marker_lon: float,
                        marker_size: A4Float | MetersFloat,
                        color: str,
                        lw: A4Float | MetersFloat) -> None:
        """Draw an Arrow pointing to an existing Marker."""
        assert self.__is_open
        # Don't use ax.arrow as it will be affected by the aspect ratio of the plot
        self.__ax.annotate('',  # Empty text, we're only using the arrow
                           xy=(marker_lon, marker_lat),  # End of the arrow (marker position)
                           xytext=(begin_lon, begin_lat),  # Start of the arrow
                           arrowprops=dict(arrowstyle='-|>',
                                           color=color,
                                           lw=self._eval(lw),
                                           shrinkB=self._eval(marker_size) * 0.7))

    @profile
    def fill(self, *,
             list_lat: list[float] | np.ndarray,
             list_lon: list[float] | np.ndarray,
             color: str,
             alpha: float) -> None:
        """Draw a filled Polygon."""
        assert self.__is_open
        self.__ax.fill(list_lon, list_lat, c=color, alpha=alpha)

    @profile
    def polygon_collection(self, *,
                           lon_lat_polygons: SurfacePolygons,
                           color_patch: str,
                           color_background: str) -> None:
        """Draw a Polygon Collection."""
        assert self.__is_open
        self.__ax.add_collection(PatchCollection(lon_lat_polygons.exterior_polygons,
                                                 facecolor=color_patch,
                                                 edgecolor=None))
        if lon_lat_polygons.interior_polygons is not None and len(lon_lat_polygons.interior_polygons) > 0:
            self.__ax.add_collection(PatchCollection(lon_lat_polygons.interior_polygons,
                                                     facecolor=color_background,
                                                     edgecolor=None))

    @profile
    def line_collection(self, *,
                        lon_lat_lines: list[ListLonLat],
                        color: str,
                        lw: A4Float | MetersFloat) -> None:
        """Draw a Line Collection."""
        assert self.__is_open
        self.__ax.add_collection(LineCollection(lon_lat_lines, colors=color, lw=self._eval(lw), zorder=1))
