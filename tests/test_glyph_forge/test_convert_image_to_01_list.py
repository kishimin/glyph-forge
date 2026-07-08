from PIL import Image

from glyph_forge.services.convert_image_to_01_list import (
    gray_list_2_wb_list,
    img_2_gray_list,
)


def test_img_2_gray_list_converts_rgb_pixels_to_grayscale_values():
    img = Image.new("RGB", (2, 1))
    img.putpixel((0, 0), (0, 0, 0))
    img.putpixel((1, 0), (255, 255, 255))

    assert img_2_gray_list(img) == [[0, 255]]


def test_gray_list_2_wb_list_uses_average_value_as_threshold():
    wb_list = gray_list_2_wb_list(
        [
            [0, 100],
            [200, 255],
        ]
    )

    assert wb_list == [
        [0, 0],
        [1, 1],
    ]
