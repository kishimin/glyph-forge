from itertools import islice

from glyph_forge.services.glyph_text_grid import binary_grid_to_text_grid, cycle_text


def test_cycle_text_cycles_input_text():
    chars = list(islice(cycle_text("ab"), 5))

    assert chars == ["a", "b", "a", "b", "a"]


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
