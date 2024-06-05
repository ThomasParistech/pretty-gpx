#!/usr/bin/python3
"""Hill Shading."""
import numpy as np

AZIMUTHS: dict[str, int] = {
    "North": 0,
    "East": 90,
    "South": 180,
    "West": 270
}


class CachedHillShading:
    """"
    equivalent of
    # import earthpy.spatial as es
    # hillshade = es.hillshade(elevation)

    """

    def __init__(self, elevation: np.ndarray) -> None:
        """altitude=0"""
        x, y = np.gradient(elevation)
        slope = np.pi / 2.0 - np.arctan(np.sqrt(x*x + y*y))
        self.aspect = np.arctan2(-x, y)
        self.cos_slope = np.cos(slope)

        # self.grey_cmap = get_cmap("Greys") # FIXME: explain that there are ugly steps

        self.last_azimuth: int = -1
        self.last_img: np.ndarray = self.render_grey(0)

    def render_grey(self, azimuth: int) -> np.ndarray:
        """aaaaaa at, return flaot array """
        if self.last_azimuth == azimuth:
            return self.last_img

        # Hillshade
        azimuthrad = (360.0 - azimuth) * np.pi / 180.0
        shaded = self.cos_slope * np.cos((azimuthrad - np.pi / 2.0) - self.aspect)
        hillshade = 255 * (shaded + 1) / 2

        # Grey
        normalized_hillshade = (hillshade - np.min(hillshade))/(np.max(hillshade) - np.min(hillshade))

        grey_hillshade = (1.0 - np.power(normalized_hillshade, 1.3))[..., None]

        # # Colormap
        # colored_hillshade = grey_hillshade * (np.array(color_1) - np.array(color_0)) + np.array(color_0)

        # # plt.matshow(colored_hillshade.astype(np.uint8))
        # # # plt.matshow(get_cmap("Greys")(normalized_hillshade))
        # # plt.show()

        self.last_img = grey_hillshade
        self.last_azimuth = azimuth

        return self.last_img
