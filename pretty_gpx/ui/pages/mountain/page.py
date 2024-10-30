#!/usr/bin/python3
"""Mountain UI."""
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import safe
from pretty_gpx.rendering_modes.mountain.drawing.hillshading import AZIMUTHS
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawer import MountainDrawer
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawer import MountainDrawingData
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawing_cache_data import MountainDrawingCacheData
from pretty_gpx.rendering_modes.mountain.drawing.theme_colors import DARK_COLOR_THEMES
from pretty_gpx.rendering_modes.mountain.drawing.theme_colors import LIGHT_COLOR_THEMES
from pretty_gpx.ui.pages.template.ui_cache import UiCache
from pretty_gpx.ui.pages.template.ui_manager import UiManager
from pretty_gpx.ui.utils.run import on_click_slow_action_in_other_thread


def mountain_page() -> None:
    """Mountain Page."""
    MountainUiManager()


@dataclass
class MountainUiCache(UiCache[MountainDrawingCacheData]):
    """Mountain Ui Cache."""

    @profile_parallel
    def change_paper_size(self, new_paper_size: PaperSize) -> "MountainUiCache":
        """Change the paper size."""
        new_data = MountainDrawingCacheData.from_augmented_gpx_data(self.safe_data.gpx_data, new_paper_size)
        return MountainUiCache(new_data)

    @classmethod
    @profile_parallel
    def process_files(cls, list_b: list[bytes] | list[str], paper_size: PaperSize) -> "MountainUiCache":
        """Process the GPX files."""
        new_data = MountainDrawingCacheData.from_gpx(list_b, paper_size)
        return MountainUiCache(new_data)


@dataclass
class MountainUiManager(UiManager[MountainUiCache]):
    """Mountain Ui Manager."""
    uphill_button: ui.input
    azimuth_toggle: ui.toggle

    def __init__(self, cache: MountainUiCache = MountainUiCache()) -> None:
        super().__init__(cache)

        with self.col_2:
            with ui.input(label='D+ (m)', value="").on('keydown.enter', self.on_click_update()) as self.uphill_button:
                ui.tooltip("Press Enter to override elevation from GPX")

            self.azimuth_toggle = ui.toggle(list(AZIMUTHS.keys()), value=list(AZIMUTHS.keys())[0],
                                            on_change=self.on_click_update())

    @staticmethod
    def get_chat_msg() -> list[str]:
        """Return the chat message."""
        return ['Welcome 😀\nCreate a custom poster from\n'
                'your cycling/hiking GPX file! 🚵 🥾',
                'For multi-day trips, upload all consecutive\n'
                'GPX tracks together.\n'
                '(Make sure filenames are in alphabetical order)',
                'Customize your poster below and download\n'
                'the High-Resolution SVG file when ready.\n'
                '(N.B. the map below is a Low-Resolution preview.)']

    def on_click_update(self) -> Callable[[], Awaitable[None]]:
        """Return an async function that updates the poster with the current settings."""
        return on_click_slow_action_in_other_thread('Updating', self.update_low_res, self.update_done_callback_low_res)

    async def cb_before_download(self) -> None:
        """Callback before downloading."""
        dpi = self.high_res_cache.dpi
        await on_click_slow_action_in_other_thread(f'Rendering at High Resolution ({dpi} dpi)',
                                                   self.update_high_res, self.update_done_callback_high_res)()

    ####

    @property
    def high_res_cache(self) -> MountainDrawer:
        """Return the high resolution Poster cache."""
        return self.cache.safe_data.high_res

    @property
    def low_res_cache(self) -> MountainDrawer:
        """Return the low resolution Poster cache."""
        return self.cache.safe_data.low_res

    @profile_parallel
    def update_low_res(self) -> MountainDrawingData:
        """Update the MountainDrawingData with the current settings, at the low resolution."""
        return self._update(self.low_res_cache)

    @profile_parallel
    def update_high_res(self) -> MountainDrawingData:
        """Update the MountainDrawingData with the current settings, at the high resolution."""
        return self._update(self.high_res_cache)

    @profile
    def update_done_callback_low_res(self, poster_drawing_data: MountainDrawingData) -> None:
        """Update the plot with the low resolution MountainDrawingData."""
        self._update_done_callback(self.low_res_cache, poster_drawing_data)

    @profile
    def update_done_callback_high_res(self, poster_drawing_data: MountainDrawingData) -> None:
        """Update the plot with the high resolution MountainDrawingData."""
        self._update_done_callback(self.high_res_cache, poster_drawing_data)

    def _update(self, c: MountainDrawer) -> MountainDrawingData:
        """Asynchronously update the MountainDrawingData with the current settings."""
        dark_mode = bool(safe(self.dark_mode_switch.value))

        color_themes = (DARK_COLOR_THEMES if dark_mode else LIGHT_COLOR_THEMES)
        return c.update_drawing_data(azimuth=AZIMUTHS[safe(self.azimuth_toggle.value)],
                                     theme_colors=color_themes[safe(self.theme_toggle.value)],
                                     title_txt=self.title_button.value,
                                     uphill_m=self.uphill_button.value,
                                     dist_km=self.dist_km_button.value)

    def _update_done_callback(self, c: MountainDrawer,
                              poster_drawing_data: MountainDrawingData) -> None:
        """Synchronously update the plot with the MountainDrawingData.

        (Matplotlib must run in the main thread).
        """
        with Profiling.Scope("Pyplot Context"), self.plot.plot:
            c.draw(self.plot.fig, self.plot.ax, poster_drawing_data)
        self.plot.update()
