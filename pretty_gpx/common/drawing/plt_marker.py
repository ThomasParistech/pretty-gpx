#!/usr/bin/python3
"""Matplotlib Marker."""

import os
from enum import auto
from enum import Enum
from typing import Final

import matplotlib as mpl
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

    TRIANGLE = auto()
    SQUARE = auto()
    DISK = auto()

    def path(self) -> Path:
        """Get the Matplotlib path."""
        return MARKERS[self]


def _load_marker(m: MarkerType) -> Path:
    """Generate a Matplotlib marker from an SVG path."""
    svg_path = os.path.join(ICONS_DIR, f"{m.name.lower()}.svg")

    # See https://www.iconfinder.com/
    svg_paths, _ = svg2paths(svg_path)

    image_marker = parse_path(" ".join([p.d() for p in svg_paths]))

    # Center
    image_marker.vertices -= np.mean(image_marker.vertices, axis=0)

    # Rotate 180° and flip horizontally
    image_marker = image_marker.transformed(mpl.transforms.Affine2D().rotate_deg(180))
    image_marker = image_marker.transformed(mpl.transforms.Affine2D().scale(-1, 1))

    # No need to scale, Matplotlib will normalized it to the box (-0.5, 0.5)x(-0.5, 0.5)
    return image_marker


MARKERS: Final[dict[MarkerType, Path]] = {m: _load_marker(m) for m in MarkerType}
