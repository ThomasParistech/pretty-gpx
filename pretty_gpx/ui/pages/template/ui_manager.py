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

from pretty_gpx.common.drawing.color_theme import DarkTheme
from pretty_gpx.common.drawing.color_theme import LightTheme
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.ui.pages.template.elements.ui_input import UiInputInt
from pretty_gpx.ui.pages.template.elements.ui_input import UiInputStr
from pretty_gpx.ui.pages.template.elements.ui_toggle import UiToggle
from pretty_gpx.ui.pages.template.ui_cache import UiCache
from pretty_gpx.ui.pages.template.ui_plot import HIGH_RES_DPI
from pretty_gpx.ui.pages.template.ui_plot import UiPlot
from pretty_gpx.ui.utils.run import on_click_slow_action_in_other_thread
from pretty_gpx.ui.utils.style import DARK_MODE_TEXT
from pretty_gpx.ui.utils.style import LIGHT_MODE_TEXT

T = TypeVar('T', bound=UiCache)


@dataclass(slots=True)
class UiManager(Generic[T]):
    """Ui Manager.

    The UiManager is a template class that manages the layout of the page.

    At initialization, when the cache is not initialized, the layout is partially hidden and looks like this:

        ┌──────┐
        │ Chat │
        └──────┘
        ┌──────┐
        │Upload│
        └──────┘
      ┌──────────┐
      │Paper Size│
      └──────────┘

    When the cache is initialized, the layout is fully displayed:

                            ┌──────┐
    ┌─────────────────┐     │ Chat │
    │                 │     └──────┘
    │                 │     ┌──────┐
    │                 │     │Upload│
    │                 │     └──────┘
    │                 │   ┌──────────┐
    │                 │   │Paper Size│
    │                 │   └──────────┘
    │                 │  ┌────────────┐
    │      Plot       │  │   Title    │
    │                 │  │  Distance  │
    │                 │  │            │
    │                 │  │    ...     │
    │                 │  │            │
    │                 │  │  Dark Mode │
    │                 │  │Theme Colors│
    │                 │  └────────────┘
    │                 │    ┌────────┐
    │                 │    │Download│
    └─────────────────┘    └────────┘

    The "..." represents the fields that the subclass can add to the layout, using the `subclass_column` context.

    Subclasses must implement:
    - `get_chat_msg`: Return the chat message, introducing the page.
    - `on_click_update`: Return an async function that updates the poster with the current settings.
    - `cb_before_download`: Optional callback to run before downloading the poster. If not implemented, it does nothing.

    The template cache type `T` must implement:
    - `on_multi_upload_events` or `on_single_upload_events`
    - `on_paper_size_change`
    """
    cache: T

    plot: UiPlot
    subclass_column: ui.column
    params_to_hide: ui.column

    paper_size: UiToggle[PaperSize]
    title: UiInputStr
    dist_km: UiInputInt
    dark_mode_switch: ui.switch
    theme: UiToggle[DarkTheme] | UiToggle[LightTheme]

    hidden: bool

    def __init__(self, cache: T) -> None:
        """When subclassing, add elements inside `subclass_column`."""
        self.cache = cache

        with ui.row().style("height: 100vh; width: 100%; justify-content: center; align-items: center; gap: 20px;"):
            self.plot = UiPlot(visible=False)

            with ui.column(align_items="center"):
                col_1 = ui.column(align_items="center")

                with ui.column(align_items="center") as self.params_to_hide:
                    with ui.card():
                        self.subclass_column = ui.column(align_items="center")
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
            self.paper_size = UiToggle[PaperSize].create(PAPER_SIZES, on_change=self.on_paper_size_change)

        with self.subclass_column:
            self.title = UiInputStr.create(label='Title', value="Title", tooltip="Press Enter to update title",
                                           on_enter=self.on_click_update())
            self.dist_km = UiInputInt.create(label='Distance (km)', value="", on_enter=self.on_click_update(),
                                             tooltip="Press Enter to override distance from GPX")

            #
            # New fields will be added here by the subclass
            #

        with col_3:
            # Colors
            # TODO(upgrade): Use same Theme colors for the different rendering modes
            self.dark_mode_switch = ui.switch(DARK_MODE_TEXT, value=True, on_change=self.on_dark_mode_switch_change)

            self.theme = UiToggle[DarkTheme].create(DarkTheme.get_mapping(), on_change=self.on_click_update())

        #######

        self.hidden = True

        if self.cache.is_initialized():
            self.make_visible()

    async def on_multi_upload_events(self, e: events.MultiUploadEventArguments) -> None:
        """Sort the uploaded files by name and process them."""
        res = await self.cache.on_multi_upload_events(e, self.paper_size.value)
        await self.update_cache_if_sucessful(res)

    async def on_single_upload_events(self, e: events.UploadEventArguments) -> None:
        """Process the uploaded file."""
        res = await self.cache.on_single_upload_events(e, self.paper_size.value)
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
            self.cache = await self.cache.on_paper_size_change(self.paper_size.value)
            await self.on_click_update()()

    def on_dark_mode_switch_change(self, e: events.ValueChangeEventArguments) -> None:
        """Switch between dark and light mode."""
        dark_mode = e.value
        self.dark_mode_switch.text = DARK_MODE_TEXT if dark_mode else LIGHT_MODE_TEXT

        if dark_mode:
            self.theme = self.theme.change(DarkTheme.get_mapping())
        else:
            self.theme = self.theme.change(LightTheme.get_mapping())

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
        basename = "poster"
        title = self.title.value
        if title:
            basename += f"_{sanitize_filename(title.replace(' ', '_'))}"
        ui.download(svg_bytes, f'{basename}.svg')
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
