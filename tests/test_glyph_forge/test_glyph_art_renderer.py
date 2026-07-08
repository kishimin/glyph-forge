from glyph_forge.services.glyph_art_renderer import (
    render_background_image,
    render_glyph_art_image,
    render_x_icon_image,
)
from glyph_forge.services.settings import (
    DEFAULT_BACKGROUND_SIZE,
    DEFAULT_X_ICON_SIZE,
    GlyphForgeConfig,
)


def _sample_config() -> GlyphForgeConfig:
    return GlyphForgeConfig(
        max_chars_per_line=5,
        frame_font_size=40,
        output_font_size=24,
        inner_color=(255, 183, 197),
        outer_color=(255, 0, 0),
    )


def test_render_glyph_art_image_returns_non_blank_result():
    img = render_glyph_art_image(
        "FRAME_TEXT_SAMPLE",
        "INNER_TEXT_SAMPLE",
        "OUTER_TEXT_SAMPLE",
        config=_sample_config(),
    )

    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)

    assert colors is not None
    assert len(colors) > 1


def test_render_glyph_art_image_can_color_inner_and_outer_text_separately():
    img = render_glyph_art_image(
        "A",
        "x",
        ".",
        config=GlyphForgeConfig(
            max_chars_per_line=1,
            frame_font_size=40,
            output_font_size=24,
            inner_color=(255, 0, 0),
            outer_color=(0, 0, 255),
        ),
    )

    colors = {
        color
        for _, color in img.convert("RGB").getcolors(maxcolors=img.width * img.height)
    }

    assert any(red > 200 and green < 120 and blue < 120 for red, green, blue in colors)
    assert any(blue > 200 and red < 120 and green < 120 for red, green, blue in colors)


def test_render_x_icon_image_uses_icon_canvas_without_edge_cropping():
    img = render_x_icon_image("FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config())

    assert img.size == DEFAULT_X_ICON_SIZE
    assert _min_drawn_margin(img) > 0
    assert _drawn_height_ratio(img) > 0.35
    assert _inner_side_color_ratio(img) > 0.01
    assert _outer_side_color_ratio(img) > 0.01


def test_render_background_image_uses_background_canvas_without_edge_cropping():
    img = render_background_image("FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config())

    assert img.size == DEFAULT_BACKGROUND_SIZE
    assert _min_drawn_margin(img) > 0
    assert _drawn_height_ratio(img) > 0.35
    assert _inner_side_color_ratio(img) > 0.01
    assert _outer_side_color_ratio(img) > 0.01


def test_render_x_icon_image_fills_white_space_with_outer_side():
    img = render_x_icon_image("FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config())

    assert _has_no_white_pixels(img)


def test_render_background_image_fills_white_space_with_outer_side():
    img = render_background_image("FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config())

    assert _has_no_white_pixels(img)


def test_render_glyph_art_image_fills_white_space_with_outer_side():
    img = render_glyph_art_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", config=_sample_config()
    )

    assert _has_no_white_pixels(img)


def _min_drawn_margin(img) -> int:
    rgb_img = img.convert("RGB")
    background_color = rgb_img.getpixel((0, 0))
    drawn_pixels = [
        (x, y)
        for y in range(img.height)
        for x in range(img.width)
        if rgb_img.getpixel((x, y)) != background_color
    ]
    left = min(x for x, _ in drawn_pixels)
    right = max(x for x, _ in drawn_pixels)
    top = min(y for _, y in drawn_pixels)
    bottom = max(y for _, y in drawn_pixels)
    return min(left, img.width - right - 1, top, img.height - bottom - 1)


def _has_no_white_pixels(img) -> bool:
    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)
    assert colors is not None
    return all(color != (255, 255, 255) for _, color in colors)


def _drawn_height_ratio(img) -> float:
    rgb_img = img.convert("RGB")
    background_color = rgb_img.getpixel((0, 0))
    y_values = [
        y
        for y in range(img.height)
        for x in range(img.width)
        if rgb_img.getpixel((x, y)) != background_color
    ]
    return (max(y_values) - min(y_values) + 1) / img.height


def _inner_side_color_ratio(img) -> float:
    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)
    assert colors is not None
    inner_pixels = sum(
        count
        for count, (red, green, blue) in colors
        if red > 220 and green > 100 and blue > 100
    )
    return inner_pixels / (img.width * img.height)


def _outer_side_color_ratio(img) -> float:
    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)
    assert colors is not None
    outer_pixels = sum(
        count
        for count, (red, green, blue) in colors
        if red > 200 and green < 80 and blue < 80
    )
    return outer_pixels / (img.width * img.height)
