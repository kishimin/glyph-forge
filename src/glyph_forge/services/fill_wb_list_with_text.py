from itertools import cycle
from typing import Generator


def infinity_gen_text(text: str) -> Generator[str, None, None]:
    """A generator that extracts characters from a string one by one.
        It repeats using a semi-infinite loop.

    Args:
        text (str)

    Yields:
        Generator[str, None, None]
    """
    yield from cycle(text)


def wb_list_2_wb_text_list(
    input_wb_list: list[list[int]], inner_text: str, outer_text: str
) -> list[list[str]]:
    """Return a two-dimensional list filled with the specified strings.

    White cells are filled with outer_str. Black cells are filled with
    inner_str. Space-filling monospaced characters work best.

    Args:
        input_wb_list (list[list[int]])
        inner_str (str)
        outer_str (str)

    Returns:
        list[list[str]]
    """
    gen_inner_text = infinity_gen_text(inner_text)
    gen_outer_text = infinity_gen_text(outer_text)

    result_wb_char_list: list[list[str]] = []
    for tmp_wb_list in input_wb_list:
        tmp_wb_char_list: list[str] = []
        for tmp_wb_val in tmp_wb_list:
            if tmp_wb_val == 1:
                tmp_wb_char_list.append(next(gen_outer_text))
            else:
                tmp_wb_char_list.append(next(gen_inner_text))
        result_wb_char_list.append(tmp_wb_char_list)

    return result_wb_char_list
