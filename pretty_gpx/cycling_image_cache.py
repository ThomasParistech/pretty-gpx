#!/usr/bin/python3
"""aaaaaaaa."""
from dataclasses import dataclass
from typing import BinaryIO
from typing import TextIO

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pretty_gpx.drawing.drawing_data import PlotData
from pretty_gpx.drawing.drawing_data import PolyFillData
from pretty_gpx.drawing.drawing_data import ScatterData
from pretty_gpx.drawing.drawing_data import TextData
from pretty_gpx.drawing.drawing_figure import DrawingFigure
from pretty_gpx.drawing.drawing_params import DrawingParams
from pretty_gpx.drawing.text_allocation import allocate_text
from pretty_gpx.drawing.theme_colors import hex_to_rgb
from pretty_gpx.drawing.theme_colors import ThemeColors
from pretty_gpx.gpx.augmented_gpx_data import AugmentedGpxData
from pretty_gpx.gpx.augmented_gpx_data import MountainPass
from pretty_gpx.gpx.elevation_map import download_elevation_map
from pretty_gpx.gpx.elevation_map import rescale_elevation
from pretty_gpx.hillshading import CachedHillShading
from pretty_gpx.layout.paper_size import PAPER_SIZES
from pretty_gpx.layout.vertical_layout import get_bounds
from pretty_gpx.layout.vertical_layout import VerticalLayout

W_DISPLAY_PIX = 800


def mountain_pass_to_str(mountain_pass: MountainPass) -> str:
    """aaaaaaaa"""
    return f" {mountain_pass.name} \n({int(mountain_pass.ele)} m)"


def get_elevation_drawings(layout: VerticalLayout,
                           h_pix: int, w_pix: int,
                           list_ele: list[float],
                           passes_ids: list[int],
                           draw_start: bool,
                           draw_end: bool,
                           drawing_params: DrawingParams) -> tuple[ScatterData, ScatterData, PolyFillData, TextData]:
    """aaaaaaaaaa"""
    h_up_pix = h_pix * (layout.title_relative_h + layout.map_relative_h)
    h_bot_pix = h_pix * (layout.title_relative_h + layout.map_relative_h + layout.elevation_relative_h)

    hmin, hmax = np.min(list_ele), np.max(list_ele)
    elevation_poly_x = np.linspace(0., w_pix, num=len(list_ele))
    elevation_poly_y = h_bot_pix + (np.array(list_ele) -
                                    hmin) * (h_up_pix-h_bot_pix) / (hmax-hmin)

    start_peaks_x, start_peaks_y = [], []
    if draw_start:
        start_peaks_x.append(elevation_poly_x[0])
        start_peaks_y.append(elevation_poly_y[0])
    if draw_end:
        start_peaks_x.append(elevation_poly_x[-1])
        start_peaks_y.append(elevation_poly_y[-1])
    start_end_track_data = ScatterData(x=start_peaks_x, y=start_peaks_y,
                                       marker="o", markersize=drawing_params.peak_markersize)

    elevation_peaks_x = [elevation_poly_x[closest_idx] for closest_idx in passes_ids]
    elevation_peaks_y = [elevation_poly_y[closest_idx] for closest_idx in passes_ids]

    elevation_poly_x = np.hstack((0, 0, elevation_poly_x, w_pix, w_pix)).tolist()
    elevation_poly_y = np.hstack((h_pix, h_bot_pix, elevation_poly_y, h_bot_pix, h_pix)).tolist()

    track_data = ScatterData(x=elevation_peaks_x, y=elevation_peaks_y,
                             marker="^", markersize=drawing_params.peak_markersize)

    peak_data = PolyFillData(x=elevation_poly_x, y=elevation_poly_y)

    stats = TextData(x=0.5 * w_pix, y=0.5 * (h_bot_pix+h_pix),
                     s="", fontsize=drawing_params.stats_fontsize,
                     fontproperties=drawing_params.pretty_font, ha="center")

    return track_data, start_end_track_data, peak_data, stats


@dataclass
class CyclingImageCache:

    elevation_map: np.ndarray
    elevation_shading: CachedHillShading

    stats_dist_km: float
    stats_uphill_m: float

    plotter: DrawingFigure

    @staticmethod
    def from_gpx(gpx_path: str | BinaryIO | TextIO | bytes,
                 dpi: int = 400) -> 'CyclingImageCache':
        """aaaaaaaa"""
        gpx_data = AugmentedGpxData.from_path(gpx_path)

        layout = VerticalLayout()
        paper = PAPER_SIZES["A4"]
        drawing_params = DrawingParams()

        bounds, latlon_aspect_ratio = get_bounds(gpx_data.track, layout, paper)
        elevation = download_elevation_map(bounds, cache_folder="data/dem_cache")

        current_dpi = elevation.shape[0]/(paper.h_mm / 25.4)
        elevation = rescale_elevation(elevation, dpi/current_dpi)

        h, w = elevation.shape[:2]
        x_pix, y_pix = gpx_data.track.project_on_image(elevation, bounds)

        list_x: list[float] = []
        list_y: list[float] = []
        list_text: list[str] = []

        for idx, mountain_pass in zip(gpx_data.passes_ids, gpx_data.mountain_passes):
            list_x.append(x_pix[idx])
            list_y.append(y_pix[idx])
            list_text.append(mountain_pass_to_str(mountain_pass))

        if gpx_data.start_name is not None:
            list_x.append(x_pix[0])
            list_y.append(y_pix[0])
            list_text.append(f" {gpx_data.start_name} ")

        if gpx_data.end_name is not None:
            list_x.append(x_pix[-1])
            list_y.append(y_pix[-1])
            list_text.append(f" {gpx_data.end_name} ")

        plots_x_to_avoid, plots_y_to_avoid = [x_pix], [y_pix]
        for y in np.concatenate((np.linspace(0., h * layout.title_relative_h, num=10),
                                 np.linspace(h * (layout.title_relative_h + layout.map_relative_h), h, num=10))):
            plots_x_to_avoid.append([0., w])
            plots_y_to_avoid.append([y, y])

        texts, lines = allocate_text(fig=plt.gcf(),
                                     ax=plt.gca(),
                                     imshow_img=np.full((h, w), fill_value=np.nan),
                                     w_mm=paper.w_mm,
                                     latlon_aspect_ratio=latlon_aspect_ratio,
                                     x=list_x,
                                     y=list_y,
                                     s=list_text,
                                     plots_x_to_avoid=plots_x_to_avoid,
                                     plots_y_to_avoid=plots_y_to_avoid,
                                     output_linewidth=drawing_params.text_arrow_linewidth,
                                     fontsize=drawing_params.text_fontsize,
                                     fontproperties=drawing_params.classic_font)

        draw_start = gpx_data.start_name is not None
        draw_end = draw_start if gpx_data.is_closed else gpx_data.end_name is not None
        ele_scatter, start_end_scatter, ele_fill_poly, stats = get_elevation_drawings(layout=layout,
                                                                                      h_pix=h, w_pix=w,
                                                                                      list_ele=gpx_data.track.list_ele,
                                                                                      passes_ids=gpx_data.passes_ids,
                                                                                      draw_start=draw_start,
                                                                                      draw_end=draw_end,
                                                                                      drawing_params=drawing_params)

        track_data = [PlotData(x=x_pix, y=y_pix, linewidth=drawing_params.track_linewidth),
                      ele_fill_poly]
        peak_data = [ele_scatter,
                     start_end_scatter,
                     ScatterData(x=list_x[:len(gpx_data.mountain_passes)], y=list_y[:len(gpx_data.mountain_passes)],
                                 marker="^", markersize=drawing_params.peak_markersize)]
        peak_data += texts[:len(gpx_data.mountain_passes)]
        peak_data += lines[:len(gpx_data.mountain_passes)]

        if gpx_data.start_name is not None:
            peak_data += [texts[len(gpx_data.mountain_passes)],
                          lines[len(gpx_data.mountain_passes)],
                          ScatterData(x=[list_x[len(gpx_data.mountain_passes)]],
                                      y=[list_y[len(gpx_data.mountain_passes)]],
                                      marker="o", markersize=drawing_params.peak_markersize)]

        if gpx_data.end_name is not None:
            peak_data += [texts[-1],
                          lines[-1],
                          ScatterData(x=[list_x[-1]],
                                      y=[list_y[-1]],
                                      marker="o", markersize=drawing_params.peak_markersize)]

        title = TextData(x=0.5 * w, y=0.8 * h * layout.title_relative_h,
                         s="", fontsize=drawing_params.title_fontsize,
                           fontproperties=drawing_params.pretty_font, ha="center")

        plotter = DrawingFigure(ref_img_shape=(h, w),
                                w_mm=paper.w_mm,
                                w_display_pix=W_DISPLAY_PIX,
                                latlon_aspect_ratio=latlon_aspect_ratio,
                                track_data=track_data,
                                peak_data=peak_data,
                                title=title,
                                stats=stats)

        print("Done")
        return CyclingImageCache(elevation_map=elevation,
                                 elevation_shading=CachedHillShading(elevation),
                                 stats_dist_km=gpx_data.dist_km,
                                 stats_uphill_m=gpx_data.uphill_m,
                                 plotter=plotter)

    def rescale(self, scale: float) -> 'CyclingImageCache':
        """pass"""
        new_elevation_map = rescale_elevation(self.elevation_map, scale)

        return CyclingImageCache(elevation_map=new_elevation_map,
                                 elevation_shading=CachedHillShading(new_elevation_map),
                                 stats_dist_km=self.stats_dist_km,
                                 stats_uphill_m=self.stats_uphill_m,
                                 plotter=self.plotter)

    def draw(self,
             fig: Figure,
             ax: Axes,
             azimuth: int,
             theme_colors: ThemeColors,
             title_txt: str,
             uphill_m: str,
             dist_km: str):
        """aa"""
        grey_hillshade = self.elevation_shading.render_grey(azimuth)[..., None]
        background_color_rgb = hex_to_rgb(theme_colors.background_color)
        color_0 = (0, 0, 0) if theme_colors.dark_mode else background_color_rgb
        color_1 = background_color_rgb if theme_colors.dark_mode else (255, 255, 255)
        colored_hillshade = grey_hillshade * (np.array(color_1) - np.array(color_0)) + np.array(color_0)

        img = colored_hillshade.astype(np.uint8)

        dist_km_int = int(dist_km if dist_km != '' else self.stats_dist_km)
        uphill_m_int = int(uphill_m if uphill_m != '' else self.stats_uphill_m)
        stats_text = f"{dist_km_int} km - {uphill_m_int} m D+"

        self.plotter.draw(fig, ax, img, theme_colors, title_txt, stats_text)
