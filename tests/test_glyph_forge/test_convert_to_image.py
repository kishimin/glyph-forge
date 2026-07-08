from glyph_forge.services.convert_to_image import text_2_text_img
from glyph_forge.services.settings import GlyphForgeConfig


def test_text_2_text_img_returns_image_with_expected_size():
    img = text_2_text_img("カニ", "エビ", " ", 2, 1, 20, 15)

    assert img.size == (600, 300)


def test_text_2_text_img_draws_non_blank_result():
    img = text_2_text_img("A", "x", " ", 1, 1, 20, 10)

    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)

    assert colors is not None
    assert len(colors) > 1


def test_text_2_text_img_uses_config_to_wrap_frame_text():
    img = text_2_text_img(
        "ABCDEF",
        "x",
        " ",
        config=GlyphForgeConfig(
            max_chars_per_line=5,
            frame_font_size=10,
            output_font_size=2,
        ),
    )

    assert img.size == (100, 40)


def test_text_2_text_img_can_color_inner_and_outer_text_separately():
    img = text_2_text_img(
        "A",
        "x",
        ".",
        config=GlyphForgeConfig(
            max_chars_per_line=1,
            frame_font_size=40,
            output_font_size=10,
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
