#!/usr/bin/python3
"""Fonts."""
import os
from enum import Enum

from matplotlib.font_manager import FontProperties

from pretty_gpx.common.utils.paths import FONTS_DIR


class FontEnum(Enum):
    """Font Enum."""
    ANNOTATION = FontProperties(weight="bold")
    TITLE = FontProperties(fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf"))
    STATS = FontProperties(fname=os.path.join(FONTS_DIR, "Lobster 1.4.otf"))
