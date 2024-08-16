#!/usr/bin/python3
"""aaaaaaaa."""


from natsort import index_natsorted
from nicegui import events
from nicegui import run
from nicegui import ui

from pretty_gpx.cycling_image_cache import CyclingImageCache
from pretty_gpx.drawing.theme_colors import COLOR_THEMES
from pretty_gpx.hillshading import AZIMUTHS
from pretty_gpx.utils import safe


async def on_multi_upload(e: events.MultiUploadEventArguments):
    sorted_indices = index_natsorted(e.names)
    names = [e.names[i] for i in sorted_indices]
    contents = [e.contents[i].read() for i in sorted_indices]
    e.sender.reset()

    if len(e.contents) == 1:
        ui.notify(f'Start processing {names[0]}')
    else:
        ui.notify(f'Start processing a {len(contents)}-days track ({", ".join(names)})')

    global cache
    cache = await run.cpu_bound(process_file, contents)
    ui.notify('Done')
    update()


def process_file(list_b: list[bytes]) -> CyclingImageCache:
    return CyclingImageCache.from_gpx(list_b)


with ui.row():
    ui.upload(label="Drag & drop your GPX file(s) here and press upload",
              multiple=True,
              on_multi_upload=on_multi_upload
              ).props('accept=.gpx').on('rejected', lambda: ui.notify('Please provide a GPX file')).classes('max-w-full')

    ui.chat_message(['Welcome 😀\nThis web app lets you create a custom poster from your cycling or hiking GPX file! 🚵 🥾',
                     'For a multi-day trip, simply upload all consecutive GPX tracks together.\n'
                     'Just make sure the filenames are in the correct alphabetical order.']
                    ).props('bg-color=blue-2')
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

cache = CyclingImageCache.from_gpx(["examples/vanoise1.gpx", "examples/vanoise2.gpx", "examples/vanoise3.gpx"])
update()

ui.run(reload=False)
