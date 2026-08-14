from itertools import islice

import pytest

from glyph_forge.services.glyph_text_grid import binary_grid_to_text_grid, cycle_text


def test_cycle_text_cycles_input_text():
    chars = list(islice(cycle_text("ab"), 5))

    assert chars == ["a", "b", "a", "b", "a"]


def test_cycle_text_keeps_multicodepoint_graphemes_together():
    astronaut = "👩‍🚀"

    graphemes = list(islice(cycle_text(astronaut + "A"), 3))

    assert graphemes == [astronaut, "A", astronaut]


def test_binary_grid_to_text_grid_fills_black_with_inner_and_white_with_outer():
    text_grid = binary_grid_to_text_grid(
        [
            [0, 1, 0],
            [1, 0, 1],
        ],
        inner_text="ab",
        outer_text="xy",
    )

    assert text_grid == [
        ["a", "x", "b"],
        ["y", "a", "x"],
    ]


def test_cycle_text_rejects_empty_text():
    with pytest.raises(ValueError, match="text must not be empty"):
        next(cycle_text(""))


def test_binary_grid_to_text_grid_rejects_empty_inner_text():
    with pytest.raises(ValueError, match="inner_text must not be empty"):
        binary_grid_to_text_grid([[0]], inner_text="", outer_text="x")


def test_binary_grid_to_text_grid_rejects_empty_outer_text():
    with pytest.raises(ValueError, match="outer_text must not be empty"):
        binary_grid_to_text_grid([[1]], inner_text="x", outer_text="")
