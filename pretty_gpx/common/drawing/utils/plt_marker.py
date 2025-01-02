#!/usr/bin/python3
"""Matplotlib Marker."""
import os
from enum import auto
from enum import Enum
from typing import Final

import numpy as np
from matplotlib.path import Path
from svgpath2mpl import parse_path
from svgpathtools import svg2paths

from pretty_gpx.common.utils.paths import ICONS_DIR


class MarkerType(Enum):
    """Marker Type."""
    STAR = auto()
    HOUSE = auto()
    BRIDGE = auto()
    MUSEUM = auto()
    CAMPING = auto()

    TRIANGLE = auto()
    SQUARE = auto()
    DISK = auto()

    def path(self) -> Path:
        """Get the Matplotlib path."""
        return MARKERS[self]


def _load_marker(m: MarkerType) -> Path:
    """Generate a Matplotlib marker from an SVG path."""
    # See examples at https://www.iconfinder.com/

    # Load SVG
    svg_filepath = os.path.join(ICONS_DIR, f"{m.name.lower()}.svg")
    svg_paths, _ = svg2paths(svg_filepath)
    image_marker = parse_path(" ".join([p.d() for p in svg_paths]))

    # Center
    min_xy = np.min(image_marker.vertices, axis=0)
    max_xy = np.max(image_marker.vertices, axis=0)
    center_xy = 0.5 * (min_xy + max_xy)
    image_marker.vertices -= center_xy

    # Flip vertically
    image_marker.vertices[:, 1] *= -1

    # No need to scale, Matplotlib will normalized it to the box (-0.5, 0.5)x(-0.5, 0.5)
    return image_marker


MARKERS: Final[dict[MarkerType, Path]] = {m: _load_marker(m) for m in MarkerType}
