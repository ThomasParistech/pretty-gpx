#!/usr/bin/python3
"""Colors."""

from dataclasses import dataclass

from matplotlib import colors


@dataclass
class ThemeColors:
    """Theme Colors."""
    dark_mode: bool
    background_color: str
    track_color: str
    point_color: str
    rivers_color: str
    railways_color: str
    sleepers_color: str


DARK_COLOR_THEMES: dict[str, ThemeColors] = {
    "⬛🟩🟨": ThemeColors(dark_mode=True,
                            background_color="#264653",
                            track_color="#2a9d8f",
                            point_color="#e9c46a",
                            rivers_color="#89b0ba",
                            railways_color="#8C8C8C",
                            sleepers_color="#999999"),
    "⬛🟥⬜": ThemeColors(dark_mode=True,
                            background_color="#393e41",
                            track_color="#e94f37",
                            point_color="#e9c46a",
                            rivers_color="#96b6bf",
                            railways_color="#8C8C8C",
                            sleepers_color="#999999"),
    "⬛🟦⬜": ThemeColors(dark_mode=True,
                            background_color="#4a598c",
                            track_color="#69a1f7",
                            point_color="#e9c46a",
                            rivers_color="#9cb4d0",
                            railways_color="#8C8C8C",
                            sleepers_color="#999999"),
    "🟦🟪🟨": ThemeColors(dark_mode=True,
                            background_color="#34447d",
                            track_color="#8390fa",
                            point_color="#e9c46a",
                            rivers_color="#91a6c6",
                            railways_color="#8C8C8C",
                            sleepers_color="#999999")

}

LIGHT_COLOR_THEMES: dict[str, ThemeColors] = {
    "🟨🟩⬛": ThemeColors(dark_mode=False,
                            background_color="#e9c46a",
                            track_color="#2a9d8f",
                            point_color="#264653",
                            rivers_color="#a5b8cf",
                            railways_color="#737373",
                            sleepers_color="#666666"),
    "⬜🟥⬛": ThemeColors(dark_mode=False,
                            background_color="#bfdbf7",
                            track_color="#f87060",
                            point_color="#f87060",
                            rivers_color="#b0c8e2",
                            railways_color="#737373",
                            sleepers_color="#666666"),
    "⬜🟦⬛": ThemeColors(dark_mode=False,
                            background_color="#cadcfc",
                            track_color="#69a1f7",
                            point_color="#405480",
                            rivers_color="#acc3dd",
                            railways_color="#737373",
                            sleepers_color="#666666"),
    "🟨🟥⬛": ThemeColors(dark_mode=False,
                            background_color="#eaaa33",
                            track_color="#840032",
                            point_color="#840032",
                            rivers_color="#a8bad6",
                            railways_color="#737373",
                            sleepers_color="#666666")
}


def hex_to_rgb(hex_color: str) -> tuple[int, ...]:
    """Convert hexadecimal color string to RGB triplet."""
    rgb_tuple = colors.hex2color(hex_color)
    rgb_int_tuple = tuple(int(x * 255) for x in rgb_tuple)
    return rgb_int_tuple
