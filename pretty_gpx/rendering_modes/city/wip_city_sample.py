#!/usr/bin/python3
"""Work in progress. Generate a poster from a urban marathon GPX track."""
import os

import matplotlib.pyplot as plt

from pretty_gpx.common.gpx.gpx_track import GpxTrack
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.paths import RUNNING_DIR
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.rendering_modes.city.city_poster_image_cache import CityPosterImageCache
from pretty_gpx.rendering_modes.city.drawing.theme_colors import DARK_COLOR_THEMES
from pretty_gpx.rendering_modes.city.drawing.theme_colors import LIGHT_COLOR_THEMES

if __name__ == "__main__":
    gpx_track = GpxTrack.load(os.path.join(RUNNING_DIR, "route_4_chateaux.gpx"))
    for theme in list(DARK_COLOR_THEMES.values())[:1]+list(LIGHT_COLOR_THEMES.values())[:1]:

        fig, ax = plt.subplots(figsize=(10, 10))
        paper = PAPER_SIZES['A4']

        poster = CityPosterImageCache.from_gpx([os.path.join(RUNNING_DIR, "marathon_paris.gpx")], paper_size=paper)

        poster_data, update = poster.update_drawing_data(theme_colors=theme,
                                                         title_txt="Marathon de Paris",
                                                         uphill_m="250",
                                                         duration_s="10800",
                                                         dist_km="42.195")
        if update is True:
            logger.info("An update of the plotter is done")
            poster = CityPosterImageCache.from_gpx_data(poster.gpx_data, paper_size=paper, force_two_line=update)


        poster.draw(fig, ax, poster_data)

        plt.show()

    Profiling.export_events()
