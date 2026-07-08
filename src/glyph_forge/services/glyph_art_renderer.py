from PIL import Image

from glyph_forge.services.glyph_text_grid import binary_grid_to_text_grid
from glyph_forge.services.image_threshold import (
    grayscale_grid_to_binary_grid,
    image_to_grayscale_grid,
)
from glyph_forge.services.settings import (
    DEFAULT_BACKGROUND_SIZE,
    DEFAULT_CANVAS_MARGIN_RATIO,
    DEFAULT_X_ICON_SIZE,
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


def render_glyph_art_image(
    frame_text: str,
    inner_text: str,
    outer_text: str,
    *,
    config: GlyphForgeConfig | None = None,
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
    grayscale_grid = image_to_grayscale_grid(frame_img)
    binary_grid = grayscale_grid_to_binary_grid(grayscale_grid)
    text_grid = binary_grid_to_text_grid(binary_grid, inner_text, outer_text)
    color_grid = _build_color_grid(binary_grid, config)

    return render_text_grid_image(
        text_grid,
        config.output_font_size,
        color_grid=color_grid,
        background_color=config.outer_color,
    )


def _fit_image_on_canvas(
    img: Image.Image,
    canvas_size: tuple[int, int],
    background_color: tuple[int, int, int],
    margin_ratio: float = DEFAULT_CANVAS_MARGIN_RATIO,
) -> Image.Image:
    canvas = Image.new("RGBA", canvas_size, background_color)
    fitted_img = img.copy()
    margin_x = round(canvas.width * margin_ratio)
    margin_y = round(canvas.height * margin_ratio)
    fit_size = (
        max(1, canvas.width - margin_x * 2),
        max(1, canvas.height - margin_y * 2),
    )
    fitted_img.thumbnail(fit_size, Image.Resampling.LANCZOS)
    x = (canvas.width - fitted_img.width) // 2
    y = (canvas.height - fitted_img.height) // 2
    canvas.paste(fitted_img, (x, y), fitted_img)
    return canvas


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
        config=_with_uncropped_frame(config),
    )
    return _fit_image_on_canvas(art, DEFAULT_X_ICON_SIZE, config.outer_color)


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
        config=_with_uncropped_frame(config),
    )
    return _fit_image_on_canvas(art, DEFAULT_BACKGROUND_SIZE, config.outer_color)
