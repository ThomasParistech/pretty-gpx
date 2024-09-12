#!/usr/bin/python3
"""Simplify GPX file."""
import fire
import gpxpy

from pretty_gpx.utils.asserts import assert_isfile
from pretty_gpx.utils.utils import suffix_filename


def main(input: str, max_distance_m: float = 5.0):
    """Simplify GPX file using the Ramer-Douglas-Peucker algorithm."""
    assert_isfile(input, ext=".gpx")

    with open(input) as f:
        g = gpxpy.parse(f)

    g.simplify(max_distance=max_distance_m)

    output = suffix_filename(input, "_simplified")
    with open(output, "w") as f:
        f.write(g.to_xml())

    print(f"Saved simplified GPX to {output}")


if __name__ == "__main__":
    fire.Fire(main)
