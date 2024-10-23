"""Linewidth for city drawings."""
from dataclasses import dataclass

import numpy as np

from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.rendering_modes.city.data.roads import CityRoadType

# Diagonal of the case used to set the reference value
REF_DIAGONAL_DISTANCE_M: float = 39298
REF_PAPER_SIZE: PaperSize = PAPER_SIZES["A4"]


@dataclass(kw_only=True)
class CityLinewidthParams:
    """City Linewidth Parameters."""
    paper_size: PaperSize

    caracteristic_distance: float

    linewidth_priority: dict[CityRoadType, float]
    linewidth_track: float

    def change_paper_size(self, new_paper_size: PaperSize) -> 'CityLinewidthParams':
        """Scale parameters to new paper size."""
        current_diag_mm = np.linalg.norm([self.paper_size.w_mm, self.paper_size.h_mm])
        new_diag_mm = np.linalg.norm([new_paper_size.w_mm, new_paper_size.h_mm])
        scale = float(new_diag_mm/current_diag_mm)

        updated_lw_priority = {road_type: value * scale for road_type, value in self.linewidth_priority.items()}
        updated_lw_track = self.linewidth_track * scale

        return CityLinewidthParams(paper_size=new_paper_size,
                                   caracteristic_distance=self.caracteristic_distance*scale,
                                   linewidth_priority=updated_lw_priority,
                                   linewidth_track=updated_lw_track)

    @staticmethod
    def default(paper_size: PaperSize, diagonal_distance_m: float) -> 'CityLinewidthParams':
        """Default Drawing Size Parameters."""
        # Convert default A4 parameters to paper size
        ref_diag_mm = np.linalg.norm([REF_PAPER_SIZE.w_mm, REF_PAPER_SIZE.h_mm])
        new_diag_mm = np.linalg.norm([paper_size.w_mm, paper_size.h_mm])
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
        linewidth_track = min(2.0 * scale, max_track_linewidth)

        return CityLinewidthParams(paper_size=paper_size,
                                   caracteristic_distance=diagonal_distance_m,
                                   linewidth_priority=linewidth_priority,
                                   linewidth_track=linewidth_track)
