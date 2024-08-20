#!/usr/bin/python3
"""NiceGUI Webapp. Drag&Drop GPX files to create a custom poster."""
import os
import tempfile
from collections.abc import Callable

from natsort import index_natsorted
from nicegui import events
from nicegui import run
from nicegui import ui

from pretty_gpx.drawing.theme_colors import COLOR_THEMES
from pretty_gpx.hillshading import AZIMUTHS
from pretty_gpx.poster_image_cache import DPI
from pretty_gpx.poster_image_cache import PosterDrawingData
from pretty_gpx.poster_image_cache import PosterImageCache
from pretty_gpx.ui_helper import on_click_slow_action_in_other_thread
from pretty_gpx.ui_helper import UiModal
from pretty_gpx.utils import safe


def process_files(list_b: list[bytes]) -> PosterImageCache:
    return PosterImageCache.from_gpx(list_b)


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
        res = update()
        update_done_callback(res)


with ui.row():
    ui.upload(label="Drag & drop your GPX file(s) here and press upload",
              multiple=True,
              on_multi_upload=on_multi_upload
              ).props('accept=.gpx'
                      ).on('rejected', lambda: ui.notify('Please provide a GPX file')
                           ).classes('max-w-full')

    ui.chat_message(
        ['Welcome 😀\nThis web app lets you create a custom poster from your cycling or hiking GPX file! 🚵 🥾',
         'For a multi-day trip, simply upload all consecutive GPX tracks together.\n'
         'Just make sure the filenames are in the correct alphabetical order.']
    ).props('bg-color=blue-2')

with ui.row():
    with ui.pyplot(close=False) as plot:
        ax = plot.fig.add_subplot()

    with ui.column():
        # Update options

        def update() -> PosterDrawingData:
            return cache.update_drawing_data(azimuth=AZIMUTHS[safe(azimuth_toggle.value)],
                                             theme_colors=COLOR_THEMES[safe(theme_toggle.value)],
                                             title_txt=title_button.value,
                                             uphill_m=uphill_button.value,
                                             dist_km=dist_km_button.value)

        def update_done_callback(poster_drawing_data: PosterDrawingData) -> None:
            with plot:
                cache.draw(plot.fig, ax, poster_drawing_data)
            ui.update(plot)

        def on_click_update() -> Callable:
            return on_click_slow_action_in_other_thread('Updating', update, update_done_callback)

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
                plot.fig.savefig(tmp_svg, dpi=DPI)
                with open(tmp_svg, "rb") as svg_file:
                    return svg_file.read()

        def download_done_callback(svg_bytes: bytes):
            ui.download(svg_bytes, 'poster.svg')

        def on_click_download() -> Callable:
            return on_click_slow_action_in_other_thread('Prepare HD Poster for Downloading',
                                                        download, download_done_callback)

        download_button = ui.button('Download', on_click=on_click_download())

cache = PosterImageCache.from_gpx([os.path.join("data/clo", "clo_1.gpx"),
                                   os.path.join("data/clo", "clo_2.gpx"),
                                   os.path.join("data/clo", "clo_3.gpx"),
                                   os.path.join("data/clo", "clo_4.gpx")])


res = update()
update_done_callback(res)
ui.run(reload=False)
