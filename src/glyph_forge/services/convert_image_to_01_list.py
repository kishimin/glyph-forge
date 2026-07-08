from PIL import Image
import numpy as np

from glyph_forge.services.settings import (
    BLACK_BINARY_VALUE,
    IMAGE_MODE_RGB,
    WHITE_BINARY_VALUE,
)


def img_2_gray_list(input_img: Image.Image) -> list[list[float]]:
    """Converts the provided image into a grayscale(white = 1, gray = 0.5, black = 0)
        It is designed to handle even color images.

    Args:
        input_img (Image.Image)

    Returns:
        list[int]
    """
    rgb_array = np.asarray(input_img.convert(IMAGE_MODE_RGB), dtype=np.float32)
    return rgb_array.mean(axis=2).tolist()


def gray_list_2_wb_list(input_gray_list: list[list[float]]) -> list[list[int]]:
    """Convert the provided grayscale image into a binary image where white = 1 and black = 0.
        To prevent images with predominantly black areas from becoming entirely black,
        or images with light colors from becoming entirely white,
        calculate the average value as a threshold and use that threshold to datetime
        the value of each pixel.
        As a result, list areas will not be converted entirely to white, nor will dark
        areas be converted entirely to black.

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
