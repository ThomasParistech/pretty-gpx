#!/usr/bin/python3
"""City UI."""

from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass

from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.rendering_modes.city.drawing.city_colors import CITY_COLOR_THEMES
from pretty_gpx.rendering_modes.city.drawing.city_drawer import CityDrawingData
from pretty_gpx.rendering_modes.city.drawing.city_drawing_cache_data import CityDrawingCacheData
from pretty_gpx.ui.pages.template.elements.ui_input import UiInputInt
from pretty_gpx.ui.pages.template.ui_cache import UiCache
from pretty_gpx.ui.pages.template.ui_manager import UiManager
from pretty_gpx.ui.utils.run import on_click_slow_action_in_other_thread


def city_page() -> None:
    """City Page."""
    CityUiManager()


@dataclass
class CityUiCache(UiCache[CityDrawingCacheData]):
    """City Ui Cache."""

    @profile_parallel
    def change_paper_size(self, new_paper_size: PaperSize) -> "CityUiCache":
        """Change the paper size."""
        new_data = CityDrawingCacheData.from_augmented_gpx_data(self.safe_data.gpx_data, new_paper_size)
        return CityUiCache(new_data)

    @classmethod
    @profile_parallel
    def process_file(cls, b: bytes | str, paper_size: PaperSize) -> "CityUiCache":
        """Process the GPX file."""
        new_data = CityDrawingCacheData.from_gpx(b, paper_size)
        return CityUiCache(new_data)


@dataclass(slots=True)
class CityUiManager(UiManager[CityUiCache]):
    """City Ui Manager."""
    uphill: UiInputInt
    duration_s: UiInputInt

    def __init__(self, cache: CityUiCache = CityUiCache()) -> None:
        # Dataclass doesn't handle __slots__  correctly and calling super() when slots=True raises an error
        super(CityUiManager, self).__init__(cache)  # noqa : UP008

        with self.subclass_column:
            self.uphill = UiInputInt.create(label='D+ (m)', value="", on_enter=self.on_click_update(),
                                            tooltip="Press Enter to override elevation from GPX",)
            self.duration_s = UiInputInt.create(label='Duration (s)', value="", on_enter=self.on_click_update(),
                                                tooltip="Press Enter to override duration from GPX",)

    @staticmethod
    def get_chat_msg() -> list[str]:
        """Return the chat message."""
        return ['Welcome 😀\nCreate a custom poster from\n'
                'your cycling/running GPX file! 🚵 🥾',
                'Customize your poster below and download\n']

    def on_click_update(self) -> Callable[[], Awaitable[None]]:
        """Return an async function that updates the poster with the current settings."""
        return on_click_slow_action_in_other_thread('Updating', self.update, self.update_done_callback)

    ####

    @property
    def city_cache(self) -> CityDrawingCacheData:
        """Return the Poster cache."""
        return self.cache.safe_data

    @profile_parallel
    def update(self) -> CityDrawingData:
        """Update the CityDrawingData with the current settings."""
        colors = CITY_COLOR_THEMES[self.theme.value]
        return self.city_cache.drawer.update_drawing_data(colors=colors,
                                                          title_txt=self.title.value,
                                                          uphill_m=self.uphill.value,
                                                          dist_km=self.dist_km.value,
                                                          duration_s=self.duration_s.value)

    @profile
    def update_done_callback(self, poster_drawing_data: CityDrawingData) -> None:
        """Synchronously update the plot with the CityDrawingData.

        (Matplotlib must run in the main thread).
        """
        with Profiling.Scope("Pyplot Context"), self.plot.plot:
            self.city_cache.drawer.draw(self.plot.fig, self.plot.ax, poster_drawing_data)
        self.plot.update()
