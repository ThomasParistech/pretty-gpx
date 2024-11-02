#!/usr/bin/python3
"""Mountain UI."""
from dataclasses import dataclass

from pretty_gpx.rendering_modes.mountain.drawing.hillshading import AZIMUTHS
from pretty_gpx.rendering_modes.mountain.drawing.mountain_colors import MOUNTAIN_COLOR_THEMES
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawer import MountainDrawer
from pretty_gpx.rendering_modes.mountain.drawing.mountain_drawer import MountainDrawingInputs
from pretty_gpx.ui.pages.template.elements.ui_input import UiInputInt
from pretty_gpx.ui.pages.template.elements.ui_toggle import UiToggle
from pretty_gpx.ui.pages.template.ui_cache import UiCache
from pretty_gpx.ui.pages.template.ui_manager import UiManager


def mountain_page() -> None:
    """Mountain Page."""
    MountainUiManager()


@dataclass
class MountainUiCache(UiCache[MountainDrawer]):
    """Mountain Ui Cache."""

    @staticmethod
    def get_drawer_cls() -> type[MountainDrawer]:
        """Return the template Drawer class (Because Python doesn't allow to use T as a type)."""
        return MountainDrawer


@dataclass(slots=True)
class MountainUiManager(UiManager[MountainUiCache]):
    """Mountain Ui Manager."""
    uphill: UiInputInt
    azimuth: UiToggle[int]

    def __init__(self, cache: MountainUiCache = MountainUiCache()) -> None:
        # Dataclass doesn't handle __slots__  correctly and calling super() when slots=True raises an error
        super(MountainUiManager, self).__init__(cache)  # noqa : UP008

        with self.subclass_column:
            self.uphill = UiInputInt.create(label='D+ (m)', value="", on_enter=self.on_click_update,
                                            tooltip="Press Enter to override elevation from GPX",)
            self.azimuth = UiToggle[int].create(mapping=AZIMUTHS, on_change=self.on_click_update)

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

    async def on_click_update(self) -> None:
        """Asynchronously update the UiPlot."""
        await self.plot.update_preview(self.cache.safe_drawer.draw, self.get_inputs(high_res=False))

    async def render_download_svg_bytes(self) -> bytes:
        """Asynchronously download bytes of SVG image using UiPlot."""
        return await self.plot.render_svg(self.cache.safe_drawer.draw, self.get_inputs(high_res=True))

    def get_inputs(self, high_res: bool) -> MountainDrawingInputs:
        """Return the inputs."""
        colors = MOUNTAIN_COLOR_THEMES[self.theme.value]
        return MountainDrawingInputs(high_res=high_res,
                                     azimuth=self.azimuth.value,
                                     colors=colors,
                                     title_txt=self.title.value,
                                     uphill_m=self.uphill.value,
                                     dist_km=self.dist_km.value)
