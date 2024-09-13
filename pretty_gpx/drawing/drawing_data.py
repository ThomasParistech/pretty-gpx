#!/usr/bin/python3
"""Drawing Data."""
from collections.abc import Callable
from dataclasses import asdict
from dataclasses import dataclass
from typing import Literal
from typing import overload

from matplotlib.axes import Axes
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path

from pretty_gpx.utils.asserts import assert_same_len


@overload
def imshow_scale(old_value: float, old_size: int, new_size: float) -> float: ...


@overload
def imshow_scale(old_value: list[float], old_size: int, new_size: float) -> list[float]: ...


def imshow_scale(old_value: float | list[float], old_size: int, new_size: float) -> float | list[float]:
    """Account for the 0.5pix offset during scaling of coordinates from one plt.imshow to another.

    Args:
        old_value: X (resp. Y) value in the plot defined by plt.imshow with width (resp. height) of length `old_size`
        old_size: Old image width (resp. height)
        new_size:: New image width (resp. height)

    Returns:
        new_value: X (resp. Y) value in the plot defined by plt.imshow with width (resp. height) of length `new_size`
    """
    if isinstance(old_value, list):
        return [imshow_scale(old_v, old_size, new_size) for old_v in old_value]
    return (old_value + 0.5) * new_size / old_size - 0.5


@dataclass
class BaseDrawingData:
    """Base Drawing Annotations for a plot defined by plt.imshow at a given scale."""
    x: float | list[float]
    y: float | list[float]

    def __init__(self) -> None:
        raise NotImplementedError()

    def __post_init__(self) -> None:
        """Ensure x and y have the same length."""
        if isinstance(self.x, list) or isinstance(self.y, list):
            assert isinstance(self.x, list) and isinstance(self.y, list), "x and y must be both lists or both floats"
            assert_same_len([self.x, self.y], msg="x and y must have the same length")

    @staticmethod
    def get_plot_func(ax: Axes) -> Callable:
        """Get corresponding matplotlib plot function, e.g. ax.plot, ax.text, ax.fill ..."""
        raise NotImplementedError()

    def plot(self, ax: Axes, color: str, old_shape: tuple[int, ...], new_shape: tuple[int, ...]) -> None:
        """Plot the annotation with the appropriate scale."""
        old_h, old_w = tuple(old_shape[:2])
        new_h, new_w = tuple(new_shape[:2])

        kwargs = asdict(self)
        kwargs.pop('x')
        kwargs.pop('y')

        scaled_x = imshow_scale(self.x, old_w, new_w)
        scaled_y = imshow_scale(self.y, old_h, new_h)

        self.get_plot_func(ax)(scaled_x, scaled_y, **kwargs, c=color)

    def __len__(self) -> int:
        """Return the number of points in the annotation."""
        return len(self.x) if isinstance(self.x, list) else 1


@dataclass
class TextData(BaseDrawingData):
    """Text Data."""
    x: float
    y: float

    s: str

    fontsize: float
    fontproperties: FontProperties
    ha: str

    @staticmethod
    def get_plot_func(ax: Axes) -> Callable:
        """Get corresponding matplotlib plot function, e.g. ax.plot, ax.text, ax.fill ..."""
        return ax.text


@dataclass
class PlotData(BaseDrawingData):
    """Line plot Data."""
    x: list[float]
    y: list[float]

    linewidth: float
    linestyle: Literal["solid", "dashed", "dashdot", "dotted"] = "solid"

    @staticmethod
    def get_plot_func(ax: Axes) -> Callable:
        """Get corresponding matplotlib plot function, e.g. ax.plot, ax.text, ax.fill ..."""
        return ax.plot


@dataclass
class ScatterData(BaseDrawingData):
    """Scatter Data."""
    x: list[float]
    y: list[float]

    marker: str | Path
    markersize: float

    @staticmethod
    def get_plot_func(ax: Axes) -> Callable:
        """Get corresponding matplotlib plot function, e.g. ax.plot, ax.text, ax.fill ..."""
        def plot_with_no_lines(*args, **kwargs):
            return ax.plot(*args, linestyle='',
                           clip_on=False,  # Allow start/end markers to be drawn outside the plot area
                           **kwargs)
        return plot_with_no_lines


@dataclass
class PolyFillData(BaseDrawingData):
    """Polygon Fill Data."""
    x: list[float]
    y: list[float]

    @staticmethod
    def get_plot_func(ax: Axes) -> Callable:
        """Get corresponding matplotlib plot function, e.g. ax.plot, ax.text, ax.fill ..."""
        return ax.fill
