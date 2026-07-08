from PIL import Image
from glyph_forge.services.convert_text_to_image import (
    split_text_lines,
    text_2_img,
    text_grid_2_img,
)
from glyph_forge.services.convert_image_to_01_list import (
    gray_list_2_wb_list,
    img_2_gray_list,
)
from glyph_forge.services.fill_wb_list_with_text import wb_list_2_wb_text_list
from glyph_forge.services.settings import GlyphForgeConfig


def _build_color_grid(
    wb_list: list[list[int]],
    config: GlyphForgeConfig,
) -> list[list[tuple[int, int, int]]]:
    return [
        [
            config.outer_color if wb_value == 1 else config.inner_color
            for wb_value in wb_row
        ]
        for wb_row in wb_list
    ]


def text_2_text_img(
    flame_text: str,
    inner_text: str,
    outer_text: str,
    horizontal_len: int | None = None,
    vertical_len: int | None = None,
    text_size: int | None = None,
    final_text_size: int | None = None,
    *,
    config: GlyphForgeConfig | None = None,
) -> Image.Image:
    """Execute the processing in batches and save the resulting list of characters as an image

    Args:
        flame_text (str)
        inner_text (str)
        outer_text (str)
        horizontal_len (int)
        vertical_len (int)
        text_size (int)
        final_text_size (int)

    Returns:
        Image.Image
    """
    if config is None:
        if (
            horizontal_len is None
            or vertical_len is None
            or text_size is None
            or final_text_size is None
        ):
            config = GlyphForgeConfig()
            text_lines = split_text_lines(flame_text, config.max_chars_per_line)
            horizontal_len = max(len(line) for line in text_lines)
            vertical_len = len(text_lines)
            text_size = config.frame_font_size
            final_text_size = config.output_font_size
        else:
            config = GlyphForgeConfig(
                max_chars_per_line=horizontal_len,
                frame_font_size=text_size,
                output_font_size=final_text_size,
            )
    else:
        text_lines = split_text_lines(flame_text, config.max_chars_per_line)
        horizontal_len = max(len(line) for line in text_lines)
        vertical_len = len(text_lines)
        text_size = config.frame_font_size
        final_text_size = config.output_font_size

    img = text_2_img(
        flame_text,
        horizontal_len,
        vertical_len,
        text_size,
        background_color=config.background_color,
    )
    gray_list = img_2_gray_list(img)
    wb_list = gray_list_2_wb_list(gray_list)
    wb_text_list = wb_list_2_wb_text_list(wb_list, inner_text, outer_text)
    color_grid = _build_color_grid(wb_list, config)

    img = text_grid_2_img(
        wb_text_list,
        final_text_size,
        color_grid=color_grid,
        background_color=config.background_color,
    )

    return img
