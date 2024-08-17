#!/usr/bin/python3
"""Drawing Parameters."""
import os
from dataclasses import dataclass

from matplotlib.font_manager import FontProperties
from matplotlib.path import Path

from pretty_gpx import FONTS_DIR
from pretty_gpx import ICONS_DIR
from pretty_gpx.drawing.plt_marker import marker_from_svg
from pretty_gpx.utils import mm_to_point


@dataclass
class DrawingParams:
    """Drawing Parameters."""
    text_fontsize: float = mm_to_point(5.0)
    text_arrow_linewidth: float = mm_to_point(0.3)

    title_fontsize: float = mm_to_point(20.0)
    stats_fontsize: float = mm_to_point(20.0)

    start_markersize: float = mm_to_point(4.0)
    start_marker: str | Path = "o"

    end_markersize: float = mm_to_point(4.0)
    end_marker: str | Path = "s"

    peak_markersize: float = mm_to_point(4.0)
    peak_marker: str | Path = "^"

    hut_markersize: float = mm_to_point(7.0)
    hut_marker: str | Path = marker_from_svg(os.path.join(ICONS_DIR, "house.svg"))

    track_linewidth: float = mm_to_point(1.0)

    classic_font: FontProperties = FontProperties()
    pretty_font: FontProperties = FontProperties(fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf"))
