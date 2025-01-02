#!/usr/bin/python3
"""Drawing Component for a Centered Title."""
from dataclasses import dataclass
from typing import Protocol

from matplotlib.font_manager import FontProperties

from pretty_gpx.common.drawing.utils.drawing_figure import A4Float
from pretty_gpx.common.drawing.utils.drawing_figure import DrawingFigure
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.utils import get


class CenteredTitleParamsProtocol(Protocol):
    """Protocol for Centered Title Parameters."""
    centered_title_font_color: str
    centered_title_font_size: A4Float
    centered_title_fontproperties: FontProperties

    user_title: str | None


@dataclass
class CenteredTitle:
    """Drawing Component for a Centered Title."""
    bounds: GpxBounds

    def change_papersize(self, paper: PaperSize, bounds: GpxBounds) -> None:
        """Change Paper Size and GPX Bounds."""
        self.bounds = bounds

    def draw(self, fig: DrawingFigure, params: CenteredTitleParamsProtocol) -> None:
        """Draw the title text."""
        # Text
        fig.text(lon=self.bounds.lon_center, lat=self.bounds.lat_max - 0.8*self.bounds.dlat,
                 s=get(params.user_title, ""),
                 color=params.centered_title_font_color,
                 fontsize=params.centered_title_font_size,
                 font=params.centered_title_fontproperties,
                 ha="center", va="center")
