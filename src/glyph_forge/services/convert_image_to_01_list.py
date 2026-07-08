import numpy as np
from PIL import Image

from glyph_forge.services.settings import (
    BLACK_BINARY_VALUE,
    IMAGE_MODE_RGB,
    WHITE_BINARY_VALUE,
)


def img_2_gray_list(input_img: Image.Image) -> list[list[float]]:
    """Convert the provided image into a grayscale list.

    It is designed to handle even color images.

    Args:
        input_img (Image.Image)

    Returns:
        list[int]
    """
    rgb_array = np.asarray(input_img.convert(IMAGE_MODE_RGB), dtype=np.float32)
    return rgb_array.mean(axis=2).tolist()


def gray_list_2_wb_list(input_gray_list: list[list[float]]) -> list[list[int]]:
    """Convert grayscale values into a binary black-and-white image.

    The average value is used as a threshold. This prevents predominantly
    black or light images from being converted entirely to one value.

    Args:
        input_gray_list (list[int])

    Returns:
        list[int]
    """
    gray_array = np.asarray(input_gray_list)
    threshold = gray_array.mean()
    return np.where(
        gray_array >= threshold,
        WHITE_BINARY_VALUE,
        BLACK_BINARY_VALUE,
    ).tolist()
