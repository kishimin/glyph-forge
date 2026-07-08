from importlib.resources import files

from PIL import Image, ImageDraw, ImageFont

from glyph_forge.services.settings import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_FRAME_CELL_PADDING_RATIO,
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


def load_font(font_size: int) -> ImageFont.FreeTypeFont:
    font_path = files("glyph_forge.fonts").joinpath("ipaexg.ttf")
    return ImageFont.truetype(str(font_path), size=font_size)


def _centered_text_offset(
    text: str,
    cell_size: int,
    font: ImageFont.FreeTypeFont,
) -> tuple[float, float]:
    left, top, right, bottom = font.getbbox(text)
    text_width = right - left
    text_height = bottom - top
    x = (cell_size - text_width) / 2 - left
    y = (cell_size - text_height) / 2 - top
    return x, y


def _resolve_cell_size(
    text_grid: list[list[str]],
    font: ImageFont.FreeTypeFont,
    font_size: int,
    cell_padding_ratio: float,
) -> int:
    padding = round(font_size * cell_padding_ratio)
    max_text_width = 0
    max_text_height = 0

    for row in text_grid:
        for text in row:
            left, top, right, bottom = font.getbbox(text)
            max_text_width = max(max_text_width, right - left)
            max_text_height = max(max_text_height, bottom - top)

    return max(font_size, max_text_width + padding * 2, max_text_height + padding * 2)


def _draw_solid_text_cell(
    img: Image.Image,
    row_index: int,
    column_index: int,
    mask: Image.Image,
    cell_size: int,
    fill: Color,
) -> None:
    cell_left = column_index * cell_size
    cell_top = row_index * cell_size
    img.paste(
        fill,
        (cell_left, cell_top, cell_left + cell_size, cell_top + cell_size),
        mask,
    )


def _solid_text_mask(
    text: str,
    cell_size: int,
    font: ImageFont.FreeTypeFont,
) -> Image.Image:
    mask = Image.new("L", (cell_size, cell_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text(
        _centered_text_offset(text, cell_size, font),
        text,
        fill=255,
        font=font,
    )
    return mask.point(lambda alpha: 255 if alpha else 0)


def render_text_grid_image(
    text_grid: list[list[str]],
    font_size: int,
    color_grid: list[list[Color]] | None = None,
    fill: Color = DEFAULT_TEXT_COLOR,
    background_color: Color = DEFAULT_BACKGROUND_COLOR,
    cell_padding_ratio: float = DEFAULT_FRAME_CELL_PADDING_RATIO,
) -> Image.Image:
    row_count = len(text_grid)
    column_count = max((len(row) for row in text_grid), default=0)
    font = load_font(font_size)
    cell_size = _resolve_cell_size(text_grid, font, font_size, cell_padding_ratio)
    img = Image.new(
        IMAGE_MODE_RGBA,
        (cell_size * column_count, cell_size * row_count),
        background_color,
    )
    mask_cache: dict[str, Image.Image] = {}

    for row_index, row in enumerate(text_grid):
        for column_index, text in enumerate(row):
            color = color_grid[row_index][column_index] if color_grid else fill
            if text not in mask_cache:
                mask_cache[text] = _solid_text_mask(text, cell_size, font)
            mask = mask_cache[text]
            _draw_solid_text_cell(
                img,
                row_index,
                column_index,
                mask,
                cell_size,
                color,
            )

    return img


def render_text_image(
    input_text: str,
    column_count: int,
    row_count: int,
    font_size: int,
    fill: Color = DEFAULT_TEXT_COLOR,
    background_color: Color = DEFAULT_BACKGROUND_COLOR,
    cell_padding_ratio: float = DEFAULT_FRAME_CELL_PADDING_RATIO,
) -> Image.Image:
    text_grid = [
        list(input_text[index : index + column_count])
        for index in range(0, column_count * row_count, column_count)
    ]
    return render_text_grid_image(
        text_grid,
        font_size,
        fill=fill,
        background_color=background_color,
        cell_padding_ratio=cell_padding_ratio,
    )
