import pytest

from glyph_forge.services.glyph_art_renderer import _render_center_frame_mask
from glyph_forge.services.text_image_renderer import render_text_grid_image

pytestmark = pytest.mark.medium


def test_distinct_emoji_render_as_distinct_glyphs():
    grinning = render_text_grid_image([["😀"]], 40)
    rocket = render_text_grid_image([["🚀"]], 40)

    assert (grinning.size, grinning.tobytes()) != (rocket.size, rocket.tobytes())


def test_distinct_emoji_frames_render_as_distinct_shapes():
    grinning = _render_center_frame_mask("😀", 1, (150, 150))
    rocket = _render_center_frame_mask("🚀", 1, (150, 150))

    assert grinning.tobytes() != rocket.tobytes()
