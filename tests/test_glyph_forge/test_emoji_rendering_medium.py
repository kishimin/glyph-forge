import sys

import pytest
from PIL import Image, ImageDraw, ImageFont, features

from glyph_forge.services.glyph_art_renderer import (
    _render_center_frame_mask,
    render_background_image,
    render_glyph_art_image,
    render_image_frame_art_image,
    render_x_icon_image,
)
from glyph_forge.services.settings import GlyphForgeConfig
from glyph_forge.services.text_image_renderer import (
    load_font,
    render_text_grid_image,
    resolve_text_cell_size,
)

pytestmark = pytest.mark.medium


@pytest.mark.skipif(sys.platform != "linux", reason="Production runs on Linux")
def test_linux_runtime_supports_combined_emoji_shaping():
    assert features.check_feature("raqm")


def test_distinct_emoji_render_as_distinct_glyphs():
    grinning = render_text_grid_image([["😀"]], 40)
    rocket = render_text_grid_image([["🚀"]], 40)

    assert (grinning.size, grinning.tobytes()) != (rocket.size, rocket.tobytes())


def test_distinct_emoji_frames_render_as_distinct_shapes():
    grinning = _render_center_frame_mask("😀", 1, (150, 150))
    rocket = _render_center_frame_mask("🚀", 1, (150, 150))

    assert grinning.tobytes() != rocket.tobytes()


@pytest.mark.parametrize("emoji", ["😀", "🚀", "👍🏽", "👩‍🚀", "🇯🇵", "1️⃣", "❤️"])
@pytest.mark.parametrize("font_size", [10, 20, 64])
def test_emoji_fill_is_visible_colored_and_not_clipped(emoji, font_size):
    color = (17, 93, 201, 128)
    img = render_text_grid_image(
        [[emoji]], font_size, fill=color, background_color=(0, 0, 0, 0)
    )
    missing = render_text_grid_image(
        [["\U0010ffff"]], font_size, fill=color, background_color=(0, 0, 0, 0)
    )
    bounds = img.getbbox()

    assert bounds is not None
    left, top, right, bottom = bounds
    assert 0 < left < right < img.width
    assert 0 < top < bottom < img.height
    assert set(img.getdata()) == {(0, 0, 0, 0), color}
    assert img.crop(bounds).tobytes() != missing.crop(missing.getbbox()).tobytes()
    assert img.size == (resolve_text_cell_size(emoji, font_size),) * 2


def test_mixed_emoji_and_japanese_keep_separate_cells_and_colors():
    texts = ["日", "😀", "A", "🚀", "1"]
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (128, 0, 128), (0, 0, 0)]
    img = render_text_grid_image([texts], 32, color_grid=[colors])
    cell_size = img.height

    assert img.width == len(texts) * cell_size
    for column, color in enumerate(colors):
        cell = img.crop((column * cell_size, 0, (column + 1) * cell_size, cell_size))
        assert set(cell.convert("RGB").getdata()) == {(255, 255, 255), color}


@pytest.mark.parametrize("text", ["A", "日", "1", "か\u3099"])
def test_non_emoji_keep_the_existing_font(text):
    font = load_font(32)
    cell_size = resolve_text_cell_size(text, 32)
    expected_mask = Image.new("L", (cell_size, cell_size), 0)
    left, top, right, bottom = font.getbbox(text)
    ImageDraw.Draw(expected_mask).text(
        (
            (cell_size - (right - left)) / 2 - left,
            (cell_size - (bottom - top)) / 2 - top,
        ),
        text,
        font=font,
        fill=255,
    )
    expected_mask = expected_mask.point(lambda value: 255 if value else 0)

    actual = render_text_grid_image([[text]], 32, background_color=(0, 0, 0, 0))

    assert actual.getchannel("A").tobytes() == expected_mask.tobytes()


@pytest.mark.skipif(not features.check_feature("raqm"), reason="Raqm is unavailable")
@pytest.mark.parametrize("emoji", ["👩‍🚀", "🇯🇵", "👍🏽", "1️⃣"])
def test_combined_emoji_are_shaped_into_one_glyph_cell(emoji):
    font = load_font(40, emoji)
    single = load_font(40, "😀")
    img = render_text_grid_image([[emoji]], 40)

    assert font.layout_engine == ImageFont.Layout.RAQM
    assert font.getlength(emoji) == single.getlength("😀")
    assert img.width == img.height


@pytest.mark.parametrize("render", [render_x_icon_image, render_background_image])
def test_profile_images_distinguish_emoji_in_mixed_frames(render):
    config = GlyphForgeConfig(output_font_size=32)
    first = render("日😀A", "x", ".", config)
    second = render("日🚀A", "x", ".", config)

    assert first.size == second.size
    assert first.tobytes() != second.tobytes()


def test_standard_image_distinguishes_emoji_fill_characters():
    config = GlyphForgeConfig(output_font_size=32)
    first = render_glyph_art_image("KA", "😀", " ", config=config)
    second = render_glyph_art_image("KA", "🚀", " ", config=config)

    assert (first.size, first.tobytes()) != (second.size, second.tobytes())


@pytest.mark.parametrize("canvas_size", [(800, 400), (1000, 1000)])
def test_standard_emoji_frame_fits_requested_canvas_with_default_config(canvas_size):
    first = render_glyph_art_image("😀", "x", " ", max_output_size=canvas_size)
    second = render_glyph_art_image("🚀", "x", " ", max_output_size=canvas_size)

    assert first.size == second.size == canvas_size
    assert first.getbbox() is not None
    assert first.tobytes() != second.tobytes()


def test_uploaded_frame_image_distinguishes_emoji_fill_with_default_config():
    frame = Image.new("L", (2, 2), 0)
    frame.putpixel((1, 1), 255)
    first = render_image_frame_art_image(frame, "😀", " ")
    second = render_image_frame_art_image(frame, "🚀", " ")

    assert first.getbbox() is not None
    assert (first.size, first.tobytes()) != (second.size, second.tobytes())
