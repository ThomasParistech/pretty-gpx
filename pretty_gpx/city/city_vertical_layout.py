#!/usr/bin/python3
"""City Vertical Layout."""
from dataclasses import dataclass

from pretty_gpx.common.layout.elevation_vertical_layout import ElevationVerticalLayout


@dataclass(kw_only=True)
class CityVerticalLayout(ElevationVerticalLayout):
    """City Vertical Layout."""

    @staticmethod
    def default() -> 'CityVerticalLayout':
        """Return the default City Vertical Layout."""
        return CityVerticalLayout(title_relative_h=0.18,
                                  map_relative_h=0.65,
                                  elevation_relative_h=0.05,
                                  stats_relative_h=0.12)
