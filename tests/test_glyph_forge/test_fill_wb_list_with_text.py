from itertools import islice

from glyph_forge.services.fill_wb_list_with_text import (
    infinity_gen_text,
    wb_list_2_wb_text_list,
)


def test_infinity_gen_text_cycles_input_text():
    chars = list(islice(infinity_gen_text("ab"), 5))

    assert chars == ["a", "b", "a", "b", "a"]


def test_wb_list_2_wb_text_list_fills_black_with_inner_and_white_with_outer():
    wb_text_list = wb_list_2_wb_text_list(
        [
            [0, 1, 0],
            [1, 0, 1],
        ],
        inner_text="ab",
        outer_text="xy",
    )

    assert wb_text_list == [
        ["a", "x", "b"],
        ["y", "a", "x"],
    ]
