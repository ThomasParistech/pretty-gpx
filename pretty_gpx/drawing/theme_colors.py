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


COLOR_THEMES: dict[str, ThemeColors] = {
    "DARK_A": ThemeColors(dark_mode=True,
                          background_color="#393e41",
                          track_color="#e94f37",
                          peak_color="#f6f7eb"),
    "DARK_B": ThemeColors(dark_mode=True,
                          background_color="#264653",
                          track_color="#2a9d8f",
                          peak_color="#e9c46a"),
    "LIGHT_C": ThemeColors(dark_mode=False,
                           background_color="#e9c46a",
                           track_color="#2a9d8f",
                           peak_color="#264653"),
    "LIGHT_D": ThemeColors(dark_mode=False,
                           background_color="#e59500",
                           track_color="#002642",
                           peak_color="#840032")
}


def hex_to_rgb(hex_color: str) -> tuple[int, ...]:
    """Convert hexadecimal color string to RGB triplet."""
    rgb_tuple = colors.hex2color(hex_color)
    rgb_int_tuple = tuple(int(x * 255) for x in rgb_tuple)
    return rgb_int_tuple
