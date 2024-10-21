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

class UiMode(Enum):
    MOUNTAIN = auto()

class UiManager:
    """Manage the UI elements and the Poster cache."""

    def __init__(self) -> None:
        self.__cache: dict[UiMode, PosterImageCaches | None] = {
            UiMode.MOUNTAIN: None,
        }

    async def _on_upload(self, contents: list[bytes] | list[str], msg: str, mode: UiMode) -> None:
        """Pocess the files asynchronously to update the Poster cache."""
        with UiWaitingModal(msg):
            try:
                self.__cache[mode] = await run_cpu_bound(process_files,
                                                         contents, PAPER_SIZES[safe(paper_size_mode_toggle.value)], mode)
            except SubprocessException as e:
                logger.error(f"Error while {msg}: {e}")
                logger.warning("Skip processing uploaded files")
                ui.notify(f'Error while {msg}:\n{e.original_message}',
                          type='negative', multi_line=True, timeout=0, close_button='OK')
                return

        await on_click_update(mode)()

    async def on_multi_upload(self, e: events.MultiUploadEventArguments, mode: UiMode) -> None:
        """Sort the uploaded files by name and process them to update the Poster cache."""
        sorted_indices = index_natsorted(e.names)
        names = [e.names[i] for i in sorted_indices]
        contents = [e.contents[i].read() for i in sorted_indices]
        assert isinstance(e.sender, Upload)
        e.sender.reset()

        if len(contents) == 1:
            msg = f"Processing {names[0]}"
        else:
            msg = f'Processing a {len(names)}-days track ({", ".join(names)})'

        await self._on_upload(contents, msg, mode)

    async def on_click_load_example(self) -> None:
        """Load the example GPX files."""
        contents = [os.path.join(HIKING_DIR, "vanoise1.gpx"),
                    os.path.join(HIKING_DIR, "vanoise2.gpx"),
                    os.path.join(HIKING_DIR, "vanoise3.gpx")]
        await self._on_upload(contents, f"Generate a {len(contents)}-days example poster", UiMode.MOUNTAIN)

    async def on_paper_size_change(self, mode: UiMode) -> None:
        """Change the paper size and update the poster."""
        new_paper_size_name = str(safe(paper_size_mode_toggle.value))
        with UiWaitingModal(f"Creating {new_paper_size_name} Poster"):
            self.__cache[mode] = await run_cpu_bound(change_paper_size, copy.deepcopy(safe(self.__cache[mode]).gpx_data),
                                                     PAPER_SIZES[new_paper_size_name], mode)
        await on_click_update(mode)()


    def high_res_cache(self, mode: UiMode) -> PosterImageCache:
        """Return the high resolution Poster cache."""
        return safe(self.__cache[mode]).high_res


    def low_res_cache(self, mode: UiMode) -> PosterImageCache:
        """Return the low resolution Poster cache."""
        return safe(self.__cache[mode]).low_res


ui_manager = UiManager()


@profile_parallel
def process_files(list_b: list[bytes] | list[str], new_paper_size: PaperSize, mode: UiMode) -> PosterImageCaches:
    """Process the uploaded files and return the PosterImageCaches."""
    if mode == UiMode.MOUNTAIN:
        return PosterImageCaches.from_gpx(list_b, new_paper_size)
    else:
        raise ValueError


@profile_parallel
def change_paper_size(gpx_data: AugmentedGpxData, new_paper_size: PaperSize, mode: UiMode) -> PosterImageCaches:
    """Return the PosterImageCaches with the new paper size."""
    if mode == UiMode.MOUNTAIN:
        return PosterImageCaches.from_augmented_gpx_data(gpx_data, new_paper_size)
    else:
        raise ValueError


with ui.row():
    with ui.card().classes(f'w-[{W_DISPLAY_PIX}px]').style('box-shadow: 0 0 20px 10px rgba(0, 0, 0, 0.2);'):
        with ui.pyplot(close=False) as plot:
            ax = plot.fig.add_subplot()
            ax.axis('off')

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

        ui.upload(label="Drag & drop your GPX file(s) here and press upload",
                  multiple=True,
                  on_multi_upload=ui_manager.on_multi_upload
                  ).props('accept=.gpx'
                          ).on('rejected', lambda: ui.notify('Please provide a GPX file')
                               ).classes('max-w-full')

        with ui.card():
            paper_size_mode_toggle = ui.toggle(list(PAPER_SIZES.keys()), value=list(PAPER_SIZES.keys())[0],
                                               on_change=ui_manager.on_paper_size_change)

        # Update options
        with ui.card():
            def _update(c: PosterImageCache) -> PosterDrawingData:
                """Asynchronously update the PosterDrawingData with the current settings."""
                dark_mode = bool(safe(dark_mode_switch_mountain.value))

                color_themes = (DARK_COLOR_THEMES if dark_mode else LIGHT_COLOR_THEMES)
                return c.update_drawing_data(azimuth=AZIMUTHS[safe(azimuth_toggle.value)],
                                             theme_colors=color_themes[safe(theme_toggle_mountain.value)],
                                             title_txt=title_button_mountain.value,
                                             uphill_m=uphill_button_mountain.value,
                                             dist_km=dist_km_button_mountain.value)

            def _update_done_callback(c: PosterImageCache, poster_drawing_data: PosterDrawingData) -> None:
                """Synchronously update the plot with the PosterDrawingData (Matplotlib must run in the main thread)."""
                with Profiling.Scope("Pyplot Context"), plot:
                    c.draw(plot.fig, ax, poster_drawing_data)
                ui.update(plot)

            @profile_parallel
            def update_high_res(mode: UiMode) -> PosterDrawingData:
                """Update the PosterDrawingData with the current settings, at the high resolution."""
                return _update(ui_manager.high_res_cache(mode))

            @profile_parallel
            def update_low_res(mode: UiMode) -> PosterDrawingData:
                """Update the PosterDrawingData with the current settings, at the low resolution."""
                return _update(ui_manager.low_res_cache(mode))

            @profile
            def update_done_callback_high_res(poster_drawing_data: PosterDrawingData) -> None:
                """Update the plot with the high resolution PosterDrawingData."""
                if isinstance(poster_drawing_data, PosterDrawingData):
                    _update_done_callback(ui_manager.high_res_cache(UiMode.MOUNTAIN), poster_drawing_data)
                else:
                    raise ValueError

            @profile
            def update_done_callback_low_res(poster_drawing_data: PosterDrawingData) -> None:
                """Update the plot with the low resolution PosterDrawingData."""
                if isinstance(poster_drawing_data, PosterDrawingData):
                    _update_done_callback(ui_manager.low_res_cache(UiMode.MOUNTAIN), poster_drawing_data)
                else:
                    raise ValueError

            def on_click_update(mode: UiMode) -> Callable[[], Awaitable[None]]:
                """Return an async function that updates the poster with the current settings."""
                return on_click_slow_action_in_other_thread('Updating', lambda: update_low_res(mode), update_done_callback_low_res)

            with ui.input(label='Title', value="Title").on('keydown.enter', on_click_update(UiMode.MOUNTAIN)) as title_button_mountain:
                ui.tooltip("Press Enter to update title")

            with ui.input(label='D+ (m)', value="").on('keydown.enter', on_click_update(UiMode.MOUNTAIN)) as uphill_button_mountain:
                ui.tooltip("Press Enter to override elevation from GPX")

            with ui.input(label='Distance (km)', value="").on('keydown.enter', on_click_update(UiMode.MOUNTAIN)) as dist_km_button_mountain:
                ui.tooltip("Press Enter to override distance from GPX")

            azimuth_toggle = ui.toggle(list(AZIMUTHS.keys()), value=list(AZIMUTHS.keys())[0],
                                       on_change=on_click_update(UiMode.MOUNTAIN))

            DARK_MODE_TEXT = "🌙"
            LIGHT_MODE_TEXT = "☀️"

            def on_dark_mode_switch_change(e: events.ValueChangeEventArguments) -> None:
                """Switch between dark and light mode."""
                dark_mode_mountain = e.value
                dark_mode_switch_mountain.text = DARK_MODE_TEXT if dark_mode_mountain else LIGHT_MODE_TEXT
                theme_toggle_mountain.options = list(DARK_COLOR_THEMES.keys()) if dark_mode_mountain else list(LIGHT_COLOR_THEMES.keys())
                theme_toggle_mountain.value = theme_toggle_mountain.options[0]
                theme_toggle_mountain.update()

            dark_mode_switch_mountain = ui.switch(DARK_MODE_TEXT, value=True,
                                         on_change=on_dark_mode_switch_change)

            theme_toggle_mountain = ui.toggle(list(DARK_COLOR_THEMES.keys()), value=list(DARK_COLOR_THEMES.keys())[0],
                                     on_change=on_click_update(UiMode.MOUNTAIN))

            # Download button

            @profile_parallel
            def download() -> bytes:
                """Save the high resolution poster as SVG and return the bytes."""
                with tempfile.TemporaryDirectory() as tmp_dir:
                    with Profiling.Scope("Matplotlib Save SVG"):
                        tmp_svg = os.path.join(tmp_dir, "tmp.svg")
                        plot.fig.savefig(tmp_svg, dpi=ui_manager.high_res_cache.dpi)
                    with open(tmp_svg, "rb") as svg_file:
                        return svg_file.read()

            def download_done_callback(svg_bytes: bytes) -> None:
                """Download the SVG file."""
                ui.download(svg_bytes, f'poster_{sanitize_filename(str(title_button_mountain.value).replace(" ", "_"))}.svg')
                logger.info("Poster Downloaded")

            async def on_click_download() -> None:
                """Asynchronously render the high resolution poster and download it as SVG."""
                dpi = ui_manager.high_res_cache.dpi
                await on_click_slow_action_in_other_thread(f'Rendering at High Resolution ({dpi} dpi)',
                                                           update_high_res, update_done_callback_high_res)()
                await on_click_slow_action_in_other_thread(f'Exporting SVG ({dpi} dpi)',
                                                           download, download_done_callback)()

            download_button = ui.button('Download', on_click=on_click_download)


with ui.dialog() as exit_dialog, ui.card():
    ui.label('Confirm exit?')
    with ui.row():
        ui.button('Yes', on_click=lambda: shutdown_app_and_close_tab(), color='red-9')
        ui.button('Cancel', on_click=exit_dialog.close)


async def confirm_exit() -> None:
    """Display a confirmation dialog before exiting."""
    await exit_dialog


exit_button = ui.button('Exit',
                        on_click=confirm_exit,
                        color='red-9',
                        icon='logout').style('position: fixed; top: 10px; right: 10px;')

app.on_startup(ui_manager.on_click_load_example)
app.on_shutdown(lambda: Profiling.export_events())

ui.run(title='Pretty GPX',
       favicon="✨",
       reload=False)
