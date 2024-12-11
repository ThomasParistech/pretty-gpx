#!/usr/bin/python3
"""City Drawing Style/Size Config."""
from dataclasses import dataclass

from matplotlib.path import Path

from pretty_gpx.common.drawing.plt_marker import MarkerType
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.utils import mm_to_point
from pretty_gpx.rendering_modes.city.data.roads import CityRoadType

# Diagonal of the case used to set the reference value
REF_DIAGONAL_DISTANCE_M: float = 39298
REF_PAPER_SIZE: PaperSize = PAPER_SIZES["A4"]


@dataclass(kw_only=True)
class CityDrawingStyleConfig:
    """City Drawing Style Config."""
    start_marker: Path = MarkerType.DISK.path()
    end_marker: Path = MarkerType.SQUARE.path()
    bridge_marker: Path = MarkerType.BRIDGE.path()


@dataclass(kw_only=True)
class CityDrawingSizeConfig:
    """City Drawing Size Config."""
    paper_size: PaperSize

    caracteristic_distance: float

    linewidth_priority: dict[CityRoadType, float]
    track_linewidth: float

    text_fontsize: float
    text_arrow_linewidth: float
    title_fontsize: float
    stats_fontsize: float

    start_markersize: float
    end_markersize: float
    bridge_markersize: float
    poi_markersize: float

    @staticmethod
    def default(paper_size: PaperSize, diagonal_distance_m: float) -> 'CityDrawingSizeConfig':
        """Default City Drawing Size Config."""
        # Convert default A4 parameters to paper size
        ref_diag_mm = REF_PAPER_SIZE.diag_mm
        new_diag_mm = paper_size.diag_mm
        scale_paper = float(new_diag_mm/ref_diag_mm)
        scale_bounds = float(REF_DIAGONAL_DISTANCE_M/diagonal_distance_m)
        scale = scale_paper*scale_bounds

        linewidth_priority = {
            CityRoadType.HIGHWAY: 1.0*scale,
            CityRoadType.SECONDARY_ROAD: 0.5*scale,
            CityRoadType.STREET: 0.25*scale,
            CityRoadType.ACCESS_ROAD: 0.1*scale
        }

        # Set a maximum track linewidth to avoid masking data
        max_track_linewidth = (linewidth_priority[CityRoadType.SECONDARY_ROAD] +
                               linewidth_priority[CityRoadType.SECONDARY_ROAD])/2.0
        track_linewidth = min(2.0 * scale, max_track_linewidth)

        return CityDrawingSizeConfig(text_fontsize=mm_to_point(3.0) * scale_paper,
                                     text_arrow_linewidth=mm_to_point(0.3) * scale_paper,
                                     title_fontsize=mm_to_point(20.0) * scale_paper,
                                     stats_fontsize=mm_to_point(14) * scale_paper,
                                     start_markersize=mm_to_point(3.5) * scale_paper,
                                     end_markersize=mm_to_point(3.5) * scale_paper,
                                     bridge_markersize=mm_to_point(7.0) * scale_paper,
                                     poi_markersize=mm_to_point(7.0) * scale_paper,
                                     track_linewidth=track_linewidth,
                                     caracteristic_distance=diagonal_distance_m,
                                     linewidth_priority=linewidth_priority,
                                     paper_size=paper_size)
