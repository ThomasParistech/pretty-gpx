#!/usr/bin/python3
"""Poster Image Cache."""
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.drawing.drawing_data import BaseDrawingData
from pretty_gpx.drawing.drawing_data import PlotData
from pretty_gpx.drawing.drawing_data import PolyFillData
from pretty_gpx.drawing.drawing_data import ScatterData
from pretty_gpx.drawing.drawing_data import TextData
from pretty_gpx.drawing.drawing_figure import DrawingFigure
from pretty_gpx.drawing.drawing_params import DrawingSizeParams
from pretty_gpx.drawing.drawing_params import DrawingStyleParams
from pretty_gpx.drawing.hillshading import CachedHillShading
from pretty_gpx.drawing.text_allocation import allocate_text
from pretty_gpx.drawing.text_allocation import AnnotatedScatterDataCollection
from pretty_gpx.drawing.theme_colors import hex_to_rgb
from pretty_gpx.drawing.theme_colors import ThemeColors
from pretty_gpx.gpx.augmented_gpx_data import AugmentedGpxData
from pretty_gpx.gpx.elevation_map import download_elevation_map
from pretty_gpx.gpx.elevation_map import rescale_elevation
from pretty_gpx.layout.paper_size import PaperSize
from pretty_gpx.layout.vertical_layout import get_bounds
from pretty_gpx.layout.vertical_layout import VerticalLayout
from pretty_gpx.utils.logger import logger
from pretty_gpx.utils.utils import mm_to_inch

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

    plotter: DrawingFigure

    dpi: float

    @staticmethod
    def from_gpx_data(gpx_data: AugmentedGpxData,
                      paper: PaperSize,
                      layout: VerticalLayout = VerticalLayout(),
                      dpi: float = HIGH_RES_DPI) -> 'PosterImageCache':
        """Create a PosterImageCache from a GPX file."""
        # Download the elevation map at the correct layout
        bounds, latlon_aspect_ratio = get_bounds(gpx_data.track, layout, paper)
        elevation = download_elevation_map(bounds)

        # Rescale the elevation map to the target DPI
        elevation = rescale_elevation_to_dpi(elevation, paper, dpi)

        # Project the track on the elevation map
        h, w = elevation.shape[:2]
        x_pix, y_pix = gpx_data.track.project_on_image(elevation, bounds)

        # Use default drawing params
        drawing_size_params = DrawingSizeParams.default(paper)
        drawing_style_params = DrawingStyleParams()

        plotter = init_and_populate_drawing_figure(gpx_data, latlon_aspect_ratio, paper, layout, drawing_size_params,
                                                   drawing_style_params, x_pix=x_pix, y_pix=y_pix, w=w, h=h)

        logger.info("Successful GPX Processing")
        return PosterImageCache(elevation_map=elevation,
                                elevation_shading=CachedHillShading(elevation),
                                stats_dist_km=gpx_data.dist_km,
                                stats_uphill_m=gpx_data.uphill_m,
                                plotter=plotter,
                                dpi=dpi)

    def change_dpi(self, dpi: float) -> 'PosterImageCache':
        """Scale the elevation map to a new DPI."""
        new_elevation_map = rescale_elevation_to_dpi(self.elevation_map, self.plotter.paper_size, dpi)
        return PosterImageCache(elevation_map=new_elevation_map,
                                elevation_shading=CachedHillShading(new_elevation_map),
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
                                     latlon_aspect_ratio: float,
                                     paper: PaperSize, layout: VerticalLayout,
                                     drawing_size_params: DrawingSizeParams,
                                     drawing_style_params: DrawingStyleParams,
                                     *,
                                     x_pix: list[float], y_pix: list[float],
                                     w: int, h: int) -> DrawingFigure:
    """Set up and populate the DrawingFigure for the poster."""
    scatters = init_annotated_scatter_collection(gpx_data, x_pix, y_pix, drawing_style_params, drawing_size_params)

    plots_x_to_avoid, plots_y_to_avoid = [x_pix], [y_pix]
    for y in np.concatenate((np.linspace(0., h * layout.title_relative_h, num=10),
                             np.linspace(h * (layout.title_relative_h + layout.map_relative_h), h, num=10))):
        plots_x_to_avoid.append([0., w])
        plots_y_to_avoid.append([y, y])

    texts, lines = allocate_text(fig=plt.gcf(),
                                 ax=plt.gca(),
                                 imshow_img=np.full((h, w), fill_value=np.nan),
                                 paper_size=paper,
                                 scatters=scatters,
                                 plots_x_to_avoid=plots_x_to_avoid,
                                 plots_y_to_avoid=plots_y_to_avoid,
                                 latlon_aspect_ratio=latlon_aspect_ratio,
                                 output_linewidth=drawing_size_params.text_arrow_linewidth,
                                 fontsize=drawing_size_params.text_fontsize,
                                 fontproperties=drawing_style_params.classic_font)

    # Draw the elevation profile
    draw_start = gpx_data.start_name is not None
    draw_end = draw_start if gpx_data.is_closed else gpx_data.end_name is not None
    ele_scatter, ele_fill_poly, stats = get_elevation_drawings(layout=layout,
                                                               h_pix=h, w_pix=w,
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
        track_data.append(PlotData(x=x_pix[begin_i:end_i],
                                   y=y_pix[begin_i:end_i],
                                   linewidth=drawing_size_params.track_linewidth))
        if k != 0:
            # Draw dotted line between huts, in case there's a visible gap
            track_data.append(PlotData(x=[x_pix[begin_i-1], x_pix[begin_i]],
                                       y=[y_pix[begin_i-1], y_pix[begin_i]],
                                       linewidth=0.5*drawing_size_params.track_linewidth,
                                       linestyle="dotted"))

    track_data.append(ele_fill_poly)

    peak_data: list[BaseDrawingData] = ele_scatter + scatters.list_scatter_data + texts + lines  # type:ignore

    title = TextData(x=0.5 * w, y=0.8 * h * layout.title_relative_h,
                     s="", fontsize=drawing_size_params.title_fontsize,
                     fontproperties=drawing_style_params.pretty_font, ha="center")

    return DrawingFigure(ref_img_shape=(h, w),
                         paper_size=paper,
                         w_display_pix=W_DISPLAY_PIX,
                         latlon_aspect_ratio=latlon_aspect_ratio,
                         track_data=track_data,
                         peak_data=peak_data,
                         title=title,
                         stats=stats)


def init_annotated_scatter_collection(gpx_data: AugmentedGpxData,
                                      global_x_pix: list[float],
                                      global_y_pix: list[float],
                                      drawing_style_params: DrawingStyleParams,
                                      drawing_size_params: DrawingSizeParams) -> AnnotatedScatterDataCollection:
    """Initialize the AnnotatedScatterDataCollection with the mountain passes, huts, start and end markers."""
    scatter_collection = AnnotatedScatterDataCollection()

    scatter_collection.add_scatter_data(global_x=global_x_pix, global_y=global_y_pix,
                                        scatter_ids=gpx_data.passes_ids,
                                        scatter_texts=[f" {mountain_pass.name} \n({int(mountain_pass.ele)} m)"
                                                       for mountain_pass in gpx_data.mountain_passes],
                                        marker=drawing_style_params.peak_marker,
                                        markersize=drawing_size_params.peak_markersize)

    scatter_collection.add_scatter_data(global_x=global_x_pix, global_y=global_y_pix,
                                        scatter_ids=gpx_data.hut_ids,
                                        scatter_texts=[f" {mountain_hut.name} "
                                                       for mountain_hut in gpx_data.huts],
                                        marker=drawing_style_params.hut_marker,
                                        markersize=drawing_size_params.hut_markersize)

    if gpx_data.start_name is not None:
        scatter_collection.add_scatter_data(global_x=global_x_pix, global_y=global_y_pix,
                                            scatter_ids=[0],
                                            scatter_texts=[f" {gpx_data.start_name} "],
                                            marker=drawing_style_params.start_marker,
                                            markersize=drawing_size_params.start_markersize)

    if gpx_data.end_name is not None:
        scatter_collection.add_scatter_data(global_x=global_x_pix, global_y=global_y_pix,
                                            scatter_ids=[len(global_x_pix)-1],
                                            scatter_texts=[f" {gpx_data.end_name} "],
                                            marker=drawing_style_params.end_marker,
                                            markersize=drawing_size_params.end_markersize)
    return scatter_collection


def get_elevation_drawings(layout: VerticalLayout,
                           h_pix: int, w_pix: int,
                           list_ele: list[float],
                           list_cum_d: list[float],
                           passes_ids: list[int],
                           huts_ids: list[int],
                           draw_start: bool,
                           draw_end: bool,
                           drawing_style_params: DrawingStyleParams,
                           drawing_size_params: DrawingSizeParams) -> tuple[list[ScatterData], PolyFillData, TextData]:
    """Create the plot elements for the elevation profile."""
    # Elevation Profile
    h_up_pix = h_pix * (layout.title_relative_h + layout.map_relative_h)
    h_bot_pix = h_pix * (layout.title_relative_h + layout.map_relative_h + layout.elevation_relative_h)

    elevation_poly_x = np.array(list_cum_d)/list_cum_d[-1]*w_pix

    hmin, hmax = np.min(list_ele), np.max(list_ele)
    elevation_poly_y = h_bot_pix + (np.array(list_ele) -
                                    hmin) * (h_up_pix-h_bot_pix) / (hmax-hmin)

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
    elevation_poly_x = np.hstack((0, 0, elevation_poly_x, w_pix, w_pix))
    elevation_poly_y = np.hstack((h_pix, h_bot_pix, elevation_poly_y, h_bot_pix, h_pix))
    elevation_data = PolyFillData(x=elevation_poly_x.tolist(), y=elevation_poly_y.tolist())

    stats = TextData(x=0.5 * w_pix, y=0.5 * (h_bot_pix+h_pix),
                     s="", fontsize=drawing_size_params.stats_fontsize,
                     fontproperties=drawing_style_params.pretty_font, ha="center")

    return scatter_data, elevation_data, stats


def rescale_elevation_to_dpi(elevation_map: np.ndarray, paper: PaperSize, target_dpi: float) -> np.ndarray:
    """Rescale the elevation map to a target DPI."""
    current_dpi = elevation_map.shape[0]/mm_to_inch(paper.h_mm)
    return rescale_elevation(elevation_map,  target_dpi/current_dpi)
