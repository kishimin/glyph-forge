from glyph_forge.services.text_image_renderer import render_text_image


def _drawn_bounds(img):
    rgb_img = img.convert("RGB")
    drawn_pixels = [
        (x, y)
        for y in range(img.height)
        for x in range(img.width)
        if rgb_img.getpixel((x, y)) != (255, 255, 255)
    ]
    return (
        min(x for x, _ in drawn_pixels),
        max(x for x, _ in drawn_pixels),
        min(y for _, y in drawn_pixels),
        max(y for _, y in drawn_pixels),
    )


def test_render_text_image_returns_image_with_grid_size():
    img = render_text_image(
        input_text="ABCDEF",
        column_count=2,
        row_count=3,
        font_size=50,
    )

    assert img.size == (100, 150)


def test_render_text_image_draws_text_on_white_background():
    img = render_text_image(
        input_text="A",
        column_count=1,
        row_count=1,
        font_size=50,
    )

    colors = img.convert("RGB").getcolors(maxcolors=img.width * img.height)

    assert colors is not None
    assert len(colors) > 1


def test_render_text_image_centers_character_in_cell():
    img = render_text_image(
        input_text="A",
        column_count=1,
        row_count=1,
        font_size=100,
    )

    left, right, _, _ = _drawn_bounds(img)

    assert left > 10
    assert img.width - right - 1 > 10


def test_render_text_image_adds_padding_to_prevent_frame_text_cropping():
    img = render_text_image(
        input_text="A",
        column_count=1,
        row_count=1,
        font_size=100,
        cell_padding_ratio=0.2,
    )

    left, right, top, bottom = _drawn_bounds(img)

    assert min(left, img.width - right - 1, top, img.height - bottom - 1) > 0
