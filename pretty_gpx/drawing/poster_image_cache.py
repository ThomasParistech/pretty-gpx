#!/usr/bin/python3
"""Poster Image Cache."""
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.drawing.drawing_data import PlotData
from pretty_gpx.drawing.drawing_data import PolyFillData
from pretty_gpx.drawing.drawing_data import ScatterData
from pretty_gpx.drawing.drawing_data import TextData
from pretty_gpx.drawing.drawing_figure import DrawingFigure
from pretty_gpx.drawing.drawing_params import DrawingSizeParams
from pretty_gpx.drawing.drawing_params import DrawingStyleParams
from pretty_gpx.drawing.hillshading import CachedHillShading
from pretty_gpx.drawing.text_allocation import allocate_text
from pretty_gpx.drawing.theme_colors import hex_to_rgb
from pretty_gpx.drawing.theme_colors import ThemeColors
from pretty_gpx.gpx.augmented_gpx_data import AugmentedGpxData
from pretty_gpx.gpx.elevation_map import download_elevation_map
from pretty_gpx.gpx.elevation_map import rescale_elevation
from pretty_gpx.layout.paper_size import PaperSize
from pretty_gpx.layout.vertical_layout import get_bounds
from pretty_gpx.layout.vertical_layout import VerticalLayout
from pretty_gpx.utils.utils import mm_to_inch
from pretty_gpx.utils.utils import safe

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
        return PosterImageCaches.from_gpx_data(gpx_data, paper_size)

    @staticmethod
    def from_gpx_data(gpx_data: AugmentedGpxData,
                      paper_size: PaperSize) -> 'PosterImageCaches':
        """Create a PosterImageCaches from a GPX file."""
        high_res = PosterImageCache.from_gpx_data(gpx_data, dpi=HIGH_RES_DPI, paper=paper_size)
        low_res = high_res.change_dpi(WORKING_DPI)
        return PosterImageCaches(low_res=low_res, high_res=high_res, gpx_data=gpx_data)

    @staticmethod
    def update_duration_str(gpx_data: AugmentedGpxData,
                            paper_size: PaperSize,
                            override_duration_str:str) -> 'PosterImageCaches':
        """Create a PosterImageCaches from a GPX file."""
        high_res = PosterImageCache.from_gpx_data(gpx_data,
                                                  dpi=HIGH_RES_DPI,
                                                  paper=paper_size,
                                                  override_duration=override_duration_str)
        low_res = high_res.change_dpi(WORKING_DPI)
        return PosterImageCaches(low_res=low_res, high_res=high_res, gpx_data=gpx_data)


@dataclass
class PosterDrawingData:
    """Drawing data for the poster."""
    img: np.ndarray
    theme_colors: ThemeColors
    title_txt: str
    stats_text: str
    duration_txt: str


@dataclass
class PosterImageCache:
    """Class leveraging cache to avoid reprocessing GPX when chaning color them, title, sun azimuth..."""

    elevation_map: np.ndarray
    elevation_shading: CachedHillShading

    stats_dist_km: float
    stats_uphill_m: float
    stat_duration_str: str

    plotter: DrawingFigure

    dpi: float

    @staticmethod
    def from_gpx_data(gpx_data: AugmentedGpxData,
                      paper: PaperSize,
                      layout: VerticalLayout = VerticalLayout(),
                      dpi: float = HIGH_RES_DPI,
                      override_duration: str=None) -> 'PosterImageCache':
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

        # Allocate non-overlapping text annotations on the map
        list_x: list[float] = []
        list_y: list[float] = []
        list_text: list[str] = []

        passes_begin = len(list_x)
        for idx, mountain_pass in zip(gpx_data.passes_ids, gpx_data.mountain_passes):
            list_x.append(x_pix[idx])
            list_y.append(y_pix[idx])
            list_text.append(f" {mountain_pass.name} \n({int(mountain_pass.ele)} m)")
        passes_end = len(list_x)

        huts_begin = len(list_x)
        for idx, mountain_hut in zip(gpx_data.hut_ids, gpx_data.huts):
            if mountain_hut.name is not None:
                list_x.append(x_pix[idx])
                list_y.append(y_pix[idx])
                list_text.append(f" {mountain_hut.name} ")
        huts_end = len(list_x)

        start_idx = None
        if gpx_data.start_name is not None:
            start_idx = len(list_x)
            list_x.append(x_pix[0])
            list_y.append(y_pix[0])
            list_text.append(f" {gpx_data.start_name} ")

        end_idx = None
        if gpx_data.end_name is not None:
            end_idx = len(list_x)
            list_x.append(x_pix[-1])
            list_y.append(y_pix[-1])
            list_text.append(f" {gpx_data.end_name} ")

        plots_x_to_avoid, plots_y_to_avoid = [x_pix], [y_pix]
        for y in np.concatenate((np.linspace(0., h * layout.title_relative_h, num=10),
                                 np.linspace(h * (layout.title_relative_h + layout.map_relative_h), h, num=10))):
            plots_x_to_avoid.append([0., w])
            plots_y_to_avoid.append([y, y])

        scatter_passes_x = [x_pix[idx] for idx in gpx_data.passes_ids]
        scatter_passes_y = [y_pix[idx] for idx in gpx_data.passes_ids]
        scatter_huts_x = [x_pix[idx] for idx in gpx_data.hut_ids]
        scatter_huts_y = [y_pix[idx] for idx in gpx_data.hut_ids]

        texts, lines = allocate_text(fig=plt.gcf(),
                                     ax=plt.gca(),
                                     imshow_img=np.full((h, w), fill_value=np.nan),
                                     paper_size=paper,
                                     latlon_aspect_ratio=latlon_aspect_ratio,
                                     x=list_x,
                                     y=list_y,
                                     s=list_text,
                                     plots_x_to_avoid=plots_x_to_avoid,
                                     plots_y_to_avoid=plots_y_to_avoid,
                                     scatter_x_to_avoid=scatter_passes_x+scatter_huts_x,
                                     scatter_y_to_avoid=scatter_passes_y+scatter_huts_y,
                                     scatter_sizes=([drawing_size_params.peak_markersize]*len(scatter_passes_x)
                                                    + [drawing_size_params.hut_markersize]*len(scatter_huts_x)),
                                     output_linewidth=drawing_size_params.text_arrow_linewidth,
                                     fontsize=drawing_size_params.text_fontsize,
                                     fontproperties=drawing_style_params.classic_font)

        # Draw the elevation profile
        if override_duration is not None and override_duration != "":
            duration_to_draw = override_duration
        else:
            duration_to_draw = gpx_data.total_duration
        
        if duration_to_draw is not None and duration_to_draw != "":
            draw_duration = True
        else:
            draw_duration = False
        draw_start = gpx_data.start_name is not None
        draw_end = draw_start if gpx_data.is_closed else gpx_data.end_name is not None
        ele_scatter, ele_fill_poly, stats, duration_stat = get_elevation_drawings(layout=layout,
                                                                             h_pix=h, w_pix=w,
                                                                             list_ele=gpx_data.track.list_ele,
                                                                             list_cum_d=gpx_data.track.list_cumul_d,
                                                                             passes_ids=gpx_data.passes_ids,
                                                                             huts_ids=gpx_data.hut_ids,
                                                                             draw_start=draw_start,
                                                                             draw_end=draw_end,
                                                                             draw_duration=draw_duration,
                                                                             drawing_style_params=drawing_style_params,
                                                                             drawing_size_params=drawing_size_params)

        # Prepare the plot data
        augmented_hut_ids = [0] + gpx_data.hut_ids + [None]
        track_data = []
        for k in range(len(augmented_hut_ids)-1):
            begin_i = augmented_hut_ids[k]
            end_i = augmented_hut_ids[k+1]
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

        peak_data = ele_scatter + [ScatterData(x=scatter_passes_x,
                                               y=scatter_passes_y,
                                               marker=drawing_style_params.peak_marker,
                                               markersize=drawing_size_params.peak_markersize),
                                   ScatterData(x=scatter_huts_x,
                                               y=scatter_huts_y,
                                               marker=drawing_style_params.hut_marker,
                                               markersize=drawing_size_params.hut_markersize)]
        peak_data += texts[passes_begin:passes_end]
        peak_data += lines[passes_begin:passes_end]
        peak_data += texts[huts_begin:huts_end]
        peak_data += lines[huts_begin:huts_end]

        if gpx_data.start_name is not None:
            i = safe(start_idx)
            peak_data += [texts[i],
                          lines[i],
                          ScatterData(x=[list_x[i]], y=[list_y[i]],
                                      marker=drawing_style_params.start_marker,
                                      markersize=drawing_size_params.start_markersize)]

        if gpx_data.end_name is not None:
            i = safe(end_idx)
            peak_data += [texts[i],
                          lines[i],
                          ScatterData(x=[list_x[i]],
                                      y=[list_y[i]],
                                      marker=drawing_style_params.end_marker,
                                      markersize=drawing_size_params.end_markersize)]

        title = TextData(x=0.5 * w, y=0.8 * h * layout.title_relative_h,
                         s="", fontsize=drawing_size_params.title_fontsize,
                           fontproperties=drawing_style_params.pretty_font, ha="center")

        plotter = DrawingFigure(ref_img_shape=(h, w),
                                paper_size=paper,
                                w_display_pix=W_DISPLAY_PIX,
                                latlon_aspect_ratio=latlon_aspect_ratio,
                                track_data=track_data,
                                peak_data=peak_data,
                                title=title,
                                stats=stats,
                                duration=duration_stat)

        print("Successful GPX Processing")
        return PosterImageCache(elevation_map=elevation,
                                elevation_shading=CachedHillShading(elevation),
                                stats_dist_km=gpx_data.dist_km,
                                stats_uphill_m=gpx_data.uphill_m,
                                stat_duration_str=duration_to_draw,
                                plotter=plotter,
                                dpi=dpi)

    def change_dpi(self, dpi: float) -> 'PosterImageCache':
        """Scale the elevation map to a new DPI."""
        new_elevation_map = rescale_elevation_to_dpi(self.elevation_map, self.plotter.paper_size, dpi)
        return PosterImageCache(elevation_map=new_elevation_map,
                                elevation_shading=CachedHillShading(new_elevation_map),
                                stats_dist_km=self.stats_dist_km,
                                stats_uphill_m=self.stats_uphill_m,
                                stat_duration_str=self.stat_duration_str,
                                plotter=self.plotter,
                                dpi=dpi)

    def update_drawing_data(self,
                            azimuth: int,
                            theme_colors: ThemeColors,
                            title_txt: str,
                            uphill_m: str,
                            dist_km: str,
                            duration: str) -> PosterDrawingData:
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

        return PosterDrawingData(img, theme_colors, title_txt=title_txt, stats_text=stats_text, duration_txt=duration)

    def draw(self, fig: Figure, ax: Axes, poster_drawing_data: PosterDrawingData) -> None:
        """Draw the updated drawing data (Must run in the main thread because of matplotlib backend)."""
        self.plotter.draw(fig, ax,
                          poster_drawing_data.img,
                          poster_drawing_data.theme_colors,
                          poster_drawing_data.title_txt,
                          poster_drawing_data.stats_text,
                          poster_drawing_data.duration_txt)
        print(f"Drawing updated (Elevation Map {poster_drawing_data.img.shape[1]}x{poster_drawing_data.img.shape[0]})")


def get_elevation_drawings(layout: VerticalLayout,
                           h_pix: int, w_pix: int,
                           list_ele: list[float],
                           list_cum_d: list[float],
                           passes_ids: list[int],
                           huts_ids: list[int],
                           draw_start: bool,
                           draw_end: bool,
                           draw_duration: bool,
                           drawing_style_params: DrawingStyleParams,
                           drawing_size_params: DrawingSizeParams) -> tuple[list[ScatterData], PolyFillData, TextData]:
    """Create the plot elements for the elevation profile."""
    # Elevation Profile
    h_up_pix = h_pix * (layout.title_relative_h + layout.map_relative_h)
    h_bot_pix = h_pix * (layout.title_relative_h + layout.map_relative_h + layout.elevation_relative_h)
    h_stat_text = h_pix *(layout.title_relative_h + layout.map_relative_h + layout.elevation_relative_h + 1.0)/2.0
    h_duration_text = h_pix * 0.99

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
    elevation_poly_x = np.hstack((0, 0, elevation_poly_x, w_pix, w_pix)).tolist()
    elevation_poly_y = np.hstack((h_pix, h_bot_pix, elevation_poly_y, h_bot_pix, h_pix)).tolist()
    elevation_data = PolyFillData(x=elevation_poly_x, y=elevation_poly_y)

    if draw_duration:
        duration = TextData(x=0.01 * w_pix, y=h_duration_text,
                         s="", fontsize=drawing_size_params.stats_fontsize*0.5,
                         fontproperties=drawing_style_params.pretty_font, ha="left")
        stats = TextData(x=0.5 * w_pix, y=h_stat_text,
                         s="", fontsize=drawing_size_params.stats_fontsize*0.8,
                         fontproperties=drawing_style_params.pretty_font, ha="center")
    else:
        duration = None
        stats = TextData(x=0.5 * w_pix, y=h_stat_text,
                         s="", fontsize=drawing_size_params.stats_fontsize*0.8,
                         fontproperties=drawing_style_params.pretty_font, ha="center")

    return scatter_data, elevation_data, stats, duration


def rescale_elevation_to_dpi(elevation_map: np.ndarray, paper: PaperSize, target_dpi: float) -> np.ndarray:
    """Rescale the elevation map to a target DPI."""
    current_dpi = elevation_map.shape[0]/mm_to_inch(paper.h_mm)
    return rescale_elevation(elevation_map,  target_dpi/current_dpi)
