#!/usr/bin/python3
"""UI Manager."""
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import cast
from typing import Generic
from typing import Literal
from typing import TypeVar

from natsort import index_natsorted
from nicegui import events
from nicegui import ui
from nicegui.elements.upload import Upload
from pathvalidate import sanitize_filename

from pretty_gpx.common.drawing.utils.color_theme import DarkTheme
from pretty_gpx.common.drawing.utils.color_theme import LightTheme
from pretty_gpx.common.drawing.utils.drawer import DrawerMultiTrack
from pretty_gpx.common.drawing.utils.drawer import DrawerSingleTrack
from pretty_gpx.common.drawing.utils.fonts import CustomFont
from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.ui.pages.template.ui_fonts_menu import UiFontsMenu
from pretty_gpx.ui.pages.template.ui_input import UiInputFloat
from pretty_gpx.ui.pages.template.ui_input import UiInputStr
from pretty_gpx.ui.pages.template.ui_plot import UiPlot
from pretty_gpx.ui.pages.template.ui_toggle import UiToggle
from pretty_gpx.ui.utils.run import run_cpu_bound
from pretty_gpx.ui.utils.run import run_cpu_bound_safe
from pretty_gpx.ui.utils.style import DARK_MODE_TEXT
from pretty_gpx.ui.utils.style import LIGHT_MODE_TEXT

T = TypeVar('T', bound=DrawerSingleTrack | DrawerMultiTrack)


@profile_parallel
def _self_change_gpx_multi(drawer: T, b: list[bytes] | list[str], paper: PaperSize) -> T:
    """Process the GPX files and return the new drawer."""
    # This function is designed for parallel execution and will be pickled.
    # Defining it as a global function avoids pickling the entire UiManager class,
    # which contains non-picklable elements like local lambdas and UI components.
    assert isinstance(drawer, DrawerMultiTrack)
    drawer.change_gpx(b, paper)
    return cast(T, drawer)


@profile_parallel
def _self_change_gpx_single(drawer: T, b: bytes | str, paper: PaperSize) -> T:
    """Process the GPX file and return the new drawer."""
    # This function is designed for parallel execution and will be pickled.
    # Defining it as a global function avoids pickling the entire UiManager class,
    # which contains non-picklable elements like local lambdas and UI components.
    assert isinstance(drawer, DrawerSingleTrack)
    drawer.change_gpx(b, paper)
    return cast(T, drawer)


@profile_parallel
def _self_change_paper_size(drawer: T, paper: PaperSize) -> T:
    """Change the paper size and return the new drawer."""
    # This function is designed for parallel execution and will be pickled.
    # Defining it as a global function avoids pickling the entire UiManager class,
    # which contains non-picklable elements like local lambdas and UI components.
    drawer.change_papersize(paper)
    return drawer


@dataclass(slots=True)
class UiManager(Generic[T], ABC):
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
    - `update_drawer_params`: Update the drawer parameters based on the UI inputs.
    """
    drawer: T

    plot: UiPlot
    permanent_column: ui.column
    subclass_column: ui.column
    params_to_hide: ui.column

    paper_size: UiToggle[PaperSize]
    title: UiInputStr
    dist_km: UiInputFloat
    font: UiFontsMenu
    dark_mode_switch: ui.switch
    theme: UiToggle[DarkTheme] | UiToggle[LightTheme]

    hidden: bool

    ##########################
    # Abstract Methods

    @staticmethod
    @abstractmethod
    def get_chat_msg() -> list[str]:
        """Return the chat message, introducing the page."""
        ...

    @abstractmethod
    def update_drawer_params(self) -> None:
        """Update the drawer parameters based on the UI inputs."""
        ...

    ##########################
    # Initialization

    def __init__(self, drawer: T) -> None:
        """When subclassing, add elements inside `subclass_column`."""
        self.drawer = drawer

        with ui.row().style("height: 100vh; width: 100%; justify-content: center; align-items: center; gap: 20px;"):
            self.plot = UiPlot(visible=False)

            with ui.column(align_items="center"):
                self.permanent_column = ui.column(align_items="center")

                with ui.column(align_items="center") as self.params_to_hide:
                    with ui.card():
                        self.subclass_column = ui.column(align_items="center")
                        col_3 = ui.column(align_items="center")

                    with ui.row(align_items="center"):
                        ui.button('Download SVG', on_click=self.on_click_download_svg)
                        ui.button('Download PDF', on_click=self.on_click_download_pdf)
                self.params_to_hide.visible = False

        ###

        with self.permanent_column:
            # Chat
            ui.chat_message(self.get_chat_msg()).props('bg-color=blue-2')

            # Upload
            if isinstance(self.drawer, DrawerMultiTrack):
                label = "Drag & drop your GPX files here and press upload"
                multiple = True
                on_upload = None
                on_multi_upload = self.on_multi_upload_events
            elif isinstance(self.drawer, DrawerSingleTrack):
                label = "Drag & drop your GPX file here and press upload"
                multiple = False
                on_upload = self.on_single_upload_events
                on_multi_upload = None
            else:
                raise NotImplementedError

            ui.upload(label=label,
                      multiple=multiple,
                      on_upload=on_upload,
                      on_multi_upload=on_multi_upload,
                      ).props('accept=.gpx').on('rejected',
                                                lambda: ui.notify('Please provide a GPX file', type='negative')
                                                ).classes('max-w-full')
            # Paper Size
            self.paper_size = UiToggle[PaperSize].create(PAPER_SIZES,
                                                         tooltip="Select the paper size",
                                                         on_change=self.on_paper_size_change)

            #
            # New permanent fields will be added here by the subclass
            #

        with self.subclass_column:
            self.title = UiInputStr.create(label='Title', value="Title", tooltip="Press Enter to update title",
                                           on_enter=self.on_click_update)
            self.dist_km = UiInputFloat.create(label='Distance (km)', value="", on_enter=self.on_click_update,
                                               tooltip="Press Enter to override distance from GPX")
            self.font = UiFontsMenu.create(fonts=(CustomFont.LOBSTER,
                                                  CustomFont.MONOTON,
                                                  CustomFont.GOCHI_HAND,
                                                  CustomFont.EMILIO_20,
                                                  CustomFont.ALLERTA_STENCIL),
                                           on_change=self.on_click_update,
                                           tooltip="Select the title's font")

            #
            # New fields will be added here by the subclass
            #

        with col_3:
            # Colors
            # TODO(upgrade): Use same Theme colors for the different rendering modes
            self.dark_mode_switch = ui.switch(DARK_MODE_TEXT, value=True, on_change=self.on_dark_mode_switch_change)

            self.theme = UiToggle[DarkTheme].create(DarkTheme.get_mapping(),
                                                    tooltip="Select the color theme",
                                                    on_change=self.on_click_update)

        #######

        self.hidden = True

    ##########################
    # Single/Multi Upload Events

    async def on_multi_upload_events(self, e: events.MultiUploadEventArguments) -> None:
        """Sort the uploaded files by name and process them."""
        sorted_indices = index_natsorted(e.names)
        names = [e.names[i] for i in sorted_indices]
        contents = [e.contents[i].read() for i in sorted_indices]
        assert isinstance(e.sender, Upload)
        e.sender.reset()

        if len(contents) == 1:
            res = None
            ui.notify('Please upload at least two GPX files', type='negative')
        else:
            name = f'a {len(names)}-days track ({", ".join(names)})'
            res = await run_cpu_bound(f"Download Data for {name}", _self_change_gpx_multi, self.drawer, contents,
                                      self.paper_size.value)

        await self.update_drawer_if_sucessful(res)

    async def on_single_upload_events(self, e: events.UploadEventArguments) -> None:
        """Process the uploaded file."""
        name = e.name
        content = e.content.read()
        assert isinstance(e.sender, Upload)
        e.sender.reset()

        res = await run_cpu_bound(f"Download Data for {name}", _self_change_gpx_single,  self.drawer, content,
                                  self.paper_size.value)
        await self.update_drawer_if_sucessful(res)

    async def update_drawer_if_sucessful(self, new_drawer: T | None) -> None:
        """Update the drawer if successful."""
        if new_drawer is None:
            return
        self.drawer = new_drawer
        await self.on_click_update()
        if self.hidden:
            self.make_visible()

    def make_visible(self) -> None:
        """Make the layout visible."""
        self.hidden = False
        self.plot.make_visible()
        self.params_to_hide.visible = True

    ##########################
    # Paper Size Event

    async def on_paper_size_change(self) -> None:
        """Change the paper size and update the poster."""
        if not self.hidden:
            new_paper = self.paper_size.value
            self.drawer = await run_cpu_bound_safe(f"Switching to {new_paper.name} Poster",
                                                   _self_change_paper_size, self.drawer, new_paper)
            await self.on_click_update()

    ##########################
    # Dark Mode Event

    def on_dark_mode_switch_change(self, e: events.ValueChangeEventArguments) -> None:
        """Switch between dark and light mode."""
        dark_mode = e.value
        self.dark_mode_switch.text = DARK_MODE_TEXT if dark_mode else LIGHT_MODE_TEXT

        if dark_mode:
            self.theme = self.theme.change(DarkTheme.get_mapping())
        else:
            self.theme = self.theme.change(LightTheme.get_mapping())

    ##########################
    # Drawing

    async def on_click_update(self) -> None:
        """Asynchronously update the UiPlot."""
        self.update_drawer_params()
        await self.plot.update_preview(self.drawer.draw)

    async def on_click_download_svg(self) -> None:
        """Asynchronously render the high resolution poster and download it as SVG."""
        svg_bytes = await self.plot.render_svg(self.drawer.draw)
        self.download(svg_bytes, "svg")

    async def on_click_download_pdf(self) -> None:
        """Asynchronously render the high resolution poster and download it as PDF."""
        svg_bytes = await self.plot.render_svg(self.drawer.draw)
        pdf_bytes = await self.plot.svg_to_pdf_bytes(svg_bytes)
        self.download(pdf_bytes, "pdf")

    def download(self, data: bytes, ext: Literal["svg", "pdf"]) -> None:
        """Download the high resolution poster."""
        basename = "poster"
        title = self.title.value
        if title:
            basename += f"_{sanitize_filename(title.replace(' ', '_'))}"
        ui.download(data, f'{basename}.{ext}')
        logger.info(f"{ext.upper()} Poster Downloaded")
