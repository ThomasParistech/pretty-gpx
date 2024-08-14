#!/usr/bin/python3
"""aaaaaaaa."""


from nicegui import events
from nicegui import ui

from pretty_gpx.drawing.theme_colors import COLOR_THEMES
from pretty_gpx.hillshading import AZIMUTHS
from pretty_gpx.utils import safe
from pretty_gpx.xxxxxxx import CyclingImageCache
import asyncio
from nicegui import ui, events
from nicegui import run, ui


async def on_file_upload(e: events.UploadEventArguments):
    ui.notify(f'File Uploaded {e.name}')
    global cache
    cache = await run.cpu_bound(process_file, e.content.read())
    ui.notify('Done')
    e.sender.reset()
    update()


def process_file(b: bytes) -> CyclingImageCache:
    return CyclingImageCache.from_gpx(b)


ui.upload(multiple=False,
          auto_upload=True,
          on_upload=on_file_upload
          ).props('accept=.gpx').on('rejected', lambda: ui.notify('Please provide a GPX file')).classes('max-w-full')

with ui.row():
    with ui.pyplot(close=False) as plot:
        ax = plot.fig.add_subplot()

    with ui.column():
        def update():
            with plot:
                cache.draw(plot.fig, ax,
                           azimuth=AZIMUTHS[safe(azimuth_toggle.value)],
                           theme_colors=COLOR_THEMES[safe(theme_toggle.value)],
                           title_txt=title_button.value,
                           uphill_m=uphill_button.value,
                           dist_km=dist_km_button.value)
            ui.update(plot)

        def download():
            tmp_svg = "data/tmp.svg"
            plot.fig.savefig(tmp_svg)
            with open(tmp_svg, "rb") as svg_file:
                svg_bytes = svg_file.read()
            ui.download(svg_bytes, 'cycling_poster.svg')

        with ui.input(label='Title', value="Title").on('keydown.enter', update) as title_button:
            ui.tooltip("Press Enter to update title")

        with ui.input(label='D+ (m)', value="").on('keydown.enter', update) as uphill_button:
            ui.tooltip("Press Enter to override elevation from GPX")

        with ui.input(label='Distance (km)', value="").on('keydown.enter', update) as dist_km_button:
            ui.tooltip("Press Enter to override distance from GPX")

        azimuth_toggle = ui.toggle(list(AZIMUTHS.keys()), value=list(AZIMUTHS.keys())[0], on_change=update)
        theme_toggle = ui.toggle(list(COLOR_THEMES.keys()), value=list(COLOR_THEMES.keys())[0], on_change=update)
        ui.button('Download', on_click=download)


# cache = CyclingImageCache.from_gpx("examples/marmotte.gpx")
# cache = CyclingImageCache.from_gpx("examples/couillole.gpx")
cache = CyclingImageCache.from_gpx("examples/vanoise.gpx")
# cache = CyclingImageCache.from_gpx("examples/ventoux.gpx")
update()

ui.run(reload=False)
