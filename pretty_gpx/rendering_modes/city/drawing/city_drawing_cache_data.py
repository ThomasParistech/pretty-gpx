#!/usr/bin/python3
"""City Drawing Cache Data."""
from dataclasses import dataclass

from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.rendering_modes.city.data.city_augmented_gpx_data import CityAugmentedGpxData
from pretty_gpx.rendering_modes.city.drawing.city_drawer import CityDrawer


@dataclass
class CityDrawingCacheData:
    """City Drawing Cache Data."""
    drawer: CityDrawer

    gpx_data: CityAugmentedGpxData

    @staticmethod
    def from_gpx(gpx_path: str | bytes, paper_size: PaperSize) -> 'CityDrawingCacheData':
        """Create a CityDrawingCacheData from a GPX file."""
        # Extract GPX data and retrieve close City passes/huts
        gpx_data = CityAugmentedGpxData.from_path(gpx_path)
        return CityDrawingCacheData.from_augmented_gpx_data(gpx_data, paper_size)

    @staticmethod
    def from_augmented_gpx_data(gpx_data: CityAugmentedGpxData,
                                paper_size: PaperSize) -> 'CityDrawingCacheData':
        """Create a CityDrawingCacheData from a GPX file."""
        drawer = CityDrawer.from_gpx_data(gpx_data, paper_size)
        return CityDrawingCacheData(drawer, gpx_data)
