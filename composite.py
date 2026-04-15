#!/usr/bin/env python3

import argparse
import math
from pathlib import Path

from PIL import Image


def load_images(first_path: Path, second_path: Path) -> tuple[Image.Image, Image.Image]:
    with Image.open(first_path) as first_image, Image.open(
            second_path) as second_image:
        first_rgba = first_image.convert("RGBA")
        second_rgba = second_image.convert("RGBA")

    if first_rgba.size != second_rgba.size:
        raise ValueError(
            f"Image sizes do not match: {first_rgba.size} != {second_rgba.size}"
        )

    return first_rgba, second_rgba


def composite_diagonal(first_rgba: Image.Image,
                       second_rgba: Image.Image) -> Image.Image:
    width, height = first_rgba.size
    output_image = second_rgba.copy()

    # Keep pixels from the first image when the pixel center lies on the
    # upper-left side of the diagonal connecting bottom-left to top-right.
    for y in range(height):
        boundary_x = width * (height - y - 0.5) / height
        split = max(0, min(width, math.ceil(boundary_x - 0.5)))
        if split == 0:
            continue
        row_slice = first_rgba.crop((0, y, split, y + 1))
        output_image.paste(row_slice, (0, y))

    return output_image


def composite_horizontal(first_rgba: Image.Image,
                         second_rgba: Image.Image) -> Image.Image:
    width, height = first_rgba.size
    split = width // 2
    output_image = second_rgba.copy()

    if split > 0:
        left_half = first_rgba.crop((0, 0, split, height))
        output_image.paste(left_half, (0, 0))

    return output_image


def save_image(image: Image.Image, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def parse_args() -> tuple[str, Path, Path]:
    parser = argparse.ArgumentParser(
        description=
        "Merge two PNG images with either a diagonal split or a width/2 split."
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--diag",
                            action="store_true",
                            help="Use the diagonal split from bottom-left to top-right")
    mode_group.add_argument("--horizontal",
                            action="store_true",
                            help="Use a width/2 split")
    parser.add_argument("first", type=Path, help="Path to the first PNG image")
    parser.add_argument("second",
                        type=Path,
                        help="Path to the second PNG image")
    args = parser.parse_args()
    mode = "diag" if args.diag else "horizontal"
    return mode, args.first, args.second


def main() -> None:
    mode, first, second = parse_args()
    first_rgba, second_rgba = load_images(first, second)

    if mode == "diag":
        output_image = composite_diagonal(first_rgba, second_rgba)
        output_path = Path("diag.png")
    else:
        output_image = composite_horizontal(first_rgba, second_rgba)
        output_path = Path("horizontal.png")

    save_image(output_image, output_path)


if __name__ == "__main__":
    main()
