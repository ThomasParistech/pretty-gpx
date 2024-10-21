#!/usr/bin/python3
"""NiceGUI Webapp. Drag&Drop GPX files to create a custom poster."""
import copy
import os
import tempfile
from collections.abc import Awaitable
from collections.abc import Callable
import sys
sys.path.insert(0,os.getcwd())
from enum import auto
from enum import Enum
from natsort import index_natsorted
from nicegui import app
from nicegui import events
from nicegui import ui
from nicegui.elements.upload import Upload
from nicegui.run import SubprocessException
from pathvalidate import sanitize_filename

from pretty_gpx.common.layout.paper_size import PAPER_SIZES
from pretty_gpx.common.layout.paper_size import PaperSize
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.nicegui_helper import on_click_slow_action_in_other_thread
from pretty_gpx.common.utils.nicegui_helper import run_cpu_bound
from pretty_gpx.common.utils.nicegui_helper import shutdown_app_and_close_tab
from pretty_gpx.common.utils.nicegui_helper import UiWaitingModal
from pretty_gpx.common.utils.paths import HIKING_DIR
from pretty_gpx.common.utils.profile import profile
from pretty_gpx.common.utils.profile import profile_parallel
from pretty_gpx.common.utils.profile import Profiling
from pretty_gpx.common.utils.utils import safe
from pretty_gpx.mountain.data.augmented_gpx_data import AugmentedGpxData
from pretty_gpx.mountain.drawing.hillshading import AZIMUTHS
from pretty_gpx.mountain.drawing.poster_image_cache import PosterDrawingData
from pretty_gpx.mountain.drawing.poster_image_cache import PosterImageCache
from pretty_gpx.mountain.drawing.poster_image_cache import PosterImageCaches
from pretty_gpx.mountain.drawing.poster_image_cache import W_DISPLAY_PIX
from pretty_gpx.mountain.drawing.theme_colors import DARK_COLOR_THEMES
from pretty_gpx.mountain.drawing.theme_colors import LIGHT_COLOR_THEMES

from matplotlib.axes import Axes

from typing import Dict, Any,Optional

class UiMode(Enum):
    MOUNTAIN = auto()

class UiManager:
    def __init__(self):
        self.__cache: Dict[UiMode, Optional[PosterImageCaches]] = {mode: None for mode in UiMode}
        self.ui_elements: Dict[UiMode, Dict[str, Any]] = {mode: {} for mode in UiMode}
        self.plots: Dict[UiMode, ui.pyplot] = {mode: ui.pyplot()  for mode in UiMode}
        self.axes: Dict[UiMode, Axes] = {mode: self.plots[mode].fig.add_subplot() for mode in UiMode}
        self.init_ui_elements()

    def init_ui_elements(self):
        for mode in UiMode:
            self.ui_elements[mode] = {
                'title_button': ui.input(label='Title', value=f"Title ({mode.name})"),
                'uphill_button': ui.input(label='D+ (m)', value=""),
                'dist_km_button': ui.input(label='Distance (km)', value=""),
                'azimuth_toggle': ui.toggle(list(AZIMUTHS.keys()), value=list(AZIMUTHS.keys())[0]),
                'dark_mode_switch': ui.switch("🌙", value=True),
                'theme_toggle': ui.toggle(list(DARK_COLOR_THEMES.keys()), value=list(DARK_COLOR_THEMES.keys())[0]),
                'paper_size_toggle': ui.toggle(list(PAPER_SIZES.keys()), value=list(PAPER_SIZES.keys())[0]),
                'upload': ui.upload(label=f"Drag & drop your GPX file(s) here for {mode.name} and press upload", multiple=True),
                'download_button': ui.button('Download', on_click=lambda m=mode: self.on_click_download(m)),
            }
            self.setup_event_handlers(mode)

    def setup_event_handlers(self, mode: UiMode):
        self.ui_elements[mode]['title_button'].on('keydown.enter', lambda: self.on_click_update(mode))
        self.ui_elements[mode]['uphill_button'].on('keydown.enter', lambda: self.on_click_update(mode))
        self.ui_elements[mode]['dist_km_button'].on('keydown.enter', lambda: self.on_click_update(mode))
        self.ui_elements[mode]['azimuth_toggle'].on('change', lambda: self.on_click_update(mode))
        self.ui_elements[mode]['dark_mode_switch'].on('change', lambda e: self.on_dark_mode_switch_change(e, mode))
        self.ui_elements[mode]['theme_toggle'].on('change', lambda: self.on_click_update(mode))
        self.ui_elements[mode]['paper_size_toggle'].on('change', lambda: self.on_paper_size_change(mode))
        self.ui_elements[mode]['upload'].on('upload', lambda e: self.on_multi_upload(e, mode))

    def setup_plot(self, mode: UiMode):
        with ui.card().classes(f'w-[{W_DISPLAY_PIX}px]').style('box-shadow: 0 0 20px 10px rgba(0, 0, 0, 0.2);'):
            with ui.pyplot(close=False) as self.plots[mode]:
                self.axes[mode] = self.plots[mode].fig.add_subplot()
                if self.axes[mode] is not None:
                    self.axes[mode].axis('off')


    async def on_multi_upload(self, e: events.MultiUploadEventArguments, mode: UiMode) -> None:
        sorted_indices = index_natsorted(e.names)
        names = [e.names[i] for i in sorted_indices]
        contents = [e.contents[i].read() for i in sorted_indices]
        assert isinstance(e.sender, Upload)
        e.sender.reset()

        msg = f"Processing {names[0]}" if len(contents) == 1 else f'Processing a {len(names)}-days track ({", ".join(names)})'
        await self._on_upload(contents, msg, mode)

    async def _on_upload(self, contents: list[bytes] | list[str], msg: str, mode: UiMode) -> None:
        with UiWaitingModal(msg):
            try:
                self.__cache[mode] = await run_cpu_bound(process_files, contents, PAPER_SIZES[safe(self.ui_elements[mode]['paper_size_toggle'].value)], mode)
            except SubprocessException as e:
                logger.error(f"Error while {msg}: {e}")
                logger.warning("Skip processing uploaded files")
                ui.notify(f'Error while {msg}:\n{e.original_message}', type='negative', multi_line=True, timeout=0, close_button='OK')
                return

        await self.on_click_update(mode)()

    async def on_paper_size_change(self, mode: UiMode) -> None:
        new_paper_size_name = str(safe(self.ui_elements[mode]['paper_size_toggle'].value))
        with UiWaitingModal(f"Creating {new_paper_size_name} Poster"):
            self.__cache[mode] = await run_cpu_bound(change_paper_size, copy.deepcopy(safe(self.__cache[mode]).gpx_data),
                                                     PAPER_SIZES[new_paper_size_name], mode)
        await self.on_click_update(mode)()

    def high_res_cache(self, mode: UiMode) -> PosterImageCache:
        return safe(self.__cache[mode]).high_res

    def low_res_cache(self, mode: UiMode) -> PosterImageCache:
        return safe(self.__cache[mode]).low_res

    def _update(self, c: PosterImageCache, mode: UiMode) -> PosterDrawingData:
        dark_mode = bool(safe(self.ui_elements[mode]['dark_mode_switch'].value))
        color_themes = DARK_COLOR_THEMES if dark_mode else LIGHT_COLOR_THEMES
        return c.update_drawing_data(
            azimuth=AZIMUTHS[safe(self.ui_elements[mode]['azimuth_toggle'].value)],
            theme_colors=color_themes[safe(self.ui_elements[mode]['theme_toggle'].value)],
            title_txt=self.ui_elements[mode]['title_button'].value,
            uphill_m=self.ui_elements[mode]['uphill_button'].value,
            dist_km=self.ui_elements[mode]['dist_km_button'].value
        )

    @profile_parallel
    def update_high_res(self, mode: UiMode) -> PosterDrawingData:
        return self._update(self.high_res_cache(mode), mode)

    @profile_parallel
    def update_low_res(self, mode: UiMode) -> PosterDrawingData:
        return self._update(self.low_res_cache(mode), mode)

    def update_done_callback(self, poster_drawing_data: PosterDrawingData, mode: UiMode, is_high_res: bool) -> None:
        if isinstance(poster_drawing_data, PosterDrawingData):
            cache = self.high_res_cache(mode) if is_high_res else self.low_res_cache(mode)
            with Profiling.Scope("Pyplot Context"):
                if self.plots[mode] and self.axes[mode]:
                    cache.draw(self.plots[mode].fig, self.axes[mode], poster_drawing_data)
            if self.plots[mode] is not None:
                ui.update(self.plots[mode])
        else:
            raise ValueError

    def on_click_update(self, mode: UiMode) -> Callable[[], Awaitable[None]]:
        return on_click_slow_action_in_other_thread(
            'Updating',
            lambda: self.update_low_res(mode),
            lambda data: self.update_done_callback(data, mode, False)
        )


    def on_dark_mode_switch_change(self, e: events.ValueChangeEventArguments, mode: UiMode) -> None:
        dark_mode = e.value
        self.ui_elements[mode]['dark_mode_switch'].text = "🌙" if dark_mode else "☀️"
        theme_options = list(DARK_COLOR_THEMES.keys()) if dark_mode else list(LIGHT_COLOR_THEMES.keys())
        self.ui_elements[mode]['theme_toggle'].options = theme_options
        self.ui_elements[mode]['theme_toggle'].value = theme_options[0]
        self.ui_elements[mode]['theme_toggle'].update()

    @profile_parallel
    def download(self, mode: UiMode) -> bytes:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with Profiling.Scope("Matplotlib Save SVG"):
                tmp_svg = os.path.join(tmp_dir, "tmp.svg")
                if self.plots[mode] and self.plots[mode].fig:
                    self.plots[mode].fig.savefig(tmp_svg, dpi=self.high_res_cache(mode).dpi)
                else:
                    raise ValueError("Plot or figure is not initialized")
            with open(tmp_svg, "rb") as svg_file:
                return svg_file.read()

    def download_done_callback(self, svg_bytes: bytes, mode: UiMode) -> None:
        ui.download(svg_bytes, f'poster_{mode.name}_{sanitize_filename(str(self.ui_elements[mode]["title_button"].value).replace(" ", "_"))}.svg')
        logger.info(f"Poster Downloaded for {mode.name}")

    async def on_click_download(self, mode: UiMode) -> None:
        dpi = self.high_res_cache(mode).dpi
        await on_click_slow_action_in_other_thread(f'Rendering at High Resolution ({dpi} dpi)',
                                                   lambda: self.update_high_res(mode),
                                                   lambda data: self.update_done_callback(data, mode, True))()
        await on_click_slow_action_in_other_thread(f'Exporting SVG ({dpi} dpi)',
                                                   lambda: self.download(mode),
                                                   lambda svg_bytes: self.download_done_callback(svg_bytes, mode))()

@profile_parallel
def process_files(list_b: list[bytes] | list[str], new_paper_size: PaperSize, mode: UiMode) -> PosterImageCaches:
    if mode == UiMode.MOUNTAIN:
        return PosterImageCaches.from_gpx(list_b, new_paper_size)
    elif mode == UiMode.CITY:
        # Implement city-specific processing here
        raise NotImplementedError("City mode not yet implemented")
    else:
        raise ValueError(f"Unsupported mode: {mode}")

@profile_parallel
def change_paper_size(gpx_data: AugmentedGpxData, new_paper_size: PaperSize, mode: UiMode) -> PosterImageCaches:
    if mode == UiMode.MOUNTAIN:
        return PosterImageCaches.from_augmented_gpx_data(gpx_data, new_paper_size)
    elif mode == UiMode.CITY:
        # Implement city-specific paper size change here
        raise NotImplementedError("City mode not yet implemented")
    else:
        raise ValueError(f"Unsupported mode: {mode}")

ui_manager = UiManager()

def create_ui():
    with ui.column(align_items="center"):
        ui.chat_message(
            ['Welcome 😀\nCreate a custom poster from\n'
             'your cycling/hiking GPX file! 🚵 🥾',
             'For multi-day trips, upload all consecutive\n'
             'GPX tracks together.\n'
             '(Make sure filenames are in alphabetical order)',
             'Customize your poster below and download\n'
             'the High-Resolution SVG file when ready.\n'
             '(N.B. the map below is a Low-Resolution preview.)']
        ).props('bg-color=blue-2')

    create_mode_ui(UiMode.MOUNTAIN)

    with ui.dialog() as exit_dialog, ui.card():
        ui.label('Confirm exit?')
        with ui.row():
            ui.button('Yes', on_click=lambda: shutdown_app_and_close_tab(), color='red-9')
            ui.button('Cancel', on_click=exit_dialog.close)

    async def confirm_exit() -> None:
        await exit_dialog

    exit_button = ui.button('Exit',
                            on_click=confirm_exit,
                            color='red-9',
                            icon='logout').style('position: fixed; top: 10px; right: 10px;')

def create_mode_ui(mode: UiMode):
    with ui.column(align_items="center"):
        with ui.card().classes('w-full'):
            ui.label(f"{mode.name} Mode").classes('text-h6')
            ui_manager.ui_elements[mode]['upload'].props('accept=.gpx').on('rejected', lambda: ui.notify('Please provide a GPX file'))
            ui_manager.ui_elements[mode]['paper_size_toggle']
            ui_manager.ui_elements[mode]['title_button']
            ui_manager.ui_elements[mode]['uphill_button']
            ui_manager.ui_elements[mode]['dist_km_button']
            ui_manager.ui_elements[mode]['azimuth_toggle']
            ui_manager.ui_elements[mode]['dark_mode_switch']
            ui_manager.ui_elements[mode]['theme_toggle']
            ui_manager.ui_elements[mode]['download_button']

        ui_manager.setup_plot(mode)
        with ui.card().classes(f'w-[{W_DISPLAY_PIX}px]').style('box-shadow: 0 0 20px 10px rgba(0, 0, 0, 0.2);'):
            ui_manager.plots[mode]


create_ui()

async def load_example():
    contents = [os.path.join(HIKING_DIR, f"vanoise{i}.gpx") for i in range(1, 4)]
    await ui_manager._on_upload(contents, f"Generate a {len(contents)}-days example poster", UiMode.MOUNTAIN)

app.on_startup(load_example)
app.on_shutdown(lambda: Profiling.export_events())


ui.run(title='Pretty GPX',
       favicon="✨",
       reload=False)
