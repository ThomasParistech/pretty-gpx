#!/usr/bin/python3
"""Parameters for City Posters."""
from dataclasses import dataclass

from matplotlib.font_manager import FontProperties

from pretty_gpx.common.drawing.components.annotated_scatter import AnnotatedScatterParams
from pretty_gpx.common.drawing.components.annotated_scatter import ScatterParams
from pretty_gpx.common.drawing.utils.color_theme import DarkTheme
from pretty_gpx.common.drawing.utils.drawing_figure import A4Float
from pretty_gpx.common.drawing.utils.drawing_figure import MetersFloat
from pretty_gpx.common.drawing.utils.fonts import FontEnum
from pretty_gpx.common.drawing.utils.plt_marker import MarkerType
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.rendering_modes.city.data.roads import CityRoadPrecision
from pretty_gpx.rendering_modes.city.data.roads import CityRoadType
from pretty_gpx.rendering_modes.city.drawing.city_colors import CITY_COLOR_THEMES


@dataclass
class CityParams:
    """Parameters for City Posters."""
    track_lw: A4Float
    track_color: str

    scatter_params: dict[ScatterPointCategory, ScatterParams]
    annot_params: dict[ScatterPointCategory, AnnotatedScatterParams]
    annot_fontproperties: FontProperties
    annot_ha: str
    annot_va: str

    city_roads_lw: dict[CityRoadType, MetersFloat]
    city_dark_mode: bool
    city_background_color: str
    city_farmland_color: str
    city_rivers_color: str
    city_forests_color: str

    profile_scatter_params: dict[ScatterPointCategory, ScatterParams]
    profile_fill_color: str
    profile_font_color: str
    profile_font_size: A4Float
    profile_fontproperties: FontProperties

    centered_title_font_color: str
    centered_title_font_size: A4Float
    centered_title_fontproperties: FontProperties

    user_title: str | None = None
    user_uphill_m: int | None = None
    user_dist_km: float | None = None
    user_road_precision: CityRoadPrecision = CityRoadPrecision.MEDIUM

    @staticmethod
    def default() -> "CityParams":
        """Default City Parameters."""
        return CityParams(
            track_lw=A4Float(mm=1.0),
            track_color="white",
            scatter_params={
                ScatterPointCategory.CITY_BRIDGE: ScatterParams(markersize=A4Float(mm=3.5),
                                                                marker=MarkerType.BRIDGE,
                                                                color="m"),
                ScatterPointCategory.CITY_POI_DEFAULT: ScatterParams(markersize=A4Float(mm=3.5),
                                                                     marker=MarkerType.MUSEUM,
                                                                     color="m"),
                ScatterPointCategory.CITY_POI_GREAT: ScatterParams(markersize=A4Float(mm=3.5),
                                                                   marker=MarkerType.STAR,
                                                                   color="m"),
                ScatterPointCategory.START: ScatterParams(markersize=A4Float(mm=3.5),
                                                          marker=MarkerType.DISK,
                                                          color="m"),
                ScatterPointCategory.END: ScatterParams(markersize=A4Float(mm=3.5),
                                                        marker=MarkerType.SQUARE,
                                                        color="m")
            },
            annot_params={
                ScatterPointCategory.CITY_BRIDGE: AnnotatedScatterParams(arrow_linewidth=A4Float(mm=0.5),
                                                                         fontsize=A4Float(mm=3.0)),
                ScatterPointCategory.CITY_POI_DEFAULT: AnnotatedScatterParams(arrow_linewidth=A4Float(mm=0.5),
                                                                              fontsize=A4Float(mm=3.0)),
                ScatterPointCategory.CITY_POI_GREAT: AnnotatedScatterParams(arrow_linewidth=A4Float(mm=0.5),
                                                                            fontsize=A4Float(mm=3.0)),
                ScatterPointCategory.START: AnnotatedScatterParams(arrow_linewidth=A4Float(mm=0.5),
                                                                   fontsize=A4Float(mm=3.0)),
                ScatterPointCategory.END: AnnotatedScatterParams(arrow_linewidth=A4Float(mm=0.5),
                                                                 fontsize=A4Float(mm=3.0))
            },
            annot_fontproperties=FontEnum.ANNOTATION.value,
            annot_ha="center",
            annot_va="center",
            city_roads_lw={
                CityRoadType.HIGHWAY: MetersFloat(m=40.0),
                CityRoadType.SECONDARY_ROAD: MetersFloat(m=20),
                CityRoadType.STREET: MetersFloat(m=10),
                CityRoadType.ACCESS_ROAD: MetersFloat(m=5)
            },
            city_dark_mode=CITY_COLOR_THEMES[DarkTheme.BLUE_PURPLE_YELLOW].dark_mode,
            city_background_color=CITY_COLOR_THEMES[DarkTheme.BLUE_PURPLE_YELLOW].background_color,
            city_farmland_color=CITY_COLOR_THEMES[DarkTheme.BLUE_PURPLE_YELLOW].farmland_color,
            city_rivers_color=CITY_COLOR_THEMES[DarkTheme.BLUE_PURPLE_YELLOW].rivers_color,
            city_forests_color=CITY_COLOR_THEMES[DarkTheme.BLUE_PURPLE_YELLOW].forests_color,
            profile_scatter_params={
                ScatterPointCategory.CITY_BRIDGE: ScatterParams(markersize=A4Float(mm=3.5),
                                                                marker=MarkerType.BRIDGE,
                                                                color="m"),
                ScatterPointCategory.CITY_POI_DEFAULT: ScatterParams(markersize=A4Float(mm=3.5),
                                                                     marker=MarkerType.MUSEUM,
                                                                     color="m"),
                ScatterPointCategory.CITY_POI_GREAT: ScatterParams(markersize=A4Float(mm=3.5),
                                                                   marker=MarkerType.STAR,
                                                                   color="m"),
                ScatterPointCategory.START: ScatterParams(markersize=A4Float(mm=3.5),
                                                          marker=MarkerType.DISK,
                                                          color="m"),
                ScatterPointCategory.END: ScatterParams(markersize=A4Float(mm=3.5),
                                                        marker=MarkerType.SQUARE,
                                                        color="m")
            },
            profile_fill_color="green",
            profile_font_color="black",
            profile_font_size=A4Float(mm=14),
            profile_fontproperties=FontEnum.STATS.value,

            centered_title_font_color="cyan",
            centered_title_font_size=A4Float(mm=20),
            centered_title_fontproperties=FontEnum.TITLE.value
        )
