#!/usr/bin/python3
"""City UI."""

from dataclasses import dataclass

from pretty_gpx.rendering_modes.city.drawing.city_colors import CITY_COLOR_THEMES
from pretty_gpx.rendering_modes.city.drawing.city_drawer import CityDrawer
from pretty_gpx.rendering_modes.city.drawing.city_drawer import CityDrawingInputs
from pretty_gpx.ui.pages.template.elements.ui_input import UiInputInt
from pretty_gpx.ui.pages.template.ui_cache import UiCache
from pretty_gpx.ui.pages.template.ui_manager import UiManager


def city_page() -> None:
    """City Page."""
    CityUiManager()


@dataclass
class CityUiCache(UiCache[CityDrawer]):
    """City Ui Cache."""

    @staticmethod
    def get_drawer_cls() -> type[CityDrawer]:
        """Return the template Drawer class (Because Python doesn't allow to use T as a type)."""
        return CityDrawer


@dataclass(slots=True)
class CityUiManager(UiManager[CityUiCache]):
    """City Ui Manager."""
    uphill: UiInputInt
    duration_s: UiInputInt

    def __init__(self, cache: CityUiCache = CityUiCache()) -> None:
        # Dataclass doesn't handle __slots__  correctly and calling super() when slots=True raises an error
        super(CityUiManager, self).__init__(cache)  # noqa : UP008

        with self.subclass_column:
            self.uphill = UiInputInt.create(label='D+ (m)', value="", on_enter=self.on_click_update,
                                            tooltip="Press Enter to override elevation from GPX",)
            self.duration_s = UiInputInt.create(label='Duration (s)', value="", on_enter=self.on_click_update,
                                                tooltip="Press Enter to override duration from GPX",)

    @staticmethod
    def get_chat_msg() -> list[str]:
        """Return the chat message."""
        return ['Welcome 😀\nCreate a custom poster from\n'
                'your cycling/running GPX file! 🚵 🥾',
                'Customize your poster below and download\n']

    async def on_click_update(self) -> None:
        """Asynchronously update the UiPlot."""
        await self.plot.update_preview(self.cache.safe_drawer.draw, self.get_inputs())

    async def render_download_svg_bytes(self) -> bytes:
        """Asynchronously download bytes of SVG image using UiPlot."""
        return await self.plot.render_svg(self.cache.safe_drawer.draw, self.get_inputs())

    def get_inputs(self) -> CityDrawingInputs:
        """Return the inputs."""
        colors = CITY_COLOR_THEMES[self.theme.value]
        return CityDrawingInputs(theme_colors=colors,
                                 title_txt=self.title.value,
                                 uphill_m=self.uphill.value,
                                 dist_km=self.dist_km.value,
                                 duration_s=self.duration_s.value)
