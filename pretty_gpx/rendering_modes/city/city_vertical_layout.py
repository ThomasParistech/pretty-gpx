#!/usr/bin/python3
"""City Vertical Layout."""
from dataclasses import dataclass

from pretty_gpx.common.layout.elevation_vertical_layout import ElevationVerticalLayout


@dataclass(kw_only=True)
class CityVerticalLayout(ElevationVerticalLayout):
    """City Vertical Layout."""

    _LAYOUTS = {'single_line_stats', 'two_lines_stats'}

    @staticmethod
    def single_line_stats() -> 'CityVerticalLayout':
        """Return the default City Vertical Layout."""
        return CityVerticalLayout(title_relative_h=0.18,
                                  map_relative_h=0.65,
                                  elevation_relative_h=0.05,
                                  stats_relative_h=0.12)

    @staticmethod
    def two_lines_stats() -> 'CityVerticalLayout':
        """Return the default City Vertical Layout with a bigger stat height to have 2 lines."""
        return CityVerticalLayout(title_relative_h=0.18,
                                  map_relative_h=0.57,
                                  elevation_relative_h=0.05,
                                  stats_relative_h=0.20)
