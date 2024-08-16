#!/usr/bin/python3
"""Matplotlib Marker."""

import matplotlib as mpl
import numpy as np
from matplotlib.path import Path
from svgpath2mpl import parse_path
from svgpathtools import svg2paths


def marker_from_svg(svg_path: str) -> Path:
    """Generate a Matplotlib marker from an SVG path."""
    # See https://www.iconfinder.com/
    _, attributes = svg2paths(svg_path)

    image_marker = parse_path(attributes[0]['d'])

    # Center
    image_marker.vertices -= np.mean(image_marker.vertices, axis=0)

    # Rotate 180° and flip horizontally
    image_marker = image_marker.transformed(mpl.transforms.Affine2D().rotate_deg(180))
    image_marker = image_marker.transformed(mpl.transforms.Affine2D().scale(-1, 1))

    # No need to scale, Matplotlib will normalized it to the box (-0.5, 0.5)x(-0.5, 0.5)
    return image_marker
