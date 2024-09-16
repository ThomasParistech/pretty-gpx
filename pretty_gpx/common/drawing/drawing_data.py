#!/usr/bin/python3
"""Drawing Data."""
from dataclasses import asdict
from dataclasses import dataclass
from typing import Literal

from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path


@dataclass(kw_only=True, init=False)
class BaseDrawingData:
    """Base Drawing Annotations."""

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        raise NotImplementedError("Plot method must be implemented in child classes")


@dataclass(kw_only=True)
class TextData(BaseDrawingData):
    """Text Data."""
    x: float
    y: float

    s: str

    fontsize: float
    fontproperties: FontProperties
    ha: str

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        kwargs = asdict(self)
        ax.text(**kwargs, c=color)


@dataclass(kw_only=True)
class PlotData(BaseDrawingData):
    """Line plot Data."""
    x: list[float]
    y: list[float]

    linewidth: float
    linestyle: Literal["solid", "dashed", "dashdot", "dotted"] = "solid"

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        kwargs = asdict(self)
        ax.plot(kwargs.pop('x'), kwargs.pop('y'), **kwargs, c=color)


@dataclass(kw_only=True)
class ScatterData(BaseDrawingData):
    """Scatter Data."""
    x: list[float]
    y: list[float]

    marker: str | Path
    markersize: float

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        kwargs = asdict(self)
        ax.plot(kwargs.pop('x'), kwargs.pop('y'), **kwargs,
                linestyle='', clip_on=False,  # Allow start/end markers to be drawn outside the plot area
                c=color)


@dataclass
class PolyFillData(BaseDrawingData):
    """Polygon Fill Data."""
    x: list[float]
    y: list[float]

    def plot(self, ax: Axes, color: str) -> None:
        """Plot the annotation."""
        kwargs = asdict(self)
        ax.fill(kwargs.pop('x'), kwargs.pop('y'), **kwargs, c=color)

