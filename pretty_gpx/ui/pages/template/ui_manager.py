#!/usr/bin/python3
"""Ui Manager."""
import os
import tempfile
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

from nicegui import events
from nicegui import ui
from pathvalidate import sanitize_filename

from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import safe
from pretty_gpx.rendering_modes.mountain.drawing.theme_colors import DARK_COLOR_THEMES
from pretty_gpx.rendering_modes.mountain.drawing.theme_colors import LIGHT_COLOR_THEMES
from pretty_gpx.ui.pages.template.ui_cache import UiCache
from pretty_gpx.ui.pages.template.ui_plot import HIGH_RES_DPI
from pretty_gpx.ui.pages.template.ui_plot import UiPlot
from pretty_gpx.ui.utils.run import on_click_slow_action_in_other_thread
from pretty_gpx.ui.utils.style import DARK_MODE_TEXT
from pretty_gpx.ui.utils.style import LIGHT_MODE_TEXT

T = TypeVar('T', bound=UiCache)


@dataclass
class UiManager(Generic[T]):
    """Ui Manager."""
    cache: T

    plot: UiPlot
    col_2: ui.column
    params_to_hide: ui.column

    paper_size_toggle: ui.toggle
    title_button: ui.input
    dist_km_button: ui.input
    dark_mode_switch: ui.switch
    theme_toggle: ui.toggle

    hidden: bool

    def __init__(self, cache: T) -> None:
        """When subclassing, add elements inside col_2."""
        self.cache = cache

        with ui.row().style("height: 100vh; width: 100%; justify-content: center; align-items: center; gap: 20px;"):
            self.plot = UiPlot(visible=False)

            with ui.column(align_items="center"):
                col_1 = ui.column(align_items="center")

                with ui.column(align_items="center") as self.params_to_hide:
                    with ui.card():
                        self.col_2 = ui.column(align_items="center")
                        col_3 = ui.column(align_items="center")

                    ui.button('Download', on_click=self.on_click_download)
                self.params_to_hide.visible = False

        ###

        with col_1:
            # Chat
            ui.chat_message(self.get_chat_msg()).props('bg-color=blue-2')

            # Upload
            multi_upload = self.cache.multi()
            if multi_upload:
                label = "Drag & drop your GPX file(s) here and press upload"
            else:
                label = "Drag & drop your GPX file here and press upload"

            ui.upload(label=label,
                      multiple=multi_upload,
                      on_upload=None if multi_upload else self.on_single_upload_events,
                      on_multi_upload=self.on_multi_upload_events if multi_upload else None,
                      ).props('accept=.gpx').on('rejected',
                                                lambda: ui.notify('Please provide a GPX file')).classes('max-w-full')
            # Paper Size
            self.paper_size_toggle = ui.toggle(list(PAPER_SIZES.keys()), value=list(PAPER_SIZES.keys())[0],
                                               on_change=self.on_paper_size_change)

        with self.col_2:
            with ui.input(label='Title',
                          value="Title").on('keydown.enter', self.on_click_update()) as self.title_button:
                ui.tooltip("Press Enter to update title")

            with ui.input(label='Distance (km)',
                          value="").on('keydown.enter', self.on_click_update()) as self.dist_km_button:
                ui.tooltip("Press Enter to override distance from GPX")

            #
            # New fields will be added here by the subclass
            #

        with col_3:
            # Colors
            # TODO(upgrade): Use same Theme colors for the different rendering modes
            self.dark_mode_switch = ui.switch(DARK_MODE_TEXT, value=True, on_change=self.on_dark_mode_switch_change)
            self.theme_toggle = ui.toggle(list(DARK_COLOR_THEMES.keys()), value=list(DARK_COLOR_THEMES.keys())[0],
                                          on_change=self.on_click_update())

        #######

        self.hidden = True

        if self.cache.is_initialized():
            self.make_visible()

    @property
    def paper_size_name(self) -> str:
        """Get the current paper size name."""
        return str(safe(self.paper_size_toggle.value))

    @property
    def paper_size(self) -> PaperSize:
        """Get the current paper size."""
        return PAPER_SIZES[self.paper_size_name]

    @property
    def title(self) -> str:
        """Get the current title."""
        return str(safe(self.title_button.value))

    @property
    def dist_km(self) -> str:
        """Get the current dist."""
        return str(safe(self.dist_km_button.value))

    async def on_multi_upload_events(self, e: events.MultiUploadEventArguments) -> None:
        """Sort the uploaded files by name and process them."""
        res = await self.cache.on_multi_upload_events(e, self.paper_size)
        await self.update_cache_if_sucessful(res)

    async def on_single_upload_events(self, e: events.UploadEventArguments) -> None:
        """Process the uploaded file."""
        res = await self.cache.on_single_upload_events(e, self.paper_size)
        await self.update_cache_if_sucessful(res)

    async def update_cache_if_sucessful(self, new_cache: T | None) -> None:
        """Update the cache if successful."""
        if new_cache is None:
            return
        self.cache = new_cache
        await self.on_click_update()()
        if self.hidden:
            self.make_visible()

    def make_visible(self) -> None:
        """Make the layout visible."""
        self.hidden = False
        self.plot.make_visible()
        self.params_to_hide.visible = True

    async def on_paper_size_change(self) -> None:
        """Change the paper size and update the poster."""
        if self.cache.is_initialized():
            self.cache = await self.cache.on_paper_size_change(self.paper_size)
            await self.on_click_update()()

    def on_dark_mode_switch_change(self, e: events.ValueChangeEventArguments) -> None:
        """Switch between dark and light mode."""
        dark_mode = e.value
        self.dark_mode_switch.text = DARK_MODE_TEXT if dark_mode else LIGHT_MODE_TEXT
        self.theme_toggle.options = list(DARK_COLOR_THEMES.keys()) if dark_mode else list(LIGHT_COLOR_THEMES.keys())
        self.theme_toggle.value = self.theme_toggle.options[0]
        self.theme_toggle.update()

    @profile_parallel
    def download(self) -> bytes:
        """Save the poster as SVG and return the bytes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with Profiling.Scope("Matplotlib Save SVG"):
                tmp_svg = os.path.join(tmp_dir, "tmp.svg")
                self.plot.fig.savefig(tmp_svg, dpi=HIGH_RES_DPI)
            with open(tmp_svg, "rb") as svg_file:
                return svg_file.read()

    def download_done_callback(self, svg_bytes: bytes) -> None:
        """Download the SVG file."""
        ui.download(svg_bytes, f'poster_{sanitize_filename(self.title.replace(" ", "_"))}.svg')
        logger.info("Poster Downloaded")

    async def on_click_download(self) -> None:
        """Asynchronously render the high resolution poster and download it as SVG."""
        await self.cb_before_download()
        await on_click_slow_action_in_other_thread('Exporting SVG', self.download, self.download_done_callback)()

    ####

    @staticmethod
    def get_chat_msg() -> list[str]:
        """Return the chat message."""
        raise NotImplementedError

    def on_click_update(self) -> Callable[[], Awaitable[None]]:
        """Return an async function that updates the poster with the current settings."""
        raise NotImplementedError

    async def cb_before_download(self) -> None:
        """Callback before downloading."""
        pass
