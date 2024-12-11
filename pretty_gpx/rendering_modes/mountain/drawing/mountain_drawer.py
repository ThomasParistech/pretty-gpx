#!/usr/bin/python3
"""Mountain Drawer."""
from dataclasses import dataclass
from typing import Final

import numpy as np

from pretty_gpx.common.drawing.base_drawing_figure import BaseDrawingFigure
from pretty_gpx.common.drawing.color_theme import hex_to_rgb
from pretty_gpx.common.drawing.drawing_data import BaseDrawingData
from pretty_gpx.common.drawing.drawing_data import PlotData
from pretty_gpx.common.drawing.drawing_data import PolyFillData
from pretty_gpx.common.drawing.drawing_data import ScatterData
from pretty_gpx.common.drawing.drawing_data import TextData
from pretty_gpx.common.drawing.elevation_stats_section import ElevationStatsSection
from pretty_gpx.common.drawing.fonts import FontEnum
from pretty_gpx.common.drawing.text_allocation import allocate_text
from pretty_gpx.common.drawing.text_allocation import AnnotatedScatterDataCollection
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.structure import Drawer
from pretty_gpx.common.structure import DrawingInputs
from pretty_gpx.common.utils.asserts import assert_lt
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.utils import mm_to_inch
from pretty_gpx.rendering_modes.mountain.data.elevation_map import rescale_elevation
from pretty_gpx.rendering_modes.mountain.data.mountain_augmented_gpx_data import MountainAugmentedGpxData
from pretty_gpx.rendering_modes.mountain.drawing.hillshading import CachedHillShading
from pretty_gpx.rendering_modes.mountain.drawing.mountain_colors import MountainColors
from pretty_gpx.rendering_modes.mountain.drawing.mountain_download_data import MountainDownloadData
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawing_config import MountainDrawingSizeConfig
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawing_config import MountainDrawingStyleConfig
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawing_figure import MountainDrawingFigure
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawing_figure import MountainDrawingParams
from pretty_gpx.rendering_modes.mountain.mountain_vertical_layout import MountainVerticalLayout
from pretty_gpx.ui.pages.template.ui_plot import HIGH_RES_DPI

MOUNTAIN_LOW_RES_DPI: Final[int] = 50


@dataclass(frozen=True)
class MountainDrawingInputs(DrawingInputs):
    """Input Data to be transformed into MountainDrawingParams."""
    high_res: bool

    azimuth: int
    colors: MountainColors
    title_txt: str | None
    uphill_m: int | None
    dist_km: float | None


@dataclass
class MountainDrawer(Drawer[MountainAugmentedGpxData,
                            MountainDownloadData,
                            MountainDrawingInputs,
                            MountainDrawingParams]):
    """Class leveraging cache to avoid reprocessing GPX when changing color theme, title, sun azimuth..."""
    low_res_elevation: CachedHillShading
    high_res_elevation: CachedHillShading

    stats_dist_km: float
    stats_uphill_m: float

    @staticmethod
    def get_gpx_data_cls() -> type[MountainAugmentedGpxData]:
        """Return the template AugmentedGpxData class (Because Python doesn't allow to use T as a type)."""
        return MountainAugmentedGpxData

    @staticmethod
    def get_download_data_cls() -> type[MountainDownloadData]:
        """Return the template MountainDownloadData class (Because Python doesn't allow to use U as a type)."""
        return MountainDownloadData

    @profile
    @staticmethod
    def from_gpx_and_download_data(gpx_data: MountainAugmentedGpxData,
                                   download_data: MountainDownloadData) -> 'MountainDrawer':
        """Create a MountainDrawer from a GPX file."""
        # Rescale the elevation map to the target DPI
        assert_lt(MOUNTAIN_LOW_RES_DPI, HIGH_RES_DPI)
        low_res_elevation = rescale_elevation_to_dpi(download_data.elevation, download_data.img_bounds,
                                                     download_data.paper_fig, MOUNTAIN_LOW_RES_DPI)
        high_res_elevation = rescale_elevation_to_dpi(download_data.elevation, download_data.img_bounds,
                                                      download_data.paper_fig, HIGH_RES_DPI)

        # Use default drawing params
        drawing_size_config = MountainDrawingSizeConfig.default(download_data.paper_fig.paper_size)
        drawing_style_config = MountainDrawingStyleConfig()

        plotter = init_and_populate_drawing_figure(gpx_data,
                                                   download_data.paper_fig,
                                                   download_data.img_bounds,
                                                   download_data.layout,
                                                   drawing_size_config,
                                                   drawing_style_config)

        logger.info("Successful GPX Processing")
        return MountainDrawer(high_res_elevation=CachedHillShading(high_res_elevation),
                              low_res_elevation=CachedHillShading(low_res_elevation),
                              stats_dist_km=gpx_data.dist_km,
                              stats_uphill_m=gpx_data.uphill_m,
                              plotter=plotter,
                              gpx_data=gpx_data)

    @profile
    def get_params(self, inputs: MountainDrawingInputs) -> MountainDrawingParams:
        """Convert DrawingInputs to DrawingParams."""
        if inputs.high_res:
            elevation_shading = self.high_res_elevation
        else:
            elevation_shading = self.low_res_elevation
        grey_hillshade = elevation_shading.render_grey(inputs.azimuth)[..., None]

        background_color_rgb = hex_to_rgb(inputs.colors.background_color)
        color_0 = (0, 0, 0) if inputs.colors.dark_mode else background_color_rgb
        color_1 = background_color_rgb if inputs.colors.dark_mode else (255, 255, 255)
        colored_hillshade = grey_hillshade * (np.array(color_1) - np.array(color_0)) + np.array(color_0)

        img = colored_hillshade.astype(np.uint8)

        dist_km_float = inputs.dist_km if inputs.dist_km is not None else self.stats_dist_km
        uphill_m_float = inputs.uphill_m if inputs.uphill_m is not None else self.stats_uphill_m
        stats_text = f"{dist_km_float:.2f} km - {int(uphill_m_float)} m D+"
        title_txt = inputs.title_txt if inputs.title_txt is not None else ""

        return MountainDrawingParams(img, inputs.colors, title_txt=title_txt, stats_txt=stats_text)


def init_and_populate_drawing_figure(gpx_data: MountainAugmentedGpxData,
                                     paper_fig: BaseDrawingFigure,
                                     img_gpx_bounds: GpxBounds,
                                     layout: MountainVerticalLayout,
                                     drawing_size_config: MountainDrawingSizeConfig,
                                     drawing_style_config: MountainDrawingStyleConfig
                                     ) -> MountainDrawingFigure:
    """Set up and populate the DrawingFigure for the poster."""
    list_x = gpx_data.track.list_lon
    list_y = gpx_data.track.list_lat

    b = paper_fig.gpx_bounds

    scatters = init_annotated_scatter_collection(gpx_data, list_x, list_y, drawing_style_config, drawing_size_config)

    plots_x_to_avoid, plots_y_to_avoid = [list_x], [list_y]

    for y in b.lat_min+b.dlat*np.concatenate((np.linspace(0., layout.stats_relative_h + layout.elevation_relative_h,
                                                          num=10, endpoint=True),  # Stats+Elevation area
                                              np.linspace(1.0-layout.title_relative_h, 1.0,
                                                          num=10, endpoint=True))):  # Title area
        plots_x_to_avoid.append([b.lon_min, b.lon_max])
        plots_y_to_avoid.append([y, y])

    texts, arrows = allocate_text(base_fig=paper_fig,
                                  scatters=scatters,
                                  plots_x_to_avoid=plots_x_to_avoid,
                                  plots_y_to_avoid=plots_y_to_avoid,
                                  output_linewidth=drawing_size_config.text_arrow_linewidth,
                                  fontsize=drawing_size_config.text_fontsize,
                                  fontproperties=FontEnum.ANNOTATION.value)

    # Draw the elevation profile
    draw_start = gpx_data.start_name is not None
    draw_end = draw_start if gpx_data.is_closed else gpx_data.end_name is not None
    ele_scatter, ele_fill_poly, stats = get_elevation_drawings(layout=layout,
                                                               paper_fig=paper_fig,
                                                               track=gpx_data.track,
                                                               passes_ids=gpx_data.passes_ids,
                                                               huts_ids=gpx_data.hut_ids,
                                                               draw_start=draw_start,
                                                               draw_end=draw_end,
                                                               drawing_style_config=drawing_style_config,
                                                               drawing_size_config=drawing_size_config)

    # Prepare the plot data
    augmented_hut_ids = [0] + gpx_data.hut_ids
    track_data: list[BaseDrawingData] = []
    for k in range(len(augmented_hut_ids)):
        begin_i = augmented_hut_ids[k]
        end_i = augmented_hut_ids[k+1] if k+1 < len(augmented_hut_ids) else None

        track_data.append(PlotData(x=list_x[begin_i:end_i],
                                   y=list_y[begin_i:end_i],
                                   linewidth=drawing_size_config.track_linewidth))
        if k != 0:
            # Draw dotted line between huts, in case there's a visible gap
            track_data.append(PlotData(x=[list_x[begin_i-1], list_x[begin_i]],
                                       y=[list_y[begin_i-1], list_y[begin_i]],
                                       linewidth=0.5*drawing_size_config.track_linewidth,
                                       linestyle="dotted"))

    track_data.append(ele_fill_poly)

    peak_data: list[BaseDrawingData] = ele_scatter + scatters.list_scatter_data + texts + arrows  # type:ignore

    title = TextData(x=b.lon_center, y=b.lat_max - 0.8 * b.dlat * layout.title_relative_h,
                     s="", fontsize=drawing_size_config.title_fontsize,
                     fontproperties=FontEnum.TITLE.value, ha="center", va="center")

    return MountainDrawingFigure(paper_size=paper_fig.paper_size,
                                 latlon_aspect_ratio=paper_fig.latlon_aspect_ratio,
                                 gpx_bounds=paper_fig.gpx_bounds,
                                 track_data=track_data,
                                 peak_data=peak_data,
                                 title=title,
                                 stats=stats,
                                 img_gpx_bounds=img_gpx_bounds)


def init_annotated_scatter_collection(gpx_data: MountainAugmentedGpxData,
                                      global_list_x: list[float],
                                      global_list_y: list[float],
                                      drawing_style_config: MountainDrawingStyleConfig,
                                      drawing_size_config: MountainDrawingSizeConfig) -> AnnotatedScatterDataCollection:
    """Initialize the AnnotatedScatterDataCollection with the mountain passes, huts, start and end markers."""
    scatter_collection = AnnotatedScatterDataCollection()

    scatter_collection.add_scatter_data_on_track(global_x=global_list_x, global_y=global_list_y,
                                                 scatter_ids=gpx_data.passes_ids,
                                                 scatter_texts=[f" {mountain_pass.name} \n({int(mountain_pass.ele)} m)"
                                                                for mountain_pass in gpx_data.mountain_passes],
                                                 marker=drawing_style_config.peak_marker,
                                                 markersize=drawing_size_config.peak_markersize)
    scatter_collection.add_scatter_data_on_track(global_x=global_list_x, global_y=global_list_y,
                                                 scatter_ids=gpx_data.hut_ids,
                                                 scatter_texts=[f" {mountain_hut.name} "
                                                                if mountain_hut.name is not None else None
                                                                for mountain_hut in gpx_data.huts],
                                                 marker=drawing_style_config.hut_marker,
                                                 markersize=drawing_size_config.hut_markersize)

    if gpx_data.start_name is not None:
        scatter_collection.add_scatter_data_on_track(global_x=global_list_x, global_y=global_list_y,
                                                     scatter_ids=[0],
                                                     scatter_texts=[f" {gpx_data.start_name} "],
                                                     marker=drawing_style_config.start_marker,
                                                     markersize=drawing_size_config.start_markersize)

    if gpx_data.end_name is not None:
        scatter_collection.add_scatter_data_on_track(global_x=global_list_x, global_y=global_list_y,
                                                     scatter_ids=[len(global_list_x)-1],
                                                     scatter_texts=[f" {gpx_data.end_name} "],
                                                     marker=drawing_style_config.end_marker,
                                                     markersize=drawing_size_config.end_markersize)
    return scatter_collection


def get_elevation_drawings(layout: MountainVerticalLayout,
                           paper_fig: BaseDrawingFigure,
                           track: GpxTrack,
                           passes_ids: list[int],
                           huts_ids: list[int],
                           draw_start: bool,
                           draw_end: bool,
                           drawing_style_config: MountainDrawingStyleConfig,
                           drawing_size_config: MountainDrawingSizeConfig) -> tuple[list[ScatterData],
                                                                                    PolyFillData,
                                                                                    TextData]:
    """Create the plot elements for the elevation profile."""
    # Elevation Profile
    ele = ElevationStatsSection(layout, paper_fig, track)

    # Mountain Passes and Huts
    scatter_data = [
        ScatterData(x=[ele.get_profile_lon_x(closest_idx) for closest_idx in ids],
                    y=[ele.get_profile_lat_y(closest_idx) for closest_idx in ids],
                    marker=marker, markersize=markersize)
        for ids, marker, markersize in [(passes_ids, drawing_style_config.peak_marker,
                                         drawing_size_config.peak_markersize),
                                        (huts_ids, drawing_style_config.hut_marker,
                                         drawing_size_config.hut_markersize)]
    ]

    # Start and End
    if draw_start:
        scatter_data.append(ScatterData(x=[ele.get_profile_lon_x(0)], y=[ele.get_profile_lat_y(0)],
                                        marker=drawing_style_config.start_marker,
                                        markersize=drawing_size_config.start_markersize))
    if draw_end:
        scatter_data.append(ScatterData(x=[ele.get_profile_lon_x(-1)], y=[ele.get_profile_lat_y(-1)],
                                        marker=drawing_style_config.end_marker,
                                        markersize=drawing_size_config.end_markersize))

    # Text
    stats = TextData(x=ele.section_center_lon_x, y=ele.section_center_lat_y,
                     s="", fontsize=drawing_size_config.stats_fontsize,
                     fontproperties=FontEnum.STATS.value, ha="center", va="center")

    return scatter_data, ele.fill_poly, stats


def rescale_elevation_to_dpi(elevation_map: np.ndarray,
                             img_bounds: GpxBounds,
                             paper_fig: BaseDrawingFigure,
                             target_dpi: float) -> np.ndarray:
    """Rescale the elevation map to a target DPI."""
    paper_h_inches = mm_to_inch(paper_fig.paper_size.h_mm)
    img_h_inches = paper_h_inches * img_bounds.dlat / paper_fig.gpx_bounds.dlat
    current_dpi = elevation_map.shape[0]/img_h_inches
    return rescale_elevation(elevation_map,  target_dpi/current_dpi)
