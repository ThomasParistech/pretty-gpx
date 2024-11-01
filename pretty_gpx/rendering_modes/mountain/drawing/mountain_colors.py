#!/usr/bin/python3
"""Mountain Colors."""

from dataclasses import dataclass
from typing import Final

from pretty_gpx.common.drawing.color_theme import DarkTheme
from pretty_gpx.common.drawing.color_theme import LightTheme


@dataclass
class MountainColors:
    """Mountain Colors."""
    dark_mode: bool
    background_color: str
    track_color: str
    peak_color: str


MOUNTAIN_COLOR_THEMES: Final[dict[DarkTheme | LightTheme, MountainColors]] = {
    DarkTheme.BLACK_GREEN_YELLOW:  MountainColors(dark_mode=True,
                                                  background_color="#264653",
                                                  track_color="#2a9d8f",
                                                  peak_color="#e9c46a"),
    DarkTheme.BLACK_RED_WHITE: MountainColors(dark_mode=True,
                                              background_color="#393e41",
                                              track_color="#e94f37",
                                              peak_color="#f6f7eb"),
    DarkTheme.BLACK_BLUE_WHITE: MountainColors(dark_mode=True,
                                               background_color="#4a598c",
                                               track_color="#69a1f7",
                                               peak_color="#e1ebfb"),
    DarkTheme.BLUE_PURPLE_YELLOW: MountainColors(dark_mode=True,
                                                 background_color="#34447d",
                                                 track_color="#8390fa",
                                                 peak_color="#fac748"),
    LightTheme.YELLOW_GREEN_BLACK: MountainColors(dark_mode=False,
                                                  background_color="#e9c46a",
                                                  track_color="#2a9d8f",
                                                  peak_color="#264653"),
    LightTheme.WHITE_RED_BLACK: MountainColors(dark_mode=False,
                                               background_color="#bfdbf7",
                                               track_color="#f87060",
                                               peak_color="#102542"),
    LightTheme.WHITE_BLUE_BLACK: MountainColors(dark_mode=False,
                                                background_color="#cadcfc",
                                                track_color="#69a1f7",
                                                peak_color="#00246b"),
    LightTheme.YELLOW_RED_BLACK: MountainColors(dark_mode=False,
                                                background_color="#eaaa33",
                                                track_color="#840032",
                                                peak_color="#002642")
}
