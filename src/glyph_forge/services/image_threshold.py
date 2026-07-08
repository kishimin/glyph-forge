import numpy as np
from PIL import Image

from glyph_forge.services.settings import (
    BLACK_BINARY_VALUE,
    IMAGE_MODE_RGB,
    WHITE_BINARY_VALUE,
)


def image_to_grayscale_grid(input_img: Image.Image) -> list[list[float]]:
    rgb_array = np.asarray(input_img.convert(IMAGE_MODE_RGB), dtype=np.float32)
    return rgb_array.mean(axis=2).tolist()


def grayscale_grid_to_binary_grid(
    input_gray_grid: list[list[float]],
) -> list[list[int]]:
    gray_array = np.asarray(input_gray_grid)
    threshold = gray_array.mean()
    return np.where(
        gray_array >= threshold,
        WHITE_BINARY_VALUE,
        BLACK_BINARY_VALUE,
    ).tolist()
