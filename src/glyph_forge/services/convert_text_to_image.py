from PIL import Image, ImageDraw, ImageFont
from importlib.resources import files

from glyph_forge.services.settings import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_TEXT_COLOR,
    IMAGE_MODE_RGBA,
    Color,
)


def split_text_lines(input_text: str, max_chars_per_line: int) -> list[str]:
    if max_chars_per_line < 1:
        raise ValueError("max_chars_per_line must be greater than 0")

    return [
        input_text[index : index + max_chars_per_line]
        for index in range(0, len(input_text), max_chars_per_line)
    ] or [""]


def _load_font(text_size: int) -> ImageFont.FreeTypeFont:
    font_path = files("glyph_forge.fonts").joinpath("ipaexg.ttf")
    return ImageFont.truetype(str(font_path), size=text_size)


def _centered_text_position(
    row_index: int,
    column_index: int,
    text: str,
    text_size: int,
    font: ImageFont.FreeTypeFont,
) -> tuple[float, float]:
    left, top, right, bottom = font.getbbox(text)
    text_width = right - left
    text_height = bottom - top
    x = column_index * text_size + (text_size - text_width) / 2 - left
    y = row_index * text_size + (text_size - text_height) / 2 - top
    return x, y


def text_grid_2_img(
    text_grid: list[list[str]],
    text_size: int,
    color_grid: list[list[Color]] | None = None,
    fill: Color = DEFAULT_TEXT_COLOR,
    background_color: Color = DEFAULT_BACKGROUND_COLOR,
) -> Image.Image:
    row_count = len(text_grid)
    column_count = max((len(row) for row in text_grid), default=0)
    img = Image.new(
        IMAGE_MODE_RGBA,
        (text_size * column_count, text_size * row_count),
        background_color,
    )
    draw = ImageDraw.Draw(img)
    font = _load_font(text_size)

    for row_index, row in enumerate(text_grid):
        for column_index, text in enumerate(row):
            color = color_grid[row_index][column_index] if color_grid else fill
            draw.text(
                _centered_text_position(row_index, column_index, text, text_size, font),
                text,
                fill=color,
                font=font,
            )

    return img


def text_2_img(
    input_text: str,
    horizontal_len: int,
    vertical_len: int,
    text_size: int,
    fill: Color = DEFAULT_TEXT_COLOR,
    background_color: Color = DEFAULT_BACKGROUND_COLOR,
) -> Image.Image:
    """Convert the given string into an image

    Args:
        input_text (str)
        horizontal_len (int)
        vertical_len (int)
        text_size (int)

    Returns:
        Image.Image
    """
    text_grid = [
        list(input_text[index : index + horizontal_len])
        for index in range(0, horizontal_len * vertical_len, horizontal_len)
    ]
    return text_grid_2_img(
        text_grid,
        text_size,
        fill=fill,
        background_color=background_color,
    )
