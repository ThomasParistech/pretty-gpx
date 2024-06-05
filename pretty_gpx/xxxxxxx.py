#!/usr/bin/python3
"""aaaaaaaa."""
import math
from dataclasses import dataclass
from typing import BinaryIO
from typing import List
from typing import Optional
from typing import TextIO
from typing import Union

import cv2
import matplotlib.pyplot as plt
import numpy as np
import textalloc as ta
from elevation_map import ElevationMap
from gpx_bounds import GpxBounds
from gpx_track import GpxTrack
from hillshading import AZIMUTHS
from hillshading import CachedHillShading
from map_data import get_close_mountain_passes
from map_data import get_place_name
from map_data import is_close_to_a_mountain_pass
from map_data import MountainPass
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from nicegui import events
from nicegui import ui
from theme_colors import COLOR_THEMES
from theme_colors import hex_to_rgb
from theme_colors import ThemeColors

TEXT_FONT_SIZE = 30
PEAK_MARKER_SIZE = 20
TRACK_LW = 7
TEXT_LW = 3


MY_FONT = FontProperties(fname="./Lobster 1.4.otf")


@dataclass
class VerticalLayoutSettings:
    """add drawing diagram explaining

    """
    w_mm: int = 210
    h_mm: int = 297

    margin_relative_w: float = 0.06
    margin_relative_h: float = 0.06

    title_relative_h: float = 0.18
    map_relative_h: float = 0.6
    elevation_relative_h: float = 0.1

    def __post_init__(self) -> None:
        assert self.title_relative_h + self.map_relative_h + self.elevation_relative_h <= 0.9


def get_bounds(gpx_track: GpxTrack, layout: VerticalLayoutSettings) -> GpxBounds:
    """aaaa"""
    bounds = GpxBounds.from_list(list_lon=gpx_track.list_lon,
                                 list_lat=gpx_track.list_lat)

    map_w_mm = layout.w_mm * (1. - 2.*layout.margin_relative_w)
    map_h_mm = layout.h_mm * (layout.map_relative_h - 2*layout.margin_relative_h)
    deg_per_mm = max((bounds.lon_max - bounds.lon_min)/map_w_mm,
                     (bounds.lat_max - bounds.lat_min)/map_h_mm)

    lon_center = 0.5*(bounds.lon_max + bounds.lon_min)
    lat_center = 0.5*(bounds.lat_max + bounds.lat_min)

    new_dlon = deg_per_mm * layout.w_mm
    new_dlat = deg_per_mm * layout.h_mm

    new_lon_min = lon_center - new_dlon * 0.5
    new_lat_min = lat_center - new_dlat * (1. - (layout.title_relative_h + 0.5*layout.map_relative_h))

    return GpxBounds(lon_min=new_lon_min,
                     lon_max=new_lon_min + new_dlon,
                     lat_min=new_lat_min,
                     lat_max=new_lat_min + new_dlat)


def rescale(l: List[float], scale: float) -> List[float]:
    return [p*scale for p in l]


@dataclass
class SymbolAnnotations:
    x: List[float]
    y: List[float]
    marker_size: float
    marker: str

    def rescale(self, scale: float) -> 'SymbolAnnotations':
        """pass"""
        return SymbolAnnotations(x=rescale(self.x, scale),
                                 y=rescale(self.y, scale),
                                 marker=self.marker,
                                 marker_size=self.marker_size*scale)

    def draw(self, ax: Axes, color: str) -> None:
        """aaaaa"""
        ax.plot(self.x, self.y, self.marker, c=color, markersize=math.ceil(self.marker_size))


@dataclass
class TextAnnotations:
    s: List[str]
    x: List[float]
    y: List[float]
    fontsize: float

    line_x: List[List[float]]
    line_y: List[List[float]]
    lw: float

    def rescale(self, scale: float) -> 'TextAnnotations':
        """pass"""
        return TextAnnotations(s=self.s,
                               x=rescale(self.x, scale),
                               y=rescale(self.y, scale),
                               fontsize=self.fontsize*scale,
                               line_x=[rescale(x, scale) for x in self.line_x],
                               line_y=[rescale(y, scale) for y in self.line_y],
                               lw=self.lw*scale)

    def draw(self, ax: Axes, color: str) -> None:
        """aaaaa"""
        for s, x, y, line_x, line_y in zip(self.s,
                                           self.x,
                                           self.y,
                                           self.line_x,
                                           self.line_y):
            ax.text(x, y, s, fontsize=math.ceil(self.fontsize), ha='center', c=color)
            ax.plot(line_x, line_y, lw=math.ceil(self.lw), c=color)


def mountain_pass_to_str(mountain_pass: MountainPass) -> str:
    """aaaaaaaa"""
    return f" {mountain_pass.name} \n({int(mountain_pass.ele)} m)"


@dataclass
class CyclingImageCache:
    peaks_texts: TextAnnotations
    peaks_symbols: SymbolAnnotations

    start_text: Optional[TextAnnotations]
    start_symbol: Optional[SymbolAnnotations]

    end_text: Optional[TextAnnotations]
    end_symbol: Optional[SymbolAnnotations]

    track_x: List[float]
    track_y: List[float]
    track_lw: float

    elevation_poly_x: List[float]
    elevation_poly_y: List[float]

    elevation_peaks_x: List[float]
    elevation_peaks_y: List[float]

    elevation_map: np.ndarray
    elevation_shading: CachedHillShading

    title_x: float
    title_y: float

    stats_x: float
    stats_y: float
    stats_dist_km: float
    stats_uphill_m: float

    @staticmethod
    def from_gpx(gpx_path: Union[str, BinaryIO, TextIO],
                 dpi: int = 400) -> 'CyclingImageCache':
        """aaaaaaaa"""
        gpx_track, dist_km, uphill_m = GpxTrack.load(gpx_path)
        end_idx = int(len(gpx_track.list_lon)*0.9)
        gpx_track = GpxTrack(list_lon=gpx_track.list_lon[:end_idx],
                             list_lat=gpx_track.list_lat[:end_idx],
                             list_ele=gpx_track.list_ele[:end_idx])

        layout = VerticalLayoutSettings()
        bounds = get_bounds(gpx_track, layout)
        elevation = ElevationMap.download(bounds, cache_folder="data/dem_cache")
        current_dpi = elevation.elevation.shape[0]/(layout.h_mm / 25.4)
        elevation = elevation.rescale(dpi/current_dpi)

        #######

        is_closed = gpx_track.is_closed(1000)
        passes_ids, mountain_passes = get_close_mountain_passes(gpx_track, 50)
        close_to_start = is_close_to_a_mountain_pass(lon=gpx_track.list_lon[0],
                                                     lat=gpx_track.list_lat[0],
                                                     mountain_passes=mountain_passes,
                                                     max_dist_m=1000)
        close_to_end = is_close_to_a_mountain_pass(lon=gpx_track.list_lon[-1],
                                                   lat=gpx_track.list_lat[-1],
                                                   mountain_passes=mountain_passes,
                                                   max_dist_m=1000)

        start_name = get_place_name(lon=gpx_track.list_lon[0], lat=gpx_track.list_lat[0])
        end_name = get_place_name(lon=gpx_track.list_lon[-1], lat=gpx_track.list_lat[-1])

        display_start = not close_to_start
        display_end = not (close_to_end or is_closed)

        #######

        h, w = elevation.elevation.shape[:2]
        x_pix, y_pix = elevation.project_on_image(gpx_track.list_lon, gpx_track.list_lat)

        plt.imshow(np.full((h, w), fill_value=np.nan))

        # plt.axhline(h * layout.title_relative_h)
        # plt.axhline(h * (layout.title_relative_h + layout.map_relative_h))
        # plt.axhline(h * (layout.title_relative_h + layout.map_relative_h + layout.elevation_relative_h))

        # plt.plot(x_pix[0], y_pix[0], "xk", markersize=10)
        # plt.plot(x_pix[-1], y_pix[-1], "ok", markersize=10)

        x_peaks = [x_pix[idx] for idx in passes_ids]
        y_peaks = [y_pix[idx] for idx in passes_ids]
        # plt.plot(x_peaks, y_peaks, '^', color="g", markersize=10)

        ######
        plt.axis('off')
        fig = plt.gcf()
        fig.set_size_inches(w/fig.get_dpi(), h/fig.get_dpi())
        fig.tight_layout(pad=0)

        list_x: List[float] = []
        list_y: List[float] = []
        list_text: List[str] = []

        for idx, mountain_pass in zip(passes_ids, mountain_passes):
            list_x.append(x_pix[idx])
            list_y.append(y_pix[idx])
            list_text.append(mountain_pass_to_str(mountain_pass))

        if display_start:
            list_x.append(x_pix[0])
            list_y.append(y_pix[0])
            list_text.append(f" {start_name} ")

        if display_end:
            list_x.append(x_pix[-1])
            list_y.append(y_pix[-1])
            list_text.append(f" {end_name} ")

        result_text_xy, result_line = ta.allocate(plt.gca(),
                                                  list_x, list_y,
                                                  list_text,
                                                  x_scatter=list_x+x_peaks, y_scatter=list_y+y_peaks,
                                                  textsize=TEXT_FONT_SIZE,
                                                  textcolor="b",
                                                  x_lines=[x_pix, [0., w], [0., w]],
                                                  y_lines=[y_pix,
                                                           [h * layout.title_relative_h,
                                                            h * layout.title_relative_h],
                                                           [h * (layout.title_relative_h + layout.map_relative_h),
                                                               h * (layout.title_relative_h + layout.map_relative_h)]],
                                                  max_distance=0.2,
                                                  min_distance=0.05,
                                                  margin=0.03,
                                                  linewidth=TEXT_LW,
                                                  linecolor='r',
                                                  nbr_candidates=1000,
                                                  draw_lines=True,
                                                  draw_all=False,
                                                  avoid_label_lines_overlap=True,
                                                  ha='center')

        hmin, hmax = np.min(gpx_track.list_ele), np.max(gpx_track.list_ele)

        h_up_pix = h * (layout.title_relative_h + layout.map_relative_h)
        h_bot_pix = h * (layout.title_relative_h + layout.map_relative_h + layout.elevation_relative_h)

        elevation_poly_x = np.linspace(0., w, num=len(gpx_track.list_ele))
        elevation_poly_y = h_bot_pix + (np.array(gpx_track.list_ele) - hmin) * (h_up_pix-h_bot_pix) / (hmax-hmin)

        elevation_peaks_x = [elevation_poly_x[closest_idx] for closest_idx in passes_ids]
        elevation_peaks_y = [elevation_poly_y[closest_idx] for closest_idx in passes_ids]

        elevation_poly_x = np.hstack((0, 0, elevation_poly_x, w, w)).tolist()
        elevation_poly_y = np.hstack((h, h_bot_pix, elevation_poly_y, h_bot_pix, h)).tolist()

        return CyclingImageCache(
            peaks_texts=TextAnnotations(s=list_text[:len(mountain_passes)],
                                        x=[x for x, _ in result_text_xy[:len(mountain_passes)]],
                                        y=[y for _, y in result_text_xy[:len(mountain_passes)]],
                                        fontsize=TEXT_FONT_SIZE,
                                        line_x=[list(x) for x, _ in result_line[:len(mountain_passes)]],
                                        line_y=[list(y) for _, y in result_line[:len(mountain_passes)]],
                                        lw=TEXT_LW),
            peaks_symbols=SymbolAnnotations(x=list_x[:len(mountain_passes)],
                                            y=list_y[:len(mountain_passes)],
                                            marker_size=PEAK_MARKER_SIZE,
                                            marker="^"),
            track_x=x_pix,
            track_y=y_pix,
            track_lw=TRACK_LW,
            elevation_map=elevation.elevation,
            elevation_shading=CachedHillShading(elevation.elevation),
            elevation_poly_x=elevation_poly_x,
            elevation_poly_y=elevation_poly_y,
            elevation_peaks_x=elevation_peaks_x,
            elevation_peaks_y=elevation_peaks_y,
            stats_x=0.5 * w,
            stats_y=0.5 * (h_bot_pix+h),
            title_x=0.5 * w,
            title_y=0.8 * h * layout.title_relative_h,
            stats_dist_km=dist_km,
            stats_uphill_m=uphill_m,
            start_text=TextAnnotations(s=[list_text[len(mountain_passes)]],
                                       x=[result_text_xy[len(mountain_passes)][0]],
                                       y=[result_text_xy[len(mountain_passes)][1]],
                                       fontsize=TEXT_FONT_SIZE,
                                       line_x=[list(result_line[len(mountain_passes)][0])],
                                       line_y=[list(result_line[len(mountain_passes)][1])],
                                       lw=TEXT_LW) if display_start else None,
            start_symbol=SymbolAnnotations(x=[list_x[len(mountain_passes)]],
                                           y=[list_y[len(mountain_passes)]],
                                           marker_size=PEAK_MARKER_SIZE,
                                           marker="o") if display_start else None,
            end_text=TextAnnotations(s=[list_text[len(mountain_passes)+1]],
                                     x=[result_text_xy[len(mountain_passes)+1][0]],
                                     y=[result_text_xy[len(mountain_passes)+1][1]],
                                     fontsize=TEXT_FONT_SIZE,
                                     line_x=[list(result_line[len(mountain_passes)+1][0])],
                                     line_y=[list(result_line[len(mountain_passes)+1][1])],
                                     lw=TEXT_LW) if display_end else None,
            end_symbol=SymbolAnnotations(x=[list_x[len(mountain_passes)+1]],
                                         y=[list_y[len(mountain_passes)+1]],
                                         marker_size=PEAK_MARKER_SIZE,
                                         marker="o") if display_end else None)

    def rescale(self, scale: float) -> 'CyclingImageCache':
        """pass"""
        new_h = int(scale*self.elevation_map.shape[0])
        new_w = int(scale*self.elevation_map.shape[1])
        new_elevation_map = cv2.resize(self.elevation_map, (new_w, new_h),
                                       interpolation=cv2.INTER_LANCZOS4)  # bicubic is ugly
        # FIXME fix aliasing when upsapling

        return CyclingImageCache(
            peaks_texts=self.peaks_texts.rescale(scale),
            peaks_symbols=self.peaks_symbols.rescale(scale),
            track_x=rescale(self.track_x, scale),
            track_y=rescale(self.track_y, scale),
            track_lw=self.track_lw*scale,
            elevation_poly_x=rescale(self.elevation_poly_x, scale),
            elevation_poly_y=rescale(self.elevation_poly_y, scale),
            elevation_peaks_x=rescale(self.elevation_peaks_x, scale),
            elevation_peaks_y=rescale(self.elevation_peaks_y, scale),
            elevation_map=new_elevation_map,
            elevation_shading=CachedHillShading(new_elevation_map),
            title_x=self.title_x*scale,
            title_y=self.title_y*scale,
            stats_x=self.stats_x*scale,
            stats_y=self.stats_y*scale,
            stats_dist_km=self.stats_dist_km,
            stats_uphill_m=self.stats_uphill_m,
            start_text=self.start_text.rescale(scale) if self.start_text is not None else None,
            start_symbol=self.start_symbol.rescale(scale) if self.start_symbol is not None else None,
            end_text=self.end_text.rescale(scale) if self.end_text is not None else None,
            end_symbol=self.end_symbol.rescale(scale) if self.end_symbol is not None else None,
        )

    def draw(self,
             fig: Figure,
             ax: Axes,
             azimuth: int,
             theme_colors: ThemeColors,
             title_txt: str = "La Marmotte",
             uphill_m: str = "",
             dist_km: str = ""):
        """aa"""
        ax.cla()
        ax.axis('off')
        fig.tight_layout(pad=0)

        h, w = self.elevation_map.shape[:2]
        fig.set_size_inches(w/fig.get_dpi(), h/fig.get_dpi())

        grey_hillshade = self.elevation_shading.render_grey(azimuth)
        background_color_rgb = hex_to_rgb(theme_colors.background_color)
        color_0 = (0, 0, 0) if theme_colors.dark_mode else background_color_rgb
        color_1 = background_color_rgb if theme_colors.dark_mode else (255, 255, 255)
        colored_hillshade = grey_hillshade * (np.array(color_1) - np.array(color_0)) + np.array(color_0)
        ax.imshow(colored_hillshade.astype(np.uint8))
        ax.autoscale(False)

        ax.plot(self.track_x, self.track_y, c=theme_colors.track_color, lw=self.track_lw)

        self.peaks_symbols.draw(ax, theme_colors.peak_color)
        self.peaks_texts.draw(ax, theme_colors.peak_color)

        if self.start_symbol is not None:
            self.start_symbol.draw(ax, theme_colors.peak_color)
            self.start_text.draw(ax, theme_colors.peak_color)

        if self.end_symbol is not None:
            self.end_symbol.draw(ax, theme_colors.peak_color)
            self.end_text.draw(ax, theme_colors.peak_color)

        ax.plot(self.elevation_peaks_x, self.elevation_peaks_y, "^",
                c=theme_colors.track_color, markersize=math.ceil(self.peaks_symbols.marker_size))

        ax.fill(self.elevation_poly_x, self.elevation_poly_y, c=theme_colors.peak_color)

        if title_txt != "":
            ax.text(self.title_x, self.title_y, title_txt, ha='center', va='center',
                    c=theme_colors.peak_color,
                    fontproperties=MY_FONT,
                    fontsize=60)

        dist_km_int = int(dist_km if dist_km != '' else self.stats_dist_km)
        uphill_m_int = int(uphill_m if uphill_m != '' else self.stats_uphill_m)
        stats_text = f"{dist_km_int} km - {uphill_m_int} m D+"
        ax.text(self.stats_x, self.stats_y, stats_text, ha='center', va='center',
                c=theme_colors.background_color,
                fontproperties=MY_FONT,
                fontsize=40)  # FIXME


# if __name__ == "__main__":
path = "data/marmotte-off.gpx"
# path = "data/3792286-les-fous-du-ventoux.gpx"
# path = "data/Cols_de_Soulor_Aubisque_Spandelles.gpx"
# path = "data/Ste_Marie_de_Campan_Hourquette_d_Ancizan_Col_de_Peyresourde_Col_d_Azet_Col_d_Aspin.gpx"
# path = "data/amberieu.gpx"

cache = CyclingImageCache.from_gpx(path)
# cache_hd = cache.rescale(1.0) # FIXME
cache = cache.rescale(0.3)


def on_file_upload(e: events.UploadEventArguments):
    ui.notify(f'File Uploaded {e.name}')
    cache = CyclingImageCache.from_gpx(path)
    cache = cache.rescale(0.3)
    ui.notify('Done')


ui.upload(multiple=False,
          auto_upload=True,
          on_upload=on_file_upload
          ).props('accept=.gpx').on('rejected', lambda: ui.notify('Please provide a GPX file')).classes('max-w-full')

with ui.row():
    with ui.pyplot(close=False) as plot:
        ax = plot.fig.add_subplot()

    with ui.column():
        def update():
            with plot:
                cache.draw(plot.fig, ax,
                           azimuth=AZIMUTHS[azimuth_toggle.value],
                           theme_colors=COLOR_THEMES[theme_toggle.value],
                           title_txt=title_button.value,
                           uphill_m=uphill_button.value,
                           dist_km=dist_km_button.value,
                           )
            ui.update(plot)

        def download():
            tmp_svg = "data/tmp.svg"
            plot.fig.savefig(tmp_svg)
            with open(tmp_svg, "rb") as svg_file:
                svg_bytes = svg_file.read()
            ui.download(svg_bytes, 'cycling_poster.svg')

        with ui.input(label='Title', value="Title").on('keydown.enter', update) as title_button:
            ui.tooltip("Press Enter to update title")

        with ui.input(label='D+ (m)', value="").on('keydown.enter', update) as uphill_button:
            ui.tooltip("Press Enter to override elevation from GPX")

        with ui.input(label='Distance (km)', value="").on('keydown.enter', update) as dist_km_button:
            ui.tooltip("Press Enter to override distance from GPX")

        azimuth_toggle = ui.toggle(list(AZIMUTHS.keys()), value=list(AZIMUTHS.keys())[0], on_change=update)
        theme_toggle = ui.toggle(list(COLOR_THEMES.keys()), value=list(COLOR_THEMES.keys())[0], on_change=update)
        ui.button('Download', on_click=download)

update()

ui.run()
