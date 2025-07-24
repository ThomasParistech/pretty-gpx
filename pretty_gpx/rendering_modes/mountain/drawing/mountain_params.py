#!/usr/bin/python3
"""Parameters for Mountain Posters."""
from dataclasses import dataclass

from matplotlib.font_manager import FontProperties

from pretty_gpx.common.drawing.components.annotated_scatter import AnnotatedScatterParams
from pretty_gpx.common.drawing.components.annotated_scatter import ScatterParams
from pretty_gpx.common.drawing.utils.color_theme import DarkTheme
from pretty_gpx.common.drawing.utils.drawing_figure import A4Float
from pretty_gpx.common.drawing.utils.fonts import ANNOTATION_FONT
from pretty_gpx.common.drawing.utils.fonts import CustomFont
from pretty_gpx.common.drawing.utils.fonts import TITLE_FONTS
from pretty_gpx.common.drawing.utils.plt_marker import MarkerType
from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.rendering_modes.mountain.drawing.mountain_colors import MOUNTAIN_COLOR_THEMES


@dataclass
class MountainParams:
    """Parameters for Mountain Posters."""
    track_lw: A4Float
    track_color: str

    scatter_params: dict[ScatterPointCategory, ScatterParams]
    annot_params: dict[ScatterPointCategory, AnnotatedScatterParams]
    annot_fontproperties: FontProperties
    annot_ha: str
    annot_va: str

    mountain_background_color: str
    mountain_dark_mode: bool
    mountain_azimuth: int

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

    @staticmethod
    def default() -> "MountainParams":
        """Default Mountain Parameters."""
        return MountainParams(
            track_lw=A4Float(mm=1.0),
            track_color="white",
            scatter_params={
                ScatterPointCategory.MOUNTAIN_PASS: ScatterParams(markersize=A4Float(mm=3.5),
                                                                  marker=MarkerType.TRIANGLE,
                                                                  color="m"),
                ScatterPointCategory.START: ScatterParams(markersize=A4Float(mm=3.5),
                                                          marker=MarkerType.DISK,
                                                          color="m"),
                ScatterPointCategory.END: ScatterParams(markersize=A4Float(mm=3.5),
                                                        marker=MarkerType.SQUARE,
                                                        color="m")
            },
            annot_params={
                ScatterPointCategory.MOUNTAIN_PASS: AnnotatedScatterParams(arrow_linewidth=A4Float(mm=0.5),
                                                                           fontsize=A4Float(mm=3.0)),
                ScatterPointCategory.START: AnnotatedScatterParams(arrow_linewidth=A4Float(mm=0.5),
                                                                   fontsize=A4Float(mm=3.0)),
                ScatterPointCategory.END: AnnotatedScatterParams(arrow_linewidth=A4Float(mm=0.5),
                                                                 fontsize=A4Float(mm=3.0))
            },
            annot_fontproperties=ANNOTATION_FONT.value,
            annot_ha="center",
            annot_va="center",
            mountain_background_color=MOUNTAIN_COLOR_THEMES[DarkTheme.BLUE_PURPLE_YELLOW].background_color,
            mountain_dark_mode=MOUNTAIN_COLOR_THEMES[DarkTheme.BLUE_PURPLE_YELLOW].dark_mode,
            mountain_azimuth=90,
            profile_scatter_params={
                ScatterPointCategory.MOUNTAIN_PASS: ScatterParams(markersize=A4Float(mm=3.5),
                                                                  marker=MarkerType.TRIANGLE,
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
            profile_fontproperties=CustomFont.LOBSTER.value,

            centered_title_font_color="cyan",
            centered_title_font_size=A4Float(mm=20),
            centered_title_fontproperties=TITLE_FONTS[0].value
        )
