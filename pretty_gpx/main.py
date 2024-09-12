#!/usr/bin/python3
"""NiceGUI Webapp. Drag&Drop GPX files to create a custom poster."""
import copy
import os
import tempfile
from collections.abc import Callable

from natsort import index_natsorted
from nicegui import app
from nicegui import events
from nicegui import run
from nicegui import ui
from pathvalidate import sanitize_filename

from pretty_gpx.drawing.hillshading import AZIMUTHS
from pretty_gpx.drawing.poster_image_cache import PosterDrawingData
from pretty_gpx.drawing.poster_image_cache import PosterImageCache
from pretty_gpx.drawing.poster_image_cache import PosterImageCaches
from pretty_gpx.drawing.poster_image_cache import W_DISPLAY_PIX
from pretty_gpx.drawing.theme_colors import DARK_COLOR_THEMES
from pretty_gpx.drawing.theme_colors import LIGHT_COLOR_THEMES
from pretty_gpx.gpx.augmented_gpx_data import AugmentedGpxData
from pretty_gpx.layout.paper_size import PAPER_SIZES
from pretty_gpx.layout.paper_size import PaperSize
from pretty_gpx.utils.paths import HIKING_DIR
from pretty_gpx.utils.ui_helper import on_click_slow_action_in_other_thread
from pretty_gpx.utils.ui_helper import shutdown_app_and_close_tab
from pretty_gpx.utils.ui_helper import UiModal
from pretty_gpx.utils.utils import safe


def process_files(list_b: list[bytes] | list[str], new_paper_size: PaperSize) -> PosterImageCaches:
    return PosterImageCaches.from_gpx(list_b, new_paper_size)


async def _on_upload(contents: list[bytes] | list[str], msg: str) -> None:
    with UiModal(msg):
        global cache
        cache = await run.cpu_bound(process_files, contents, PAPER_SIZES[safe(paper_size_mode_toggle.value)])

    await on_click_update()()


async def on_multi_upload(e: events.MultiUploadEventArguments):
    sorted_indices = index_natsorted(e.names)
    names = [e.names[i] for i in sorted_indices]
    contents = [e.contents[i].read() for i in sorted_indices]
    e.sender.reset()

    if len(contents) == 1:
        msg = f"Processing {names[0]}"
    else:
        msg = f'Processing a {len(names)}-days track ({", ".join(names)})'

    await _on_upload(contents, msg)


def change_paper_size(gpx_data: AugmentedGpxData, new_paper_size: PaperSize) -> PosterImageCaches:
    return PosterImageCaches.from_gpx_data(gpx_data, new_paper_size)


def change_duration_str(gpx_data: AugmentedGpxData, paper_size: PaperSize, new_duration_str: str) -> PosterImageCaches:
    return PosterImageCaches.update_duration_str(gpx_data,
                                                 paper_size,
                                                 new_duration_str)


async def on_click_load_example() -> None:
    contents = [os.path.join(HIKING_DIR, "vanoise1.gpx"),
                os.path.join(HIKING_DIR, "vanoise2.gpx"),
                os.path.join(HIKING_DIR, "vanoise3.gpx")]
    await _on_upload(contents, "Generate a 3-days example poster")
    await _on_upload(contents, f"Generate a {len(contents)}-days example poster")


async def on_paper_size_change() -> None:
    new_paper_size_name = safe(paper_size_mode_toggle.value)
    with UiModal(f"Creating {new_paper_size_name} Poster"):
        global cache
        cache = await run.cpu_bound(change_paper_size, copy.deepcopy(cache.gpx_data), PAPER_SIZES[new_paper_size_name])
    await on_click_update()()

async def on_duration_change() -> None:
    duration_value = ""
    if duration_switch.value:                
        duration_value = override_duration.value
    print("DURATION VALUE ",duration_value)
    new_paper_size_name = safe(paper_size_mode_toggle.value)
    with UiModal(f"Adding/deleting duration"):
        global cache
        cache = await run.cpu_bound(change_duration_str,
                                    copy.deepcopy(cache.gpx_data),
                                    PAPER_SIZES[new_paper_size_name],
                                    duration_value)
    await on_click_update()()

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
                  on_multi_upload=on_multi_upload
                  ).props('accept=.gpx'
                          ).on('rejected', lambda: ui.notify('Please provide a GPX file')
                               ).classes('max-w-full')

        with ui.card():
            paper_size_mode_toggle = ui.toggle(list(PAPER_SIZES.keys()), value=list(PAPER_SIZES.keys())[0],
                                               on_change=on_paper_size_change)

        # Update options
        with ui.card():
            def _update(c: PosterImageCache) -> PosterDrawingData:
                dark_mode = safe(dark_mode_switch.value)
                color_themes = (DARK_COLOR_THEMES if dark_mode else LIGHT_COLOR_THEMES)
                return c.update_drawing_data(azimuth=AZIMUTHS[safe(azimuth_toggle.value)],
                                             theme_colors=color_themes[safe(theme_toggle.value)],
                                             title_txt=title_button.value,
                                             uphill_m=uphill_button.value,
                                             dist_km=dist_km_button.value,
                                             duration=override_duration.value)

            def _update_done_callback(c: PosterImageCache, poster_drawing_data: PosterDrawingData) -> None:
                with plot:
                    c.draw(plot.fig, ax, poster_drawing_data)
                ui.update(plot)

            def update_high_res() -> PosterDrawingData:
                return _update(cache.high_res)

            def update_low_res() -> PosterDrawingData:
                return _update(cache.low_res)

            def update_done_callback_high_res(poster_drawing_data: PosterDrawingData) -> None:
                _update_done_callback(cache.high_res, poster_drawing_data)

            def update_done_callback_low_res(poster_drawing_data: PosterDrawingData) -> None:
                _update_done_callback(cache.low_res, poster_drawing_data)

            def on_click_update() -> Callable:
                return on_click_slow_action_in_other_thread('Updating', update_low_res, update_done_callback_low_res)

            with ui.input(label='Title', value="Title").on('keydown.enter', on_click_update()) as title_button:
                ui.tooltip("Press Enter to update title")

            with ui.input(label='D+ (m)', value="").on('keydown.enter', on_click_update()) as uphill_button:
                ui.tooltip("Press Enter to override elevation from GPX")

            with ui.input(label='Distance (km)', value="").on('keydown.enter', on_click_update()) as dist_km_button:
                ui.tooltip("Press Enter to override distance from GPX")

            duration_switch = ui.switch(text='Duration', value=False)
            duration_switch.tooltip("Toggle to show the duration")
            
            override_duration = ui.input(label='Duration', value="")
            override_duration.tooltip("Press the update button to override the duration from GPX")
            
            button = ui.button('Update duration', on_click=on_duration_change)


            azimuth_toggle = ui.toggle(list(AZIMUTHS.keys()), value=list(AZIMUTHS.keys())[0],
                                       on_change=on_click_update())

            DARK_MODE_TEXT = "🌙"
            LIGHT_MODE_TEXT = "☀️"

            def on_dark_mode_switch_change(e: events.ValueChangeEventArguments):
                dark_mode = e.value
                dark_mode_switch.text = DARK_MODE_TEXT if dark_mode else LIGHT_MODE_TEXT
                theme_toggle.options = list(DARK_COLOR_THEMES.keys()) if dark_mode else list(LIGHT_COLOR_THEMES.keys())
                theme_toggle.value = theme_toggle.options[0]
                theme_toggle.update()

            dark_mode_switch = ui.switch(DARK_MODE_TEXT, value=True,
                                         on_change=on_dark_mode_switch_change)

            theme_toggle = ui.toggle(list(DARK_COLOR_THEMES.keys()), value=list(DARK_COLOR_THEMES.keys())[0],
                                     on_change=on_click_update())

            # Download button

            def download() -> bytes:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_svg = os.path.join(tmp_dir, "tmp.svg")
                    plot.fig.savefig(tmp_svg, dpi=cache.high_res.dpi)
                    with open(tmp_svg, "rb") as svg_file:
                        return svg_file.read()

            def download_done_callback(svg_bytes: bytes):
                ui.download(svg_bytes, f'poster_{sanitize_filename(str(title_button.value).replace(" ", "_"))}.svg')
                print("Poster Downloaded")

            async def on_click_download() -> None:
                await on_click_slow_action_in_other_thread(f'Rendering at High Resolution ({cache.high_res.dpi} dpi)',
                                                           update_high_res, update_done_callback_high_res)()
                await on_click_slow_action_in_other_thread(f'Exporting SVG ({cache.high_res.dpi} dpi)',
                                                           download, download_done_callback)()

            download_button = ui.button('Download', on_click=on_click_download)


with ui.dialog() as exit_dialog, ui.card():
    ui.label('Confirm exit?')
    with ui.row():
        ui.button('Yes', on_click=lambda: shutdown_app_and_close_tab(), color='red-9')
        ui.button('Cancel', on_click=exit_dialog.close)


async def confirm_exit():
    """Display a confirmation dialog before exiting."""
    await exit_dialog


exit_button = ui.button('Exit',
                        on_click=confirm_exit,
                        color='red-9',
                        icon='logout').style('position: fixed; top: 10px; right: 10px;')

app.on_startup(on_click_load_example)

ui.run(title='Pretty GPX',
       favicon="✨",
       reload=False)
