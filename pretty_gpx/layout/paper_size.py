#!/usr/bin/python3
"""Paper Size."""
from dataclasses import dataclass


@dataclass
class PaperSize:
    """Paper Size."""
    w_mm: int
    h_mm: int


PAPER_SIZES: dict[str, PaperSize] = {
    "A4": PaperSize(w_mm=210, h_mm=297),
    "50x70": PaperSize(w_mm=500, h_mm=700)
}
