from glyph_forge.services.convert_text_to_image import text_2_img


def test_text_2_img_returns_image_with_grid_size():
    img = text_2_img(input_text="勝利友情努力", horizontal_len=2, vertical_len=3, text_size=50)

    assert img.size == (100, 150)


def test_text_2_img_draws_text_on_white_background():
    img = text_2_img(input_text="A", horizontal_len=1, vertical_len=1, text_size=50)

    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)

    assert colors is not None
    assert len(colors) > 1
