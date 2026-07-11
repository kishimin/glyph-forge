from PIL import Image

from glyph_forge.services.image_threshold import (
    grayscale_grid_to_binary_grid,
    image_to_grayscale_grid,
)


def test_image_to_grayscale_grid_converts_rgb_pixels_to_grayscale_values():
    img = Image.new("RGB", (2, 1))
    img.putpixel((0, 0), (0, 0, 0))
    img.putpixel((1, 0), (255, 255, 255))

    assert image_to_grayscale_grid(img) == [[0, 255]]


def test_grayscale_grid_to_binary_grid_uses_average_value_as_threshold():
    binary_grid = grayscale_grid_to_binary_grid(
        [
            [0, 100],
            [200, 255],
        ]
    )

    assert binary_grid == [
        [0, 0],
        [1, 1],
    ]
