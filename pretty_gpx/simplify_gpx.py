#!/usr/bin/python3
"""Simplify GPX file."""
import fire

from pretty_gpx.common.gpx.gpx_io import load_gpxpy
from pretty_gpx.common.utils.logger import logger
from pretty_gpx.common.utils.utils import suffix_filename


def main(input: str, max_distance_m: float = 5.0) -> None:
    """Simplify GPX file using the Ramer-Douglas-Peucker algorithm."""
    g = load_gpxpy(input)

    g.simplify(max_distance=max_distance_m)

    output = suffix_filename(input, "_simplified")
    with open(output, "w") as f:
        f.write(g.to_xml())

    logger.info(f"Saved simplified GPX to {output}")


if __name__ == "__main__":
    fire.Fire(main)
