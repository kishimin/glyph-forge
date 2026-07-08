from math import ceil, floor

from PIL import Image

from glyph_forge.services.glyph_text_grid import binary_grid_to_text_grid
from glyph_forge.services.settings import (
    DEFAULT_BACKGROUND_SIZE,
    DEFAULT_CANVAS_GRID_DIVISIONS,
    DEFAULT_X_ICON_SIZE,
    MIN_READABLE_OUTPUT_FONT_SIZE,
    UNCROPPED_FRAME_CELL_PADDING_RATIO,
    GlyphForgeConfig,
)
from glyph_forge.services.text_image_renderer import (
    render_text_grid_image,
    render_text_image,
    split_text_lines,
)


def _build_color_grid(
    binary_grid: list[list[int]],
    config: GlyphForgeConfig,
) -> list[list[tuple[int, int, int]]]:
    return [
        [
            config.outer_color if binary_value == 1 else config.inner_color
            for binary_value in binary_row
        ]
        for binary_row in binary_grid
    ]


def _with_uncropped_frame(config: GlyphForgeConfig) -> GlyphForgeConfig:
    return GlyphForgeConfig(
        max_chars_per_line=config.max_chars_per_line,
        frame_font_size=config.frame_font_size,
        output_font_size=config.output_font_size,
        frame_cell_padding_ratio=max(
            config.frame_cell_padding_ratio,
            UNCROPPED_FRAME_CELL_PADDING_RATIO,
        ),
        inner_color=config.inner_color,
        outer_color=config.outer_color,
        background_color=config.background_color,
    )


def _visible_max_chars_per_line(
    configured_max_chars_per_line: int,
) -> int:
    return configured_max_chars_per_line


def _visible_frame_font_size(
    frame_text: str,
    canvas_size: tuple[int, int],
    max_chars_per_line: int,
    configured_frame_font_size: int,
    frame_cell_padding_ratio: float,
) -> int:
    row_count = ceil(len(frame_text) / max_chars_per_line)
    fit_width = canvas_size[0]
    fit_height = canvas_size[1]
    padded_cell_ratio = 1 + frame_cell_padding_ratio * 2
    max_size_by_width = fit_width / (
        max_chars_per_line * MIN_READABLE_OUTPUT_FONT_SIZE * padded_cell_ratio
    )
    max_size_by_height = fit_height / (
        row_count * MIN_READABLE_OUTPUT_FONT_SIZE * padded_cell_ratio
    )
    visible_font_size = floor(min(max_size_by_width, max_size_by_height))
    return max(1, min(configured_frame_font_size, visible_font_size))


def _center_region_size(canvas_size: tuple[int, int]) -> tuple[int, int]:
    return (
        max(1, canvas_size[0] // DEFAULT_CANVAS_GRID_DIVISIONS),
        max(1, canvas_size[1] // DEFAULT_CANVAS_GRID_DIVISIONS),
    )


def _with_visible_layout(
    frame_text: str,
    canvas_size: tuple[int, int],
    config: GlyphForgeConfig,
) -> GlyphForgeConfig:
    safe_config = _with_uncropped_frame(config)
    visible_max_chars_per_line = _visible_max_chars_per_line(
        safe_config.max_chars_per_line,
    )
    return GlyphForgeConfig(
        max_chars_per_line=visible_max_chars_per_line,
        frame_font_size=_visible_frame_font_size(
            frame_text,
            canvas_size,
            visible_max_chars_per_line,
            safe_config.frame_font_size,
            safe_config.frame_cell_padding_ratio,
        ),
        output_font_size=safe_config.output_font_size,
        frame_cell_padding_ratio=safe_config.frame_cell_padding_ratio,
        inner_color=safe_config.inner_color,
        outer_color=safe_config.outer_color,
        background_color=safe_config.background_color,
    )


def _frame_image_to_binary_grid(frame_img: Image.Image) -> list[list[int]]:
    rgb_img = frame_img.convert("RGB")
    background_color = rgb_img.getpixel((0, 0))
    return [
        [
            1 if rgb_img.getpixel((x, y)) == background_color else 0
            for x in range(rgb_img.width)
        ]
        for y in range(rgb_img.height)
    ]


def _fit_frame_image_to_output_grid(
    frame_img: Image.Image,
    max_output_size: tuple[int, int],
    output_font_size: int,
) -> Image.Image:
    max_grid_size = (
        max(1, max_output_size[0] // output_font_size),
        max(1, max_output_size[1] // output_font_size),
    )
    if frame_img.width <= max_grid_size[0] and frame_img.height <= max_grid_size[1]:
        return frame_img

    fitted_img = frame_img.copy()
    fitted_img.thumbnail(max_grid_size, Image.Resampling.NEAREST)
    return fitted_img


def render_glyph_art_image(
    frame_text: str,
    inner_text: str,
    outer_text: str,
    *,
    config: GlyphForgeConfig | None = None,
    max_output_size: tuple[int, int] | None = None,
) -> Image.Image:
    if config is None:
        config = GlyphForgeConfig()

    text_lines = split_text_lines(frame_text, config.max_chars_per_line)
    column_count = max(len(line) for line in text_lines)
    row_count = len(text_lines)

    frame_img = render_text_image(
        frame_text,
        column_count,
        row_count,
        config.frame_font_size,
        background_color=config.background_color,
        cell_padding_ratio=config.frame_cell_padding_ratio,
    )
    if max_output_size is not None:
        frame_img = _fit_frame_image_to_output_grid(
            frame_img,
            max_output_size,
            config.output_font_size,
        )
    binary_grid = _frame_image_to_binary_grid(frame_img)
    text_grid = binary_grid_to_text_grid(binary_grid, inner_text, outer_text)
    color_grid = _build_color_grid(binary_grid, config)

    return render_text_grid_image(
        text_grid,
        config.output_font_size,
        color_grid=color_grid,
        background_color=config.background_color,
    )


def _fit_image_on_canvas(
    img: Image.Image,
    canvas_size: tuple[int, int],
    background_color: tuple[int, int, int] | tuple[int, int, int, int],
    outer_text: str,
    outer_color: tuple[int, int, int],
    output_font_size: int,
) -> Image.Image:
    fit_size = _center_region_size(canvas_size)
    scale = min(fit_size[0] / img.width, fit_size[1] / img.height, 1)
    fitted_output_font_size = max(1, round(output_font_size * scale))
    canvas = _render_outer_text_canvas(
        canvas_size,
        background_color,
        outer_text,
        outer_color,
        fitted_output_font_size,
    )
    fitted_img = img.copy()
    fitted_img.thumbnail(fit_size, Image.Resampling.NEAREST)
    x = (canvas.width - fitted_img.width) // 2
    y = (canvas.height - fitted_img.height) // 2
    canvas.paste(fitted_img, (x, y), fitted_img)
    return canvas


def _render_outer_text_canvas(
    canvas_size: tuple[int, int],
    background_color: tuple[int, int, int] | tuple[int, int, int, int],
    outer_text: str,
    outer_color: tuple[int, int, int],
    output_font_size: int,
) -> Image.Image:
    columns = ceil(canvas_size[0] / output_font_size)
    rows = ceil(canvas_size[1] / output_font_size)
    outer_chars = (outer_text * (ceil(columns * rows / len(outer_text))))[
        : columns * rows
    ]
    text_grid = [
        list(outer_chars[index : index + columns])
        for index in range(0, len(outer_chars), columns)
    ]
    background = render_text_grid_image(
        text_grid,
        output_font_size,
        fill=outer_color,
        background_color=background_color,
    )
    return background.crop((0, 0, canvas_size[0], canvas_size[1]))


def render_x_icon_image(
    frame_text: str,
    inner_text: str,
    outer_text: str,
    config: GlyphForgeConfig,
) -> Image.Image:
    art = render_glyph_art_image(
        frame_text,
        inner_text,
        outer_text,
        config=_with_visible_layout(
            frame_text,
            _center_region_size(DEFAULT_X_ICON_SIZE),
            config,
        ),
        max_output_size=_center_region_size(DEFAULT_X_ICON_SIZE),
    )
    return _fit_image_on_canvas(
        art,
        DEFAULT_X_ICON_SIZE,
        config.background_color,
        outer_text,
        config.outer_color,
        config.output_font_size,
    )


def render_background_image(
    frame_text: str,
    inner_text: str,
    outer_text: str,
    config: GlyphForgeConfig,
) -> Image.Image:
    art = render_glyph_art_image(
        frame_text,
        inner_text,
        outer_text,
        config=_with_visible_layout(
            frame_text,
            _center_region_size(DEFAULT_BACKGROUND_SIZE),
            config,
        ),
        max_output_size=_center_region_size(DEFAULT_BACKGROUND_SIZE),
    )
    return _fit_image_on_canvas(
        art,
        DEFAULT_BACKGROUND_SIZE,
        config.background_color,
        outer_text,
        config.outer_color,
        config.output_font_size,
    )
