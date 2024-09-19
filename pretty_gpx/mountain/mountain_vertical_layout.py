#!/usr/bin/python3
"""Vertical Layout."""
from dataclasses import dataclass

from pretty_gpx.common.layout.base_vertical_layout import BaseVerticalLayout
from pretty_gpx.common.layout.base_vertical_layout import RelativeYBounds


@dataclass(kw_only=True)
class MountainVerticalLayout(BaseVerticalLayout):
    """Mountain Vertical Layout.

    ┌────────────────────────────────────────┐   ▲
    │                 Title                  │   │   title_relative_h
    ├───────────────────┬────────────────────┤   ▼
    │                   │  margin_rel_h      │   ▲
    │                   ▼                    │   |
    │                 xxxxxxxxxxxxxxx        │   │
    │                   xx           xxx     │   │
    │                      x           x◄────┤   │
    │                    xxxxx      xxxx     │   │
    │ margin_rel_w     xxx        xx         │   │
    ├────►xxxxxxxxxxxxxx            xx       │   │    map_relative_h
    │     x                     xxx          │   │
    │     xxxxxxxxxxxx       xx              │   │
    │                xxxxxxxx                │   │
    │                   ▲                    │   │
    │                   │                    │   ▼
    ├───────────────────┴────────────────────┤   ▲
    │         xxx          xxx         xx    │   |
    │  xxx  xxx  xx      xx  xx      xx xx   │   │   elevation_relative_h
    │xxx xxxx     xxxxxxx     xxxxxxxx   xxxx│   │
    ├────────────────────────────────────────┤   ▼
    │            100km - 1000m D+            │   ▲
    │                                        │   │   stats_relative_h
    └────────────────────────────────────────┘   ▼
    """
    title_relative_h: float = 0.18
    map_relative_h: float = 0.6
    elevation_relative_h: float = 0.1
    stats_relative_h: float = 0.12

    def _get_download_y_bounds(self) -> RelativeYBounds:
        """Get relative Vertical Bounds of the Download Area, e.g. (0.0, 1.0) for the entire paper."""
        # Elevation map would be hidden by the stats, no need to download this part
        return RelativeYBounds(bot=self.stats_relative_h, top=1.0)

    def _get_track_y_bounds(self) -> RelativeYBounds:
        """Get relative Vertical Bounds of the Track Area."""
        bot = self.stats_relative_h + self.elevation_relative_h
        return RelativeYBounds(bot=bot, top=bot+self.map_relative_h)

    def _get_track_margin(self) -> float:
        """Get relative Horizonal/Vertical Margin around the Track Area."""
        return 0.10
