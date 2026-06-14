from typing import Generator

def infinity_gen_str(str: str) -> Generator[str, None, None]:
    """A generator that extracts characters from a string one by one.
        It repeats using a semi-infinite loop.

    Args:
        str (str)

    Yields:
        Generator[str, None, None]
    """
    for _ in range(1000000000):
        for s in str:
            yield s

def wb_list_2_wb_char_list(input_wb_list: list[list[int]], inner_str: str, outer_str: str) -> list[list[str]]:
    """Return a two-dimensional list where the black and white cells are filled with the specified strings.
        White cells are filled with outer_str.
        Black cells are filled with inner_str.
        It is preferable to use characters and fonts that are space-filling and monospaced.

    Args:
        input_wb_list (list[list[int]])
        inner_str (str)
        outer_str (str)

    Returns:
        list[list[str]]
    """
    gen_inner_str = infinity_gen_str(inner_str)
    gen_outer_str = infinity_gen_str(outer_str)

    result_wb_char_list: list[list[str]] = []
    for tmp_wb_list in input_wb_list:
        tmp_wb_char_list: list[str] = []
        for tmp_wb_val in tmp_wb_list:
            if tmp_wb_val == 1:
                tmp_wb_char_list.append(next(gen_outer_str))
            else:
                tmp_wb_char_list.append(next(gen_inner_str))
        result_wb_char_list.append(tmp_wb_char_list)

    return result_wb_char_list