#!/usr/bin/python3
"""Light/Dark Color Theme."""
from enum import auto
from enum import Enum
from typing import Final
from typing import Self

from matplotlib import colors


class _BaseTheme(Enum):
    """Base Color Theme."""

    @classmethod
    def get_mapping(cls) -> dict[str, Self]:
        """Return the mapping."""
        color_emojis: Final[dict[str, str]] = {
            "BLACK": "⬛",
            "RED": "🟥",
            "GREEN": "🟩",
            "YELLOW": "🟨",
            "BLUE": "🟦",
            "PURPLE": "🟪",
            "WHITE": "⬜"
        }
        return {''.join(color_emojis[color]
                        for color in x.name.split('_')): x
                for x in cls}


class DarkTheme(_BaseTheme):
    """Dark Color Theme."""
    BLACK_GREEN_YELLOW = auto()
    BLACK_RED_WHITE = auto()
    BLACK_BLUE_WHITE = auto()
    BLUE_PURPLE_YELLOW = auto()


class LightTheme(_BaseTheme):
    """Light Color Theme."""
    YELLOW_GREEN_BLACK = auto()
    WHITE_RED_BLACK = auto()
    WHITE_BLUE_BLACK = auto()
    YELLOW_RED_BLACK = auto()


def hex_to_rgb(hex_color: str) -> tuple[int, ...]:
    """Convert hexadecimal color string to RGB triplet."""
    rgb_tuple = colors.hex2color(hex_color)
    rgb_int_tuple = tuple(int(x * 255) for x in rgb_tuple)
    return rgb_int_tuple
