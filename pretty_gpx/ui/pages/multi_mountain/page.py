#!/usr/bin/python3
"""Multi Mountain Page."""
from dataclasses import dataclass

from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.rendering_modes.mountain.drawing.hillshading import AZIMUTHS
from pretty_gpx.rendering_modes.mountain.drawing.mountain_colors import MOUNTAIN_COLOR_THEMES
from pretty_gpx.rendering_modes.multi_mountain.drawing.multi_mountain_drawer import MultiMountainDrawer
from pretty_gpx.rendering_modes.multi_mountain.drawing.multi_mountain_params import MultiMountainParams
from pretty_gpx.ui.pages.template.ui_input import UiInputInt
from pretty_gpx.ui.pages.template.ui_manager import UiManager
from pretty_gpx.ui.pages.template.ui_toggle import UiToggle


def multi_mountain_page() -> None:
    """Multi Mountain Page."""
    MultiMountainUiManager()


@dataclass(slots=True)
class MultiMountainUiManager(UiManager[MultiMountainDrawer]):
    """Mountain Ui Manager."""
    uphill: UiInputInt
    azimuth: UiToggle[int]

    def __init__(self) -> None:
        drawer = MultiMountainDrawer(params=MultiMountainParams.default(),
                                     top_ratio=0.18, bot_ratio=0.22, margin_ratio=0.1)

        # Dataclass doesn't handle __slots__  correctly and calling super() when slots=True raises an error
        super(MultiMountainUiManager, self).__init__(drawer)  # noqa : UP008

        with self.subclass_column:
            self.uphill = UiInputInt.create(label='D+ (m)', value="", on_enter=self.on_click_update,
                                            tooltip="Press Enter to override elevation from GPX")
            self.azimuth = UiToggle[int].create(mapping=AZIMUTHS, on_change=self.on_click_update)

    @staticmethod
    def get_chat_msg() -> list[str]:
        """Return the chat message, introducing the page."""
        return ['Welcome 😀\nCreate a custom poster from\n'
                'your hiking GPX file! 🚵 🥾',
                'For multi-day trips, upload all consecutive\n'
                'GPX tracks together.\n'
                '(Make sure filenames are in alphabetical order)',
                'Customize your poster below and download\n'
                'the High-Resolution SVG file when ready.\n'
                '(N.B. the map below is a Low-Resolution preview.)']

    def update_drawer_params(self) -> None:
        """Update the drawer parameters based on the UI inputs."""
        theme = MOUNTAIN_COLOR_THEMES[self.theme.value]

        self.drawer.params.track_color = theme.track_color
        self.drawer.params.mountain_background_color = theme.background_color
        self.drawer.params.mountain_dark_mode = theme.dark_mode
        self.drawer.params.mountain_azimuth = self.azimuth.value
        self.drawer.params.profile_fill_color = theme.track_color
        self.drawer.params.profile_font_color = theme.background_color
        self.drawer.params.centered_title_font_color = theme.peak_color

        for cat in [ScatterPointCategory.MOUNTAIN_HUT,
                    ScatterPointCategory.START,
                    ScatterPointCategory.END]:
            self.drawer.params.scatter_params[cat].color = theme.peak_color
            self.drawer.params.profile_scatter_params[cat].color = theme.peak_color

        self.drawer.params.user_dist_km = self.dist_km.value
        self.drawer.params.user_uphill_m = self.uphill.value
        self.drawer.params.user_title = self.title.value
