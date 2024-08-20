#!/usr/bin/python3
"""NiceGUI Webapp. Drag&Drop GPX files to create a custom poster."""
import os
import tempfile
from collections.abc import Callable

from natsort import index_natsorted
from nicegui import events
from nicegui import run
from nicegui import ui
from pathvalidate import sanitize_filename

from pretty_gpx import EXAMPLES_DIR
from pretty_gpx.drawing.theme_colors import COLOR_THEMES
from pretty_gpx.hillshading import AZIMUTHS
from pretty_gpx.poster_image_cache import PosterDrawingData
from pretty_gpx.poster_image_cache import PosterImageCache
from pretty_gpx.poster_image_cache import PosterImageCaches
from pretty_gpx.ui_helper import on_click_slow_action_in_other_thread
from pretty_gpx.ui_helper import UiModal
from pretty_gpx.utils import safe


def process_files(list_b: list[bytes]) -> PosterImageCaches:
    return PosterImageCaches.from_gpx(list_b)


async def on_multi_upload(e: events.MultiUploadEventArguments):
    sorted_indices = index_natsorted(e.names)
    names = [e.names[i] for i in sorted_indices]
    contents = [e.contents[i].read() for i in sorted_indices]
    e.sender.reset()

    if len(e.contents) == 1:
        msg = f'Processing {names[0]}'
    else:
        msg = f'Processing a {len(contents)}-days track ({", ".join(names)})'

    with UiModal(msg):
        global cache
        cache = await run.cpu_bound(process_files, contents)
        res = update_low_res()
        update_done_callback_low_res(res)

with ui.row():
    ui.upload(label="Drag & drop your GPX file(s) here and press upload",
              multiple=True,
              on_multi_upload=on_multi_upload
              ).props('accept=.gpx'
                      ).on('rejected', lambda: ui.notify('Please provide a GPX file')
                           ).classes('max-w-full')

    ui.chat_message(
        ['Welcome 😀\nCreate a custom poster from your cycling/hiking GPX file! 🚵 🥾',
         'For multi-day trips, upload consecutive GPX tracks in alphabetical order.',
         'Customize your poster below and download the High-Resolution SVG file when ready.\n'
         '(Note: the rendered map below is a Low-Resolution preview.)']
    ).props('bg-color=blue-2')

with ui.row():
    with ui.pyplot(close=False) as plot:
        ax = plot.fig.add_subplot()

    with ui.column():
        # Update options

        def _update(c: PosterImageCache) -> PosterDrawingData:
            return c.update_drawing_data(azimuth=AZIMUTHS[safe(azimuth_toggle.value)],
                                         theme_colors=COLOR_THEMES[safe(theme_toggle.value)],
                                         title_txt=title_button.value,
                                         uphill_m=uphill_button.value,
                                         dist_km=dist_km_button.value)

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

        with ui.row().classes("w-full justify-between no-wrap"):
            ui.label("White Margin (cm): ").style("white-space: nowrap;")
            ui.slider(min=0, max=5, value=2, step=0.1).props('label-always')

        azimuth_toggle = ui.toggle(list(AZIMUTHS.keys()), value=list(AZIMUTHS.keys())[0], on_change=on_click_update())
        theme_toggle = ui.toggle(list(COLOR_THEMES.keys()), value=list(COLOR_THEMES.keys())[0],
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

        async def on_click_download() -> None:
            await on_click_slow_action_in_other_thread(f'Rendering at High Resolution ({cache.high_res.dpi} dpi)',
                                                       update_high_res, update_done_callback_high_res)()
            await on_click_slow_action_in_other_thread('Exporting SVG',
                                                       download, download_done_callback)()

        download_button = ui.button('Download', on_click=on_click_download)

cache = PosterImageCaches.from_gpx([os.path.join(EXAMPLES_DIR, "hiking/vanoise1.gpx"),
                                   os.path.join(EXAMPLES_DIR, "hiking/vanoise2.gpx"),
                                   os.path.join(EXAMPLES_DIR, "hiking/vanoise3.gpx")])

res = update_low_res()
update_done_callback_low_res(res)
ui.run(reload=False)
