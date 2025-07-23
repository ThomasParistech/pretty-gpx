#!/usr/bin/python3
"""City Page."""
from dataclasses import dataclass

from pretty_gpx.common.drawing.utils.scatter_point import ScatterPointCategory
from pretty_gpx.rendering_modes.city.data.roads import CityRoadPrecision
from pretty_gpx.rendering_modes.city.drawing.city_colors import CITY_COLOR_THEMES
from pretty_gpx.rendering_modes.city.drawing.city_drawer import CityDrawer
from pretty_gpx.rendering_modes.city.drawing.city_params import CityParams
from pretty_gpx.ui.pages.template.ui_input import UiInputInt
from pretty_gpx.ui.pages.template.ui_manager import UiManager
from pretty_gpx.ui.pages.template.ui_toggle import UiToggle


def city_page() -> None:
    """City Page."""
    CityUiManager()


@dataclass(slots=True)
class CityUiManager(UiManager[CityDrawer]):
    """City Ui Manager."""
    uphill: UiInputInt
    road_max_precision: UiToggle[CityRoadPrecision]

    def __init__(self) -> None:
        drawer = CityDrawer(params=CityParams.default(), top_ratio=0.18, bot_ratio=0.22, margin_ratio=0.1)

        # Dataclass doesn't handle __slots__  correctly and calling super() when slots=True raises an error
        super(CityUiManager, self).__init__(drawer)  # noqa : UP008

        with self.subclass_column:
            self.uphill = UiInputInt.create(label='D+ (m)', value="", on_enter=self.on_click_update,
                                            tooltip="Press Enter to override elevation from GPX")
            self.road_max_precision = UiToggle[CityRoadPrecision].create({p.pretty_name: p
                                                                          for p in CityRoadPrecision.coarse_to_fine()},
                                                                         tooltip="Change the roads level of details",
                                                                         on_change=self.on_click_update,
                                                                         start_key=CityRoadPrecision.MEDIUM.pretty_name)

    @staticmethod
    def get_chat_msg() -> list[str]:
        """Return the chat message, introducing the page."""
        return ['Welcome 😀\nCreate a custom poster from\n'
                'your cycling/running GPX file! 🚵 🥾',
                'Customize your poster below and download\n']

    def update_drawer_params(self) -> None:
        """Update the drawer parameters based on the UI inputs."""
        theme = CITY_COLOR_THEMES[self.theme.value]

        self.drawer.params.track_color = theme.track_color

        self.drawer.params.city_road_max_precision = self.road_max_precision.value
        self.drawer.params.city_background_color = theme.background_color
        self.drawer.params.city_farmland_color = theme.farmland_color
        self.drawer.params.city_rivers_color = theme.rivers_color
        self.drawer.params.city_forests_color = theme.forests_color
        self.drawer.params.city_dark_mode = theme.dark_mode

        self.drawer.params.profile_fill_color = theme.track_color
        self.drawer.params.profile_font_color = theme.background_color
        self.drawer.params.centered_title_font_color = theme.point_color
        self.drawer.params.centered_title_fontproperties = self.font.font.value
        self.drawer.params.centered_title_font_size = self.font._current_fontsize

        for cat in [ScatterPointCategory.CITY_BRIDGE,
                    ScatterPointCategory.CITY_POI_DEFAULT,
                    ScatterPointCategory.CITY_POI_GREAT,
                    ScatterPointCategory.START,
                    ScatterPointCategory.END]:
            self.drawer.params.scatter_params[cat].color = theme.point_color
            self.drawer.params.profile_scatter_params[cat].color = theme.point_color

        self.drawer.params.user_dist_km = self.dist_km.value
        self.drawer.params.user_uphill_m = self.uphill.value
        self.drawer.params.user_title = self.title.value
