"""Check title wrapping against actual rendered poster bounds."""
from types import SimpleNamespace

import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties

from pretty_gpx.common.drawing.components.centered_title import CenteredTitle
from pretty_gpx.common.drawing.utils.drawing_figure import A4Float, DrawingFigure
from pretty_gpx.common.gpx.gpx_bounds import GpxBounds
from pretty_gpx.common.layout.paper_size import PAPER_SIZES


@pytest.mark.parametrize('paper', PAPER_SIZES.values(), ids=PAPER_SIZES.keys())
@pytest.mark.parametrize('title', [
    'Title',
    'A very long adventure across the mountains and valleys with friends',
    'Supercalifragilisticexpialidocious' * 5,
    'First line\nSecond line',
    '',
])
def test_title_fits_bounds(paper, title):
    figure = Figure()
    FigureCanvasAgg(figure)
    axes = figure.add_subplot()
    bounds = GpxBounds(lon_min=0, lon_max=1, lat_min=0, lat_max=1)
    title_bounds = GpxBounds(lon_min=0, lon_max=1, lat_min=0.85, lat_max=1)
    params = SimpleNamespace(user_title=title, centered_title_font_color='black',
                             centered_title_font_size=A4Float(mm=20),
                             centered_title_fontproperties=FontProperties())
    with DrawingFigure(paper, bounds, figure, axes) as drawing:
        CenteredTitle(title_bounds).draw(drawing, params)
    figure.canvas.draw()
    label = axes.texts[0]
    if not title:
        assert label.get_text() == ''
        return
    box = label.get_window_extent(figure.canvas.get_renderer())
    left, bottom = axes.transData.transform((title_bounds.lon_min, title_bounds.lat_min))
    right, top = axes.transData.transform((title_bounds.lon_max, title_bounds.lat_max))
    assert box.x0 >= left - 0.01
    assert box.x1 <= right + 0.01
    assert box.y0 >= bottom - 0.01
    assert box.y1 <= top + 0.01
    if title == 'Title':
        assert label.get_text() == title
    elif '\n' not in title:
        assert '\n' in label.get_text()
