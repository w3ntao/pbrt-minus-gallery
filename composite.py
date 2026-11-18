#!/usr/bin/env python3

import argparse
import math
import os
from pathlib import Path

from PIL import Image
from termcolor import colored


def load_images(
    first_path: Path, second_path: Path, *other_paths: Path
) -> tuple[Image.Image, ...]:
    images = []
    for path in (first_path, second_path, *other_paths):
        with Image.open(path) as image:
            if images and image.size != images[0].size:
                raise ValueError(
                    f"Image sizes do not match: {path} has size {image.size}, "
                    f"expected {images[0].size}"
                )
            images.append(image.convert("RGBA"))

    return tuple(images)


def composite_diagonal(
    first_rgba: Image.Image, second_rgba: Image.Image, *other_rgba: Image.Image
) -> Image.Image:
    images = (first_rgba, second_rgba, *other_rgba)
    width, height = first_rgba.size
    split_count = len(images) - 1
    output_image = images[-1].copy()

    # Boundary i joins (i * width / split_count, 0) to
    # ((i - 1) * width / split_count, height). Boundary pixels use the next image.
    for y in range(height):
        left = 0
        for i, image in enumerate(images[:-1], start=1):
            boundary_x = width * (i * height - y - 0.5) / (height * split_count)
            right = max(0, min(width, math.ceil(boundary_x - 0.5)))
            if right > left:
                row_slice = image.crop((left, y, right, y + 1))
                output_image.paste(row_slice, (left, y))
            left = right

    return output_image


def composite_horizontal(
    first_rgba: Image.Image, second_rgba: Image.Image
) -> Image.Image:
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


def parse_args() -> tuple[str, list[Path]]:
    parser = argparse.ArgumentParser(
        description="Merge two or more PNG images with diagonal splits, "
        "or two PNG images with a width/2 split."
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--diag",
        action="store_true",
        help="Split two or more images along parallel diagonals",
    )
    mode_group.add_argument(
        "--horizontal", action="store_true", help="Use a width/2 split"
    )
    parser.add_argument(
        "images",
        type=Path,
        nargs="+",
        metavar="IMAGE",
        help="Input PNG images in order",
    )
    args = parser.parse_args()
    if len(args.images) < 2:
        parser.error("at least two input images are required")
    if args.horizontal and len(args.images) != 2:
        parser.error("--horizontal requires exactly two input images")
    mode = "diag" if args.diag else "horizontal"
    return mode, args.images


def main() -> None:
    mode, paths = parse_args()
    images = load_images(*paths)

    if mode == "diag":
        output_image = composite_diagonal(*images)
        output_path = Path("diag.png")
    else:
        output_image = composite_horizontal(*images)
        output_path = Path("horizontal.png")

    save_image(output_image, output_path)
    print("out image: {}".format(colored(os.path.abspath(output_path), "red")))


if __name__ == "__main__":
    main()
