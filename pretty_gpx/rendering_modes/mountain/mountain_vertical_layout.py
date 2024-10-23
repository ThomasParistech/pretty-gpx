#!/usr/bin/python3
"""Mountain Vertical Layout."""
from dataclasses import dataclass

from pretty_gpx.common.layout.elevation_vertical_layout import ElevationVerticalLayout


@dataclass(kw_only=True)
class MountainVerticalLayout(ElevationVerticalLayout):
    """Mountain Vertical Layout."""

    @staticmethod
    def default() -> 'MountainVerticalLayout':
        """Return the default Mountain Vertical Layout."""
        return MountainVerticalLayout(title_relative_h=0.18,
                                      map_relative_h=0.6,
                                      elevation_relative_h=0.1,
                                      stats_relative_h=0.12)
