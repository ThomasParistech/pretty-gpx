#!/usr/bin/python3
"""Poster Image Cache."""
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import PlotData
from pretty_gpx.common.drawing.drawing_data import PolyFillData
from pretty_gpx.common.drawing.drawing_data import ScatterData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.drawing.text_allocation import allocate_text
from pretty_gpx.common.drawing.text_allocation import AnnotatedScatterDataCollection
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import mm_to_inch
from pretty_gpx.mountain.data.augmented_gpx_data import AugmentedGpxData
from pretty_gpx.mountain.data.elevation_map import download_elevation_map
from pretty_gpx.mountain.data.elevation_map import rescale_elevation
from pretty_gpx.mountain.drawing.hillshading import CachedHillShading
from pretty_gpx.mountain.drawing.mountain_drawing_figure import MountainDrawingFigure
from pretty_gpx.mountain.drawing.mountain_drawing_params import MountainDrawingSizeParams
from pretty_gpx.mountain.drawing.mountain_drawing_params import MountainDrawingStyleParams
from pretty_gpx.mountain.drawing.theme_colors import hex_to_rgb
from pretty_gpx.mountain.drawing.theme_colors import ThemeColors
from pretty_gpx.mountain.mountain_vertical_layout import MountainVerticalLayout

W_DISPLAY_PIX = 800  # Display width of the preview (in pix)

WORKING_DPI = 50  # DPI of the poster's preview
HIGH_RES_DPI = 400  # DPI of the final poster


@dataclass
class PosterImageCaches:
    """Low and High resolution PosterImageCache."""
    low_res: 'PosterImageCache'
    high_res: 'PosterImageCache'

    gpx_data: AugmentedGpxData

    def __post_init__(self) -> None:
        assert self.low_res.dpi < self.high_res.dpi

    @staticmethod
    def from_gpx(list_gpx_path: str | bytes | list[str] | list[bytes],
                 paper_size: PaperSize) -> 'PosterImageCaches':
        """Create a PosterImageCaches from a GPX file."""
        # Extract GPX data and retrieve close mountain passes/huts
        gpx_data = AugmentedGpxData.from_path(list_gpx_path)
        return PosterImageCaches.from_augmented_gpx_data(gpx_data, paper_size)

    @staticmethod
    def from_augmented_gpx_data(gpx_data: AugmentedGpxData,
                                paper_size: PaperSize) -> 'PosterImageCaches':
        """Create a PosterImageCaches from a GPX file."""
        high_res = PosterImageCache.from_gpx_data(gpx_data, dpi=HIGH_RES_DPI, paper=paper_size)
        low_res = high_res.change_dpi(WORKING_DPI)
        return PosterImageCaches(low_res=low_res, high_res=high_res, gpx_data=gpx_data)


@dataclass
class PosterDrawingData:
    """Drawing data for the poster."""
    img: np.ndarray
    theme_colors: ThemeColors
    title_txt: str
    stats_text: str


@dataclass
class PosterImageCache:
    """Class leveraging cache to avoid reprocessing GPX when chaning color them, title, sun azimuth..."""

    elevation_map: np.ndarray
    elevation_shading: CachedHillShading

    stats_dist_km: float
    stats_uphill_m: float

    plotter: MountainDrawingFigure

    dpi: float

    @profile
    @staticmethod
    def from_gpx_data(gpx_data: AugmentedGpxData,
                      paper: PaperSize,
                      layout: MountainVerticalLayout = MountainVerticalLayout(),
                      dpi: float = HIGH_RES_DPI) -> 'PosterImageCache':
        """Create a PosterImageCache from a GPX file."""
        # Download the elevation map at the correct layout
        img_bounds, paper_fig = layout.get_download_bounds_and_paper_figure(gpx_data.track, paper)
        elevation = download_elevation_map(img_bounds)

        # Rescale the elevation map to the target DPI
        elevation = rescale_elevation_to_dpi(elevation, img_bounds, paper_fig, dpi)

        # Use default drawing params
        drawing_size_params = MountainDrawingSizeParams.default(paper)
        drawing_style_params = MountainDrawingStyleParams()

        plotter = init_and_populate_drawing_figure(gpx_data, paper_fig, img_bounds, layout, drawing_size_params,
                                                   drawing_style_params)

        logger.info("Successful GPX Processing")
        return PosterImageCache(elevation_map=elevation,
                                elevation_shading=CachedHillShading(elevation),
                                stats_dist_km=gpx_data.dist_km,
                                stats_uphill_m=gpx_data.uphill_m,
                                plotter=plotter,
                                dpi=dpi)

    @profile
    def change_dpi(self, dpi: float) -> 'PosterImageCache':
        """Scale the elevation map to a new DPI."""
        new_ele_map = rescale_elevation_to_dpi(self.elevation_map, self.plotter.img_gpx_bounds, self.plotter, dpi)
        return PosterImageCache(elevation_map=new_ele_map,
                                elevation_shading=CachedHillShading(new_ele_map),
                                stats_dist_km=self.stats_dist_km,
                                stats_uphill_m=self.stats_uphill_m,
                                plotter=self.plotter,
                                dpi=dpi)

    def update_drawing_data(self,
                            azimuth: int,
                            theme_colors: ThemeColors,
                            title_txt: str,
                            uphill_m: str,
                            dist_km: str) -> PosterDrawingData:
        """Update the drawing data (can run in a separate thread)."""
        grey_hillshade = self.elevation_shading.render_grey(azimuth)[..., None]
        background_color_rgb = hex_to_rgb(theme_colors.background_color)
        color_0 = (0, 0, 0) if theme_colors.dark_mode else background_color_rgb
        color_1 = background_color_rgb if theme_colors.dark_mode else (255, 255, 255)
        colored_hillshade = grey_hillshade * (np.array(color_1) - np.array(color_0)) + np.array(color_0)

        img = colored_hillshade.astype(np.uint8)

        dist_km_int = int(dist_km if dist_km != '' else self.stats_dist_km)
        uphill_m_int = int(uphill_m if uphill_m != '' else self.stats_uphill_m)
        stats_text = f"{dist_km_int} km - {uphill_m_int} m D+"

        return PosterDrawingData(img, theme_colors, title_txt=title_txt, stats_text=stats_text)

    @profile
    def draw(self, fig: Figure, ax: Axes, poster_drawing_data: PosterDrawingData) -> None:
        """Draw the updated drawing data (Must run in the main thread because of matplotlib backend)."""
        self.plotter.draw(fig, ax,
                          poster_drawing_data.img,
                          poster_drawing_data.theme_colors,
                          poster_drawing_data.title_txt,
                          poster_drawing_data.stats_text)
        logger.info("Drawing updated "
                    f"(Elevation Map {poster_drawing_data.img.shape[1]}x{poster_drawing_data.img.shape[0]})")


def init_and_populate_drawing_figure(gpx_data: AugmentedGpxData,
                                     paper_fig: BaseDrawingFigure,
                                     img_gpx_bounds: GpxBounds,
                                     layout: MountainVerticalLayout,
                                     drawing_size_params: MountainDrawingSizeParams,
                                     drawing_style_params: MountainDrawingStyleParams
                                     ) -> MountainDrawingFigure:
    """Set up and populate the DrawingFigure for the poster."""
    list_x = gpx_data.track.list_lon
    list_y = gpx_data.track.list_lat

    b = paper_fig.gpx_bounds

    scatters = init_annotated_scatter_collection(gpx_data, list_x, list_y, drawing_style_params, drawing_size_params)

    plots_x_to_avoid, plots_y_to_avoid = [list_x], [list_y]

    for y in b.lat_min+b.dlat*np.concatenate((np.linspace(0., layout.stats_relative_h + layout.elevation_relative_h,
                                                          num=10, endpoint=True),  # Stats+Elevation area
                                              np.linspace(1.0-layout.title_relative_h, 1.0,
                                                          num=10, endpoint=True))):  # Title area
        plots_x_to_avoid.append([b.lon_min, b.lon_max])
        plots_y_to_avoid.append([y, y])

    texts, lines = allocate_text(fig=plt.gcf(),
                                 ax=plt.gca(),
                                 base_fig=paper_fig,
                                 scatters=scatters,
                                 plots_x_to_avoid=plots_x_to_avoid,
                                 plots_y_to_avoid=plots_y_to_avoid,
                                 output_linewidth=drawing_size_params.text_arrow_linewidth,
                                 fontsize=drawing_size_params.text_fontsize,
                                 fontproperties=drawing_style_params.classic_font)

    # Draw the elevation profile
    draw_start = gpx_data.start_name is not None
    draw_end = draw_start if gpx_data.is_closed else gpx_data.end_name is not None
    ele_scatter, ele_fill_poly, stats = get_elevation_drawings(layout=layout,
                                                               b=b,
                                                               list_ele=gpx_data.track.list_ele_m,
                                                               list_cum_d=gpx_data.track.list_cumul_dist_km,
                                                               passes_ids=gpx_data.passes_ids,
                                                               huts_ids=gpx_data.hut_ids,
                                                               draw_start=draw_start,
                                                               draw_end=draw_end,
                                                               drawing_style_params=drawing_style_params,
                                                               drawing_size_params=drawing_size_params)

    # Prepare the plot data
    augmented_hut_ids = [0] + gpx_data.hut_ids
    track_data: list[BaseDrawingData] = []
    for k in range(len(augmented_hut_ids)):
        begin_i = augmented_hut_ids[k]
        end_i = augmented_hut_ids[k+1] if k+1 < len(augmented_hut_ids) else None

        track_data.append(PlotData(x=list_x[begin_i:end_i],
                                   y=list_y[begin_i:end_i],
                                   linewidth=drawing_size_params.track_linewidth))
        if k != 0:
            # Draw dotted line between huts, in case there's a visible gap
            track_data.append(PlotData(x=[list_x[begin_i-1], list_x[begin_i]],
                                       y=[list_y[begin_i-1], list_y[begin_i]],
                                       linewidth=0.5*drawing_size_params.track_linewidth,
                                       linestyle="dotted"))

    track_data.append(ele_fill_poly)

    peak_data: list[BaseDrawingData] = ele_scatter + scatters.list_scatter_data + texts + lines  # type:ignore

    title = TextData(x=b.lon_center, y=b.lat_max - 0.8 * b.dlat * layout.title_relative_h,
                     s="", fontsize=drawing_size_params.title_fontsize,
                     fontproperties=drawing_style_params.pretty_font, ha="center")

    return MountainDrawingFigure(paper_size=paper_fig.paper_size,
                                 latlon_aspect_ratio=paper_fig.latlon_aspect_ratio,
                                 gpx_bounds=paper_fig.gpx_bounds,
                                 w_display_pix=W_DISPLAY_PIX,
                                 track_data=track_data,
                                 peak_data=peak_data,
                                 title=title,
                                 stats=stats,
                                 img_gpx_bounds=img_gpx_bounds)


def init_annotated_scatter_collection(gpx_data: AugmentedGpxData,
                                      global_list_x: list[float],
                                      global_list_y: list[float],
                                      drawing_style_params: MountainDrawingStyleParams,
                                      drawing_size_params: MountainDrawingSizeParams) -> AnnotatedScatterDataCollection:
    """Initialize the AnnotatedScatterDataCollection with the mountain passes, huts, start and end markers."""
    scatter_collection = AnnotatedScatterDataCollection()

    scatter_collection.add_scatter_data(global_x=global_list_x, global_y=global_list_y,
                                        scatter_ids=gpx_data.passes_ids,
                                        scatter_texts=[f" {mountain_pass.name} \n({int(mountain_pass.ele)} m)"
                                                       for mountain_pass in gpx_data.mountain_passes],
                                        marker=drawing_style_params.peak_marker,
                                        markersize=drawing_size_params.peak_markersize)

    scatter_collection.add_scatter_data(global_x=global_list_x, global_y=global_list_y,
                                        scatter_ids=gpx_data.hut_ids,
                                        scatter_texts=[f" {mountain_hut.name} "
                                                       if mountain_hut.name is not None else None
                                                       for mountain_hut in gpx_data.huts],
                                        marker=drawing_style_params.hut_marker,
                                        markersize=drawing_size_params.hut_markersize)

    if gpx_data.start_name is not None:
        scatter_collection.add_scatter_data(global_x=global_list_x, global_y=global_list_y,
                                            scatter_ids=[0],
                                            scatter_texts=[f" {gpx_data.start_name} "],
                                            marker=drawing_style_params.start_marker,
                                            markersize=drawing_size_params.start_markersize)

    if gpx_data.end_name is not None:
        scatter_collection.add_scatter_data(global_x=global_list_x, global_y=global_list_y,
                                            scatter_ids=[len(global_list_x)-1],
                                            scatter_texts=[f" {gpx_data.end_name} "],
                                            marker=drawing_style_params.end_marker,
                                            markersize=drawing_size_params.end_markersize)
    return scatter_collection


def get_elevation_drawings(layout: MountainVerticalLayout,
                           b: GpxBounds,
                           list_ele: list[float],
                           list_cum_d: list[float],
                           passes_ids: list[int],
                           huts_ids: list[int],
                           draw_start: bool,
                           draw_end: bool,
                           drawing_style_params: MountainDrawingStyleParams,
                           drawing_size_params: MountainDrawingSizeParams) -> tuple[list[ScatterData],
                                                                                    PolyFillData,
                                                                                    TextData]:
    """Create the plot elements for the elevation profile."""
    # Elevation Profile
    y_up = b.lat_min + b.dlat * (layout.stats_relative_h + layout.elevation_relative_h)
    y_bot = b.lat_min + b.dlat * layout.stats_relative_h

    elevation_poly_x = b.lon_min + b.dlon*np.array(list_cum_d)/list_cum_d[-1]

    hmin, hmax = np.min(list_ele), np.max(list_ele)
    elevation_poly_y = y_bot + (np.array(list_ele) - hmin) * (y_up-y_bot) / (hmax-hmin)

    # Mountain Passes and Huts
    scatter_data = [
        ScatterData(x=[elevation_poly_x[closest_idx] for closest_idx in ids],
                    y=[elevation_poly_y[closest_idx] for closest_idx in ids],
                    marker=marker, markersize=markersize)
        for ids, marker, markersize in [(passes_ids, drawing_style_params.peak_marker,
                                         drawing_size_params.peak_markersize),
                                        (huts_ids, drawing_style_params.hut_marker,
                                         drawing_size_params.hut_markersize)]
    ]

    # Start and End
    if draw_start:
        scatter_data.append(ScatterData(x=[elevation_poly_x[0]], y=[elevation_poly_y[0]],
                                        marker=drawing_style_params.start_marker,
                                        markersize=drawing_size_params.start_markersize))
    if draw_end:
        scatter_data.append(ScatterData(x=[elevation_poly_x[-1]], y=[elevation_poly_y[-1]],
                                        marker=drawing_style_params.end_marker,
                                        markersize=drawing_size_params.end_markersize))

    # Complete the polygon for the elevation profile
    elevation_poly_x = np.hstack((b.lon_min, b.lon_min, elevation_poly_x, b.lon_max, b.lon_max))
    elevation_poly_y = np.hstack((b.lat_min, y_bot, elevation_poly_y, y_bot, b.lat_min))
    elevation_data = PolyFillData(x=elevation_poly_x.tolist(), y=elevation_poly_y.tolist())

    stats = TextData(x=b.lon_center, y=0.5 * (y_bot + b.lat_min),
                     s="", fontsize=drawing_size_params.stats_fontsize,
                     fontproperties=drawing_style_params.pretty_font, ha="center")

    return scatter_data, elevation_data, stats


def rescale_elevation_to_dpi(elevation_map: np.ndarray,
                             img_bounds: GpxBounds,
                             paper_fig: BaseDrawingFigure,
                             target_dpi: float) -> np.ndarray:
    """Rescale the elevation map to a target DPI."""
    paper_h_inches = mm_to_inch(paper_fig.paper_size.h_mm)
    img_h_inches = paper_h_inches * img_bounds.dlat / paper_fig.gpx_bounds.dlat
    current_dpi = elevation_map.shape[0]/img_h_inches
    return rescale_elevation(elevation_map,  target_dpi/current_dpi)
