#!/usr/bin/python3
"""Explore new Color Themes."""
import itertools
import os
import shutil

import matplotlib.pyplot as plt
from tqdm import tqdm

from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.paths import COLOR_EXPLORATION_DIR
from pretty_gpx.common.utils.paths import CYCLING_DIR
from pretty_gpx.mountain.data.augmented_gpx_data import AugmentedGpxData
from pretty_gpx.mountain.drawing.poster_image_cache import PosterImageCache
from pretty_gpx.mountain.drawing.theme_colors import hex_to_rgb
from pretty_gpx.mountain.drawing.theme_colors import ThemeColors


def generate_color_candidates(colors: list[tuple[str, str, str]], dark_mode: bool) -> list[ThemeColors]:
    """Generate color candidates."""
    candidates: list[ThemeColors] = []
    for trio in colors:
        # Sort by brightness
        sorted_trio = sorted(trio, key=lambda c: sum(hex_to_rgb(c)))
        if dark_mode:
            sorted_trio.reverse()

        background_color = sorted_trio[2]

        for (track, peak) in itertools.permutations(sorted_trio[:2]):
            candidates.append(ThemeColors(dark_mode=dark_mode,
                                          background_color=background_color,
                                          track_color=track,
                                          peak_color=peak))
    return candidates


def main(color_palettes: list[tuple[str, str, str]]) -> None:
    """Explore new Color Themes.

    The project currently offers 4 dark and 4 light color themes, but you are encouraged to create and experiment
    with new ones!

    In dark mode, hillshading modulates the background between black and the theme's background color. To achieve
    visually appealing results, the darkest color in your triplet should be assigned as the background. Ideally, it
    should be dark enough to maintain the readability of overlaid elements, yet distinct enough from pure black to
    enhance the hillshading effect.

    In light mode, the approach is similar but uses white as the base, with the lightest color taking the role of the
    background.

    This script takes a list of color triplets as input and generates posters for both light and dark modes,
    helping you identify aesthetic themes. The background color is automatically selected based on brightness,
    while the other two colors are permuted, resulting in 4 unique posters per color triplet.


    Color Palette Inspiration:
    - https://huemint.com/brand-2/
    - https://coolors.co/palettes/popular/3%20colors

    Tune Color:
    - https://mdigi.tools/darken-color/#f1effc
    """
    gpx_data = AugmentedGpxData.from_path(os.path.join(CYCLING_DIR, "marmotte.gpx"))
    cache = PosterImageCache.from_gpx_data(gpx_data, paper=PAPER_SIZES["A4"],  dpi=60)

    shutil.rmtree(COLOR_EXPLORATION_DIR, ignore_errors=True)
    os.makedirs(COLOR_EXPLORATION_DIR, exist_ok=True)

    candidates = generate_color_candidates(color_palettes, dark_mode=False)
    candidates += generate_color_candidates(color_palettes, dark_mode=True)

    fig, ax = plt.subplots()
    for theme in tqdm(candidates):
        res = cache.update_drawing_data(azimuth=0,
                                        theme_colors=theme,
                                        title_txt="Test Color",
                                        uphill_m="",
                                        dist_km="")
        cache.draw(fig, ax, res)

        prefix = "dark_" if theme.dark_mode else "light_"
        basename = f"{theme.background_color}_{theme.track_color}_{theme.peak_color}.png".lower()
        plt.savefig(os.path.join(COLOR_EXPLORATION_DIR, prefix + basename))

    logger.info(f"Candidate posters have been saved inside {os.path.relpath(COLOR_EXPLORATION_DIR)}")


if __name__ == "__main__":
    main([("#eaaa33", "#002642", "#840032"),
          ("#dce0d9", "#fbf6ef", "#ead7c3"),
          ("#0d3b66", "#faf0ca", "#f4d35e"),
          ("#f6f7eb", "#e94f37", "#393e41"),
          ("#ed6a5a", "#f4f1bb", "#9bc1bc"),
          ("#006d77", "#83c5be", "#edf6f9"),
          ("#2b2d42", "#8d99ae", "#edf2f4"),
          ("#fe218b", "#fed700", "#21b0fe"),
          ("#f4f1de", "#e07a5f", "#3d405b"),
          ("#26547c", "#ef476f", "#ffd166"),
          ("#ddfff7", "#93e1d8", "#ffa69e"),
          ("#064789", "#427aa1", "#ebf2fa"),
          ("#9381ff", "#b8b8ff", "#f8f7ff"),
          ("#606c38", "#283618", "#fefae0"),
          ("#1e1e24", "#92140c", "#fff8f0"),
          ("#cb997e", "#ddbea9", "#ffe8d6"),
          ("#edae49", "#d1495b", "#00798c"),
          ("#84ffc9", "#aab2ff", "#eca0ff"),
          ("#0c1618", "#004643", "#faf4d3"),
          ("#540d6e", "#ee4266", "#ffd23f"),
          ("#264653", "#2a9d8f", "#e9c46a"),
          ("#233d4d", "#fe7f2d", "#fcca46"),
          ("#f6511d", "#ffb400", "#00a6ed"),
          ("#fbf5f3", "#e28413", "#000022"),
          ("#003049", "#d62828", "#f77f00"),
          ("#faf3dd", "#c8d5b9", "#8fc0a9"),
          ("#f3b391", "#f6d4ba", "#fefadc"),
          ("#dd6e42", "#e8dab2", "#4f6d7a"),
          ("#ffba49", "#20a39e", "#ef5b5b"),
          ("#f1f7ed", "#243e36", "#7ca982"),
          ("#092327", "#0b5351", "#00a9a5"),
          ("#c9cba3", "#ffe1a8", "#e26d5c"),
          ("#fb8b24", "#d90368", "#820263"),
          ("#102542", "#f87060", "#cdd7d6"),
          ("#fe4a49", "#fed766", "#009fb7"),
          ("#c5f9d7", "#f7d486", "#f27a7d"),
          ("#191716", "#e6af2e", "#e0e2db"),
          ("#386641", "#6a994e", "#a7c957"),
          ("#f1e0c5", "#c9b79c", "#71816d"),
          ("#333333", "#48e5c2", "#fcfaf9"),
          ("#ffbe0b", "#fb5607", "#ff006e"),
          ("#ecc8af", "#e7ad99", "#ce796b"),
          ("#000000", "#fffffc", "#beb7a4"),
          ("#ef767a", "#456990", "#49beaa"),
          ("#d9f0ff", "#a3d5ff", "#83c9f4"),
          ("#ff218c", "#ffd800", "#21b1ff"),
          ("#002642", "#840032", "#e59500"),
          ("#e63946", "#f1faee", "#a8dadc"),
          ("#5bc0eb", "#fde74c", "#9bc53d"),
          ("#efc7c2", "#ffe5d4", "#bfd3c1"),
          ("#f3e9dc", "#c08552", "#5e3023"),
          ("#f18f01", "#048ba8", "#2e4057"),
          ("#156064", "#00c49a", "#f8e16c"),
          ("#f79256", "#fbd1a2", "#7dcfb6"),
          ("#1d2f6f", "#8390fa", "#fac748"),
          ("#cc8b86", "#f9eae1", "#7d4f50"),
          ("#273043", "#9197ae", "#eff6ee"),
          ("#db2b39", "#29335c", "#f3a712"),
          ("#011627", "#fdfffc", "#2ec4b6"),
          ("#022b3a", "#1f7a8c", "#bfdbf7"),
          ("#fcba04", "#a50104", "#590004"),
          ("#fe4a49", "#2ab7ca", "#fed766"),
          ("#f1dede", "#d496a7", "#5d576b"),
          ("#ff6978", "#fffcf9", "#b1ede8"),
          ("#423e37", "#e3b23c", "#edebd7"),
          ("#a31621", "#bfdbf7", "#053c5e"),
          ("#588b8b", "#ffffff", "#ffd5c2"),
          ("#f46036", "#2e294e", "#1b998b"),
          ("#bce784", "#5dd39e", "#348aa7"),
          ("#c9def4", "#f5ccd4", "#b8a4c9"),
          ("#e9d758", "#297373", "#ff8552"),
          ("#cadcfc", "#69a1f7", "#00246b"),
          ("#bfdbf7", "#f87060", "#102542")
          ])
