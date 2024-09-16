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
    peak_color: str


DARK_COLOR_THEMES: dict[str, ThemeColors] = {
    "⬛🟩🟨": ThemeColors(dark_mode=True,
                       background_color="#264653",
                       track_color="#2a9d8f",
                       peak_color="#e9c46a"),
    "⬛🟥⬜": ThemeColors(dark_mode=True,
                       background_color="#393e41",
                       track_color="#e94f37",
                       peak_color="#f6f7eb"),
    "⬛🟦⬜": ThemeColors(dark_mode=True,
                       background_color="#4a598c",
                       track_color="#69a1f7",
                       peak_color="#e1ebfb"),
    "🟦🟪🟨": ThemeColors(dark_mode=True,
                       background_color="#34447d",
                       track_color="#8390fa",
                       peak_color="#fac748")
}

LIGHT_COLOR_THEMES: dict[str, ThemeColors] = {
    "🟨🟩⬛": ThemeColors(dark_mode=False,
                       background_color="#e9c46a",
                       track_color="#2a9d8f",
                       peak_color="#264653"),
    "⬜🟥⬛": ThemeColors(dark_mode=False,
                       background_color="#bfdbf7",
                       track_color="#f87060",
                       peak_color="#102542"),
    "⬜🟦⬛": ThemeColors(dark_mode=False,
                       background_color="#cadcfc",
                       track_color="#69a1f7",
                       peak_color="#00246b"),
    "🟨🟥⬛": ThemeColors(dark_mode=False,
                       background_color="#eaaa33",
                       track_color="#840032",
                       peak_color="#002642")
}


def hex_to_rgb(hex_color: str) -> tuple[int, ...]:
    """Convert hexadecimal color string to RGB triplet."""
    rgb_tuple = colors.hex2color(hex_color)
    rgb_int_tuple = tuple(int(x * 255) for x in rgb_tuple)
    return rgb_int_tuple
