from itertools import cycle
from typing import Generator


def cycle_text(text: str) -> Generator[str, None, None]:
    yield from cycle(text)


def binary_grid_to_text_grid(
    binary_grid: list[list[int]], inner_text: str, outer_text: str
) -> list[list[str]]:
    inner_chars = cycle_text(inner_text)
    outer_chars = cycle_text(outer_text)

    result: list[list[str]] = []
    for binary_row in binary_grid:
        text_row: list[str] = []
        for binary_value in binary_row:
            if binary_value == 1:
                text_row.append(next(outer_chars))
            else:
                text_row.append(next(inner_chars))
        result.append(text_row)

    return result
