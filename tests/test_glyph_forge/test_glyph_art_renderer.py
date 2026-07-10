from glyph_forge.services.glyph_art_renderer import (
    _fit_image_on_canvas,
    _frame_image_to_binary_grid,
    render_background_image,
    render_glyph_art_image,
    render_x_icon_image,
)
from glyph_forge.services.settings import (
    DEFAULT_BACKGROUND_SIZE,
    DEFAULT_CANVAS_GRID_DIVISIONS,
    DEFAULT_X_ICON_SIZE,
    GlyphForgeConfig,
)


def _sample_config() -> GlyphForgeConfig:
    return GlyphForgeConfig(
        max_chars_per_line=5,
        frame_font_size=40,
        output_font_size=18,
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


def test_render_glyph_art_image_uses_configured_background_color():
    img = render_glyph_art_image(
        "FRAME_TEXT_SAMPLE",
        "INNER_TEXT_SAMPLE",
        "OUTER_TEXT_SAMPLE",
        config=_sample_config(),
    )

    assert img.getpixel((0, 0)) == (255, 255, 255, 255)


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


def test_render_x_icon_image_does_not_mix_outer_color_into_inner_text():
    img = render_x_icon_image(
        "FRAME_TEXT_SAMPLE",
        "INNER_TEXT_SAMPLE",
        "OUTER_TEXT_SAMPLE",
        GlyphForgeConfig(
            max_chars_per_line=5,
            frame_font_size=40,
            output_font_size=24,
            inner_color=(255, 0, 0),
            outer_color=(0, 0, 255),
        ),
    )

    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)

    assert colors is not None
    assert not any(_has_inner_and_outer_channels(color) for _, color in colors)


def test_render_x_icon_image_uses_inner_text_to_draw_frame_shape(monkeypatch):
    captured_calls = []

    def capture_grid(text_grid, font_size, color_grid=None, **kwargs):
        captured_calls.append(
            {
                "text_grid": text_grid,
                "fill": kwargs["fill"],
            }
        )
        return _solid_canvas(DEFAULT_X_ICON_SIZE, kwargs["background_color"])

    monkeypatch.setattr(
        "glyph_forge.services.glyph_art_renderer.render_text_grid_image",
        capture_grid,
    )

    render_x_icon_image("ABCDE", "x", "o", _sample_config())

    inner_call = next(
        call for call in captured_calls if call["fill"] == _sample_config().inner_color
    )
    frame_cells = _grid_positions_containing(inner_call["text_grid"], set("x"))
    all_profile_text = "".join(
        cell for call in captured_calls for row in call["text_grid"] for cell in row
    )

    assert frame_cells
    assert set("ABCDE").isdisjoint(all_profile_text)


def test_render_x_icon_image_keeps_inner_text_readable_in_center_region():
    img = render_x_icon_image("FRAME", "INNER", "OUTER", _sample_config())

    assert _inner_side_color_ratio(_center_region(img)) > 0.03


def test_render_x_icon_image_uses_readable_uniform_profile_text_size(monkeypatch):
    captured_font_sizes = []

    def capture_grid(text_grid, font_size, **kwargs):
        captured_font_sizes.append(font_size)
        return _solid_canvas(DEFAULT_X_ICON_SIZE, (255, 255, 255))

    monkeypatch.setattr(
        "glyph_forge.services.glyph_art_renderer.render_text_grid_image",
        capture_grid,
    )

    render_x_icon_image("ABCDE", "x", "o", _sample_config())

    assert captured_font_sizes == [14, 14]


def test_render_x_icon_image_uses_only_configured_text_colors():
    img = render_x_icon_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config()
    )

    assert _image_color_set(img) <= {
        (255, 255, 255),
        _sample_config().inner_color,
        _sample_config().outer_color,
    }


def test_render_background_image_uses_only_configured_text_colors():
    img = render_background_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config()
    )

    assert _image_color_set(img) <= {
        (255, 255, 255),
        _sample_config().inner_color,
        _sample_config().outer_color,
    }


def test_frame_binary_grid_keeps_antialiased_frame_pixels_inside_inner_text():
    assert _frame_image_to_binary_grid(
        _fake_frame_image([(255, 255, 255), (254, 254, 254)])
    ) == [[1, 0]]


def test_render_x_icon_image_uses_icon_canvas_without_edge_cropping():
    img = render_x_icon_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config()
    )

    assert img.size == DEFAULT_X_ICON_SIZE
    assert _min_inner_margin(img) > 0
    assert _inner_bounds_overlap_center_region(img)
    assert _inner_side_color_ratio(img) > 0.001
    assert _outer_side_color_ratio(img) > 0.01


def test_render_x_icon_image_uses_configured_background_color():
    img = render_x_icon_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config()
    )

    assert img.getpixel((0, 0)) == (255, 255, 255, 255)


def test_render_x_icon_image_does_not_draw_black_frame_text():
    img = render_x_icon_image("ABCD", "x", "o", _sample_config())

    assert _frame_text_color_ratio(img) == 0


def test_render_x_icon_image_draws_frame_text_without_crushing():
    img = render_x_icon_image("ABCD", "x", "o", _sample_config())

    left, right, top, bottom = _inner_bounds(_center_region(img))
    _, center_height = _center_region_size(img)

    assert right - left + 1 > 80
    assert bottom - top + 1 >= center_height * 0.25


def test_render_x_icon_image_enlarges_profile_frame_shape():
    img = render_x_icon_image("ABCD", "x", "o", _sample_config())

    left, right, top, bottom = _inner_bounds(_center_region(img))
    width = right - left + 1
    height = bottom - top + 1

    assert width >= 170
    assert height >= width * 0.3


def test_render_x_icon_image_wraps_frame_shape_for_icon_readability():
    img = render_x_icon_image("ABCD", "x", "o", _sample_config())

    left, right, top, bottom = _inner_bounds(img)
    width = right - left + 1
    height = bottom - top + 1

    assert height >= width * 0.8


def test_render_background_image_keeps_five_character_frame_line():
    img = render_background_image("ABCD", "x", "o", _sample_config())

    left, right, top, bottom = _inner_bounds(img)
    width = right - left + 1
    height = bottom - top + 1

    assert width > height


def test_render_x_icon_image_keeps_outer_text_visible_in_center_region():
    img = render_x_icon_image("ABCD", "x", "o", _sample_config())

    assert _outer_side_color_ratio(_center_region(img)) > 0.01


def test_render_background_image_uses_background_canvas_without_edge_cropping():
    img = render_background_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config()
    )

    assert img.size == DEFAULT_BACKGROUND_SIZE
    assert _min_inner_margin(img) > 0
    assert _inner_bounds_overlap_center_region(img)
    assert _inner_side_color_ratio(img) > 0.001
    assert _outer_side_color_ratio(img) > 0.01


def test_render_background_image_uses_configured_background_color():
    img = render_background_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config()
    )

    assert img.getpixel((0, 0)) == (255, 255, 255, 255)


def test_render_glyph_art_image_wraps_frame_text_at_five_characters():
    five_chars = render_glyph_art_image(
        "ABCDE",
        "x",
        "o",
        config=GlyphForgeConfig(
            max_chars_per_line=5,
            frame_font_size=20,
            output_font_size=10,
            inner_color=(255, 183, 197),
            outer_color=(255, 0, 0),
        ),
    )
    six_chars = render_glyph_art_image(
        "ABCDEF",
        "x",
        "o",
        config=GlyphForgeConfig(
            max_chars_per_line=5,
            frame_font_size=20,
            output_font_size=10,
            inner_color=(255, 183, 197),
            outer_color=(255, 0, 0),
        ),
    )

    assert six_chars.height > five_chars.height


def test_render_x_icon_image_fills_margin_with_outer_text():
    img = render_x_icon_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config()
    )

    assert _outer_side_color_ratio(_top_band(img)) > 0.01


def test_render_x_icon_image_keeps_outer_text_visible_on_background():
    img = render_x_icon_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config()
    )

    assert _outer_side_color_ratio(img) > 0.01


def test_render_background_image_keeps_outer_text_visible_on_background():
    img = render_background_image(
        "FRAME_TEXT_SAMPLE", "INNER_TEXT_SAMPLE", "OUTER_TEXT_SAMPLE", _sample_config()
    )

    assert _outer_side_color_ratio(img) > 0.01


def test_render_glyph_art_image_keeps_outer_text_visible_on_background():
    img = render_glyph_art_image(
        "FRAME_TEXT_SAMPLE",
        "INNER_TEXT_SAMPLE",
        "OUTER_TEXT_SAMPLE",
        config=_sample_config(),
    )

    assert _outer_side_color_ratio(img) > 0.01


def test_fit_image_on_canvas_keeps_outer_text_font_size_constant(monkeypatch):
    captured_font_sizes = []
    source_img = render_glyph_art_image(
        "FRAME_TEXT_SAMPLE",
        "INNER_TEXT_SAMPLE",
        "OUTER_TEXT_SAMPLE",
        config=GlyphForgeConfig(
            max_chars_per_line=5,
            frame_font_size=40,
            output_font_size=40,
            inner_color=(255, 183, 197),
            outer_color=(255, 0, 0),
        ),
    )

    def capture_canvas(
        canvas_size,
        background_color,
        outer_text,
        outer_color,
        output_font_size,
    ):
        captured_font_sizes.append(output_font_size)
        return _solid_canvas(canvas_size, background_color)

    monkeypatch.setattr(
        "glyph_forge.services.glyph_art_renderer._render_outer_text_canvas",
        capture_canvas,
    )

    _fit_image_on_canvas(
        source_img,
        (120, 120),
        (100, 100, 100),
        "OUTER_TEXT_SAMPLE",
        (255, 0, 0),
        40,
    )

    assert captured_font_sizes == [40]


def _fake_frame_image(colors):
    from PIL import Image

    img = Image.new("RGB", (len(colors), 1))
    for x, color in enumerate(colors):
        img.putpixel((x, 0), color)
    return img


def _solid_canvas(canvas_size, background_color):
    from PIL import Image

    return Image.new("RGBA", canvas_size, background_color)


def _grid_positions_containing(text_grid, target_chars: set[str]):
    return [
        (row_index, column_index)
        for row_index, row in enumerate(text_grid)
        for column_index, cell_text in enumerate(row)
        if cell_text in target_chars
    ]


def _min_inner_margin(img) -> int:
    rgb_img = img.convert("RGB")
    drawn_pixels = [
        (x, y)
        for y in range(img.height)
        for x in range(img.width)
        if _is_inner_side_color(rgb_img.getpixel((x, y)))
    ]
    left = min(x for x, _ in drawn_pixels)
    right = max(x for x, _ in drawn_pixels)
    top = min(y for _, y in drawn_pixels)
    bottom = max(y for _, y in drawn_pixels)
    return min(left, img.width - right - 1, top, img.height - bottom - 1)


def _inner_bounds_are_inside_center_region(img) -> bool:
    left, right, top, bottom = _inner_bounds(img)
    center_left = img.width // DEFAULT_CANVAS_GRID_DIVISIONS
    center_right = img.width - center_left
    center_top = img.height // DEFAULT_CANVAS_GRID_DIVISIONS
    center_bottom = img.height - center_top
    return (
        center_left <= left
        and right < center_right
        and center_top <= top
        and bottom < center_bottom
    )


def _inner_bounds_overlap_center_region(img) -> bool:
    left, right, top, bottom = _inner_bounds(img)
    center_left = img.width // DEFAULT_CANVAS_GRID_DIVISIONS
    center_right = img.width - center_left
    center_top = img.height // DEFAULT_CANVAS_GRID_DIVISIONS
    center_bottom = img.height - center_top
    return (
        left < center_right
        and right >= center_left
        and top < center_bottom
        and bottom >= center_top
    )


def _center_region_size(img) -> tuple[int, int]:
    return (
        img.width // DEFAULT_CANVAS_GRID_DIVISIONS,
        img.height // DEFAULT_CANVAS_GRID_DIVISIONS,
    )


def _inner_bounds(img):
    rgb_img = img.convert("RGB")
    drawn_pixels = [
        (x, y)
        for y in range(img.height)
        for x in range(img.width)
        if _is_inner_side_color(rgb_img.getpixel((x, y)))
    ]
    return (
        min(x for x, _ in drawn_pixels),
        max(x for x, _ in drawn_pixels),
        min(y for _, y in drawn_pixels),
        max(y for _, y in drawn_pixels),
    )


def _inner_side_color_ratio(img) -> float:
    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)
    assert colors is not None
    inner_pixels = sum(
        count
        for count, (red, green, blue) in colors
        if _is_inner_side_color((red, green, blue))
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


def _top_band(img):
    return img.crop((0, 0, img.width, max(1, img.height // 10)))


def _center_region(img):
    center_left = img.width // DEFAULT_CANVAS_GRID_DIVISIONS
    center_right = img.width - center_left
    center_top = img.height // DEFAULT_CANVAS_GRID_DIVISIONS
    center_bottom = img.height - center_top
    return img.crop((center_left, center_top, center_right, center_bottom))


def _is_inner_side_color(color) -> bool:
    red, green, blue = color
    return red > 220 and green > 100 and 100 < blue < 230


def _has_inner_and_outer_channels(color) -> bool:
    red, green, blue = color
    return red > 0 and blue > 0 and green == 0


def _is_frame_text_color(color) -> bool:
    red, green, blue = color
    return red < 40 and green < 40 and blue < 40


def _frame_text_color_ratio(img) -> float:
    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)
    assert colors is not None
    frame_text_pixels = sum(
        count for count, color in colors if _is_frame_text_color(color)
    )
    return frame_text_pixels / (img.width * img.height)


def _image_color_set(img) -> set[tuple[int, int, int]]:
    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)
    assert colors is not None
    return {color for _, color in colors}
