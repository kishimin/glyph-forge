import pytest
from PIL import Image

from glyph_forge.services import text_image_renderer
from glyph_forge.services.text_image_renderer import render_text_image, split_text_lines


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


def test_render_text_image_keeps_multicodepoint_graphemes_in_one_cell(monkeypatch):
    astronaut = "👩‍🚀"
    captured_grid = None

    def capture_grid(text_grid, *args, **kwargs):
        nonlocal captured_grid
        captured_grid = text_grid
        return Image.new("RGBA", (1, 1))

    monkeypatch.setattr(text_image_renderer, "render_text_grid_image", capture_grid)

    render_text_image(
        input_text=astronaut + "A",
        column_count=2,
        row_count=1,
        font_size=10,
    )

    assert captured_grid == [[astronaut, "A"]]


def test_split_text_lines_rejects_empty_text():
    with pytest.raises(ValueError, match="input_text must not be empty"):
        split_text_lines("", 5)


def test_split_text_lines_keeps_multicodepoint_graphemes_together():
    astronaut = "👩‍🚀"

    lines = split_text_lines(astronaut * 3, 2)

    assert lines == [astronaut * 2, astronaut]


def test_render_text_image_rejects_empty_text():
    with pytest.raises(ValueError, match="input_text must not be empty"):
        render_text_image("", column_count=1, row_count=1, font_size=20)
