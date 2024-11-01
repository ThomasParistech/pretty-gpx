#!/usr/bin/python3
"""City Colors."""

from dataclasses import dataclass
from typing import Final

from pretty_gpx.common.drawing.color_theme import DarkTheme
from pretty_gpx.common.drawing.color_theme import LightTheme


@dataclass
class CityColors:
    """Theme Colors."""
    dark_mode: bool
    background_color: str
    track_color: str
    point_color: str
    rivers_color: str
    forests_color: str
    farmland_color: str


CITY_COLOR_THEMES: Final[dict[DarkTheme | LightTheme, CityColors]] = {
    DarkTheme.BLACK_GREEN_YELLOW:  CityColors(dark_mode=True,
                                              background_color="#264653",
                                              track_color="#2a9d8f",
                                              point_color="#e9c46a",
                                              rivers_color="#89b0ba",
                                              forests_color="#3b6b7f",
                                              farmland_color="#305866"),
    DarkTheme.BLACK_RED_WHITE:  CityColors(dark_mode=True,
                                           background_color="#393e41",
                                           track_color="#e94f37",
                                           point_color="#e9c46a",
                                           rivers_color="#96b6bf",
                                           forests_color="#4f595d",
                                           farmland_color="#424649"),
    DarkTheme.BLACK_BLUE_WHITE: CityColors(dark_mode=True,
                                           background_color="#4a598c",
                                           track_color="#69a1f7",
                                           point_color="#e9c46a",
                                           rivers_color="#9cb4d0",
                                           forests_color="#5c6a9b",
                                           farmland_color="#525d89"),
    DarkTheme.BLUE_PURPLE_YELLOW: CityColors(dark_mode=True,
                                             background_color="#34447d",
                                             track_color="#8390fa",
                                             point_color="#e9c46a",
                                             rivers_color="#91a6c6",
                                             forests_color="#4f5d91",
                                             farmland_color="#414c84"),
    LightTheme.YELLOW_GREEN_BLACK:  CityColors(dark_mode=False,
                                               background_color="#e9c46a",
                                               track_color="#2a9d8f",
                                               point_color="#264653",
                                               rivers_color="#a5b8cf",
                                               forests_color="#b39335",
                                               farmland_color="#b9b359"),
    LightTheme.WHITE_RED_BLACK:  CityColors(dark_mode=False,
                                            background_color="#bfdbf7",
                                            track_color="#f87060",
                                            point_color="#f87060",
                                            rivers_color="#b0c8e2",
                                            forests_color="#94b0d4",
                                            farmland_color="#a6b8c1"),
    LightTheme.WHITE_BLUE_BLACK: CityColors(dark_mode=False,
                                            background_color="#cadcfc",
                                            track_color="#69a1f7",
                                            point_color="#405480",
                                            rivers_color="#acc3dd",
                                            forests_color="#9bb0db",
                                            farmland_color="#b2c3e1"),
    LightTheme.YELLOW_RED_BLACK: CityColors(dark_mode=False,
                                            background_color="#eaaa33",
                                            track_color="#840032",
                                            point_color="#840032",
                                            rivers_color="#a8bad6",
                                            forests_color="#b4882c",
                                            farmland_color="#c18d1a")
}
