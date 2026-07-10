from math import ceil

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from glyph_forge.services.glyph_text_grid import binary_grid_to_text_grid
from glyph_forge.services.settings import (
    DEFAULT_BACKGROUND_SIZE,
    DEFAULT_CANVAS_GRID_DIVISIONS,
    DEFAULT_X_ICON_SIZE,
    TRANSPARENT_BACKGROUND_COLOR,
    UNCROPPED_FRAME_CELL_PADDING_RATIO,
    Color,
    GlyphForgeConfig,
)
from glyph_forge.services.text_image_renderer import (
    load_font,
    render_text_grid_image,
    render_text_image,
    split_text_lines,
)

VISIBLE_FRAME_TEXT_LINE_SPACING_RATIO = 1.1
VISIBLE_FRAME_MASK_FILTER_SIZE = 17
PROFILE_FRAME_REGION_DIVISIONS = 1.45
X_ICON_FRAME_MAX_CHARS_PER_LINE = 2


def _build_color_grid(
    binary_grid: list[list[int]],
    config: GlyphForgeConfig,
) -> list[list[Color]]:
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


def _center_region_size(canvas_size: tuple[int, int]) -> tuple[int, int]:
    return (
        max(1, canvas_size[0] // DEFAULT_CANVAS_GRID_DIVISIONS),
        max(1, canvas_size[1] // DEFAULT_CANVAS_GRID_DIVISIONS),
    )


def _profile_frame_region_size(canvas_size: tuple[int, int]) -> tuple[int, int]:
    return (
        max(1, round(canvas_size[0] / PROFILE_FRAME_REGION_DIVISIONS)),
        max(1, round(canvas_size[1] / PROFILE_FRAME_REGION_DIVISIONS)),
    )


def _with_visible_layout(config: GlyphForgeConfig) -> GlyphForgeConfig:
    safe_config = _with_uncropped_frame(config)
    visible_max_chars_per_line = _visible_max_chars_per_line(
        safe_config.max_chars_per_line,
    )
    return GlyphForgeConfig(
        max_chars_per_line=visible_max_chars_per_line,
        frame_font_size=safe_config.frame_font_size,
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


def _visible_frame_text_size(
    text_lines: list[str],
    font: ImageFont.FreeTypeFont,
) -> tuple[int, int]:
    line_sizes = [_text_bbox_size(line, font) for line in text_lines]
    line_height = max((height for _, height in line_sizes), default=font.size)
    line_spacing = max(1, round(line_height * VISIBLE_FRAME_TEXT_LINE_SPACING_RATIO))
    width = max((width for width, _ in line_sizes), default=font.size)
    height = line_height + line_spacing * (len(text_lines) - 1)
    return max(1, width), max(1, height)


def _text_bbox_size(text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    left, top, right, bottom = font.getbbox(text)
    return right - left, bottom - top


def _render_center_frame_mask(
    frame_text: str,
    max_chars_per_line: int,
    canvas_size: tuple[int, int],
) -> Image.Image:
    text_lines = split_text_lines(frame_text, max_chars_per_line)
    font_size = canvas_size[1]
    while font_size > 1:
        font = load_font(font_size)
        text_size = _visible_frame_text_size(text_lines, font)
        if text_size[0] <= canvas_size[0] and text_size[1] <= canvas_size[1]:
            return _draw_frame_mask(text_lines, font, canvas_size)
        font_size -= 1

    return _draw_frame_mask(text_lines, load_font(font_size), canvas_size)


def _draw_frame_mask(
    text_lines: list[str],
    font: ImageFont.FreeTypeFont,
    canvas_size: tuple[int, int],
) -> Image.Image:
    mask = Image.new("L", canvas_size, 0)
    draw = ImageDraw.Draw(mask)
    line_sizes = [_text_bbox_size(line, font) for line in text_lines]
    line_height = max((height for _, height in line_sizes), default=font.size)
    line_spacing = max(1, round(line_height * VISIBLE_FRAME_TEXT_LINE_SPACING_RATIO))
    content_height = line_height + line_spacing * (len(text_lines) - 1)
    y = (mask.height - content_height) / 2
    for line, (line_width, _) in zip(text_lines, line_sizes):
        left, top, _, _ = font.getbbox(line)
        x = (mask.width - line_width) / 2 - left
        draw.text((x, y - top), line, fill=255, font=font)
        y += line_spacing
    return mask.point(lambda alpha: 255 if alpha else 0)


def _expand_frame_mask(frame_mask: Image.Image) -> Image.Image:
    return frame_mask.filter(ImageFilter.MaxFilter(VISIBLE_FRAME_MASK_FILTER_SIZE))


def _paste_centered(base_img: Image.Image, overlay_img: Image.Image) -> None:
    x = (base_img.width - overlay_img.width) // 2
    y = (base_img.height - overlay_img.height) // 2
    base_img.paste(overlay_img, (x, y), overlay_img)


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

    glyph_img = render_text_grid_image(
        text_grid,
        config.output_font_size,
        color_grid=color_grid,
        background_color=(
            TRANSPARENT_BACKGROUND_COLOR
            if max_output_size is not None
            else config.background_color
        ),
    )
    if max_output_size is not None:
        centered_glyph_img = Image.new(
            "RGBA", max_output_size, TRANSPARENT_BACKGROUND_COLOR
        )
        _paste_centered(centered_glyph_img, glyph_img)
        return centered_glyph_img
    return glyph_img


def _fit_image_on_canvas(
    img: Image.Image,
    canvas_size: tuple[int, int],
    background_color: Color,
    outer_text: str,
    outer_color: Color,
    output_font_size: int,
) -> Image.Image:
    fit_size = _center_region_size(canvas_size)
    canvas = _render_outer_text_canvas(
        canvas_size,
        background_color,
        outer_text,
        outer_color,
        output_font_size,
    )
    fitted_img = img.copy()
    fitted_img.thumbnail(fit_size, Image.Resampling.NEAREST)
    _paste_centered(canvas, fitted_img)
    return canvas


def _render_profile_canvas(
    canvas_size: tuple[int, int],
    frame_text: str,
    inner_text: str,
    outer_text: str,
    config: GlyphForgeConfig,
    frame_max_chars_per_line: int,
) -> Image.Image:
    center_size = _profile_frame_region_size(canvas_size)
    center_mask = _render_center_frame_mask(
        frame_text,
        frame_max_chars_per_line,
        center_size,
    )
    center_mask = _expand_frame_mask(center_mask)
    center_left = (canvas_size[0] - center_size[0]) // 2
    center_top = (canvas_size[1] - center_size[1]) // 2

    profile_img = Image.new("RGBA", canvas_size, config.background_color)
    outer_img = _render_tiled_text_canvas(
        canvas_size,
        outer_text,
        config.outer_color,
        config.output_font_size,
        background_color=TRANSPARENT_BACKGROUND_COLOR,
    )
    inner_img = _render_tiled_text_canvas(
        canvas_size,
        inner_text,
        config.inner_color,
        config.output_font_size,
        background_color=TRANSPARENT_BACKGROUND_COLOR,
    )
    full_mask = Image.new("L", canvas_size, 0)
    full_mask.paste(center_mask, (center_left, center_top))
    outside_mask = full_mask.point(lambda alpha: 0 if alpha else 255)
    _keep_text_alpha_only_in_mask(outer_img, outside_mask)
    _keep_text_alpha_only_in_mask(inner_img, full_mask)
    profile_img.alpha_composite(outer_img)
    profile_img.alpha_composite(inner_img)
    return profile_img


def _keep_text_alpha_only_in_mask(img: Image.Image, mask: Image.Image) -> None:
    clipped_alpha = Image.new("L", img.size, 0)
    clipped_alpha.paste(img.getchannel("A"), mask=mask)
    img.putalpha(clipped_alpha)


def _render_tiled_text_canvas(
    canvas_size: tuple[int, int],
    text: str,
    color: Color,
    output_font_size: int,
    background_color: Color,
) -> Image.Image:
    if not text:
        raise ValueError("text must not be empty")

    columns = ceil(canvas_size[0] / output_font_size)
    rows = ceil(canvas_size[1] / output_font_size)
    chars = (text * (ceil(columns * rows / len(text))))[: columns * rows]
    text_grid = [
        list(chars[index : index + columns]) for index in range(0, len(chars), columns)
    ]
    img = render_text_grid_image(
        text_grid,
        output_font_size,
        fill=color,
        background_color=background_color,
    )
    return img.crop((0, 0, canvas_size[0], canvas_size[1]))


def _render_outer_text_canvas(
    canvas_size: tuple[int, int],
    background_color: Color,
    outer_text: str,
    outer_color: Color,
    output_font_size: int,
) -> Image.Image:
    if not outer_text:
        raise ValueError("outer_text must not be empty")

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
    return _render_profile_canvas(
        DEFAULT_X_ICON_SIZE,
        frame_text,
        inner_text,
        outer_text,
        _with_visible_layout(config),
        min(config.max_chars_per_line, X_ICON_FRAME_MAX_CHARS_PER_LINE),
    )


def render_background_image(
    frame_text: str,
    inner_text: str,
    outer_text: str,
    config: GlyphForgeConfig,
) -> Image.Image:
    return _render_profile_canvas(
        DEFAULT_BACKGROUND_SIZE,
        frame_text,
        inner_text,
        outer_text,
        _with_visible_layout(config),
        config.max_chars_per_line,
    )
