from glyph_forge.services.convert_to_image import text_2_text_img


def test_text_2_text_img_returns_image_with_expected_size():
    img = text_2_text_img("カニ", "エビ", " ", 2, 1, 20, 15)

    assert img.size == (600, 300)


def test_text_2_text_img_draws_non_blank_result():
    img = text_2_text_img("A", "x", " ", 1, 1, 20, 10)

    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)

    assert colors is not None
    assert len(colors) > 1
