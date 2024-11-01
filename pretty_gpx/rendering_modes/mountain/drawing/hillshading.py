#!/usr/bin/python3
"""Cached Hill Shading."""
from typing import Final

import numpy as np

AZIMUTHS: Final[dict[str, int]] = {
    "North": 0,
    "East": 90,
    "South": 180,
    "West": 270
}


class CachedHillShading:
    """"Add caching around the implementation of `hillshade` method from `earthpy.spatial` module.

    A hillshade is a 3D representation of a surface. Hillshades are generally rendered in greyscale.
    The darker and lighter colors represent the shadows and highlights that you would visually expect
    to see in a terrain model.

    The sun is forced at altitude zero to increase the contrast.
    """

    def __init__(self, elevation: np.ndarray) -> None:
        x, y = np.gradient(elevation)
        slope = np.pi / 2.0 - np.arctan(np.sqrt(x*x + y*y))
        self.aspect = np.arctan2(-x, y)
        self.cos_slope = np.cos(slope)

        self.last_azimuth: int = -1
        self.last_img: np.ndarray = self.render_grey(0)

    def render_grey(self, azimuth: int) -> np.ndarray:
        """Render floating-point grayscale hillshade (inside [0., 1.])."""
        if self.last_azimuth == azimuth:
            return self.last_img

        # Hillshade
        azimuthrad = (360.0 - azimuth) * np.pi / 180.0
        shaded = self.cos_slope * np.cos((azimuthrad - np.pi / 2.0) - self.aspect)
        hillshade = 255 * (shaded + 1) / 2

        # Grey
        normalized_hillshade = (hillshade - np.min(hillshade))/(np.max(hillshade) - np.min(hillshade))

        grey_hillshade = (1.0 - np.power(normalized_hillshade, 1.3))

        self.last_img = grey_hillshade
        self.last_azimuth = azimuth

        return self.last_img
