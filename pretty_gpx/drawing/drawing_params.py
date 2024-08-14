#!/usr/bin/python3
"""Drawing Parameters."""
from dataclasses import dataclass

from matplotlib.font_manager import FontProperties

from pretty_gpx.utils import mm_to_point


@dataclass
class DrawingParams:
    """Drawing Parameters."""
    text_fontsize: float = mm_to_point(5.0)
    text_arrow_linewidth: float = mm_to_point(0.3)

    title_fontsize: float = mm_to_point(20.0)
    stats_fontsize: float = mm_to_point(20.0)

    peak_markersize: float = mm_to_point(4.0)

    track_linewidth: float = mm_to_point(1.0)

    classic_font: FontProperties = FontProperties()
    pretty_font: FontProperties = FontProperties(fname="./Lobster 1.4.otf")
