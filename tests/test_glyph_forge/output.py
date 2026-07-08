def print_2D_num_list(num_list: list[list[int]]) -> None:
    """Print the given list of 2D numbers

    Args:
        num_list (list[list[int]])
    """
    for tmp_num_list in num_list:
        for num in tmp_num_list:
            print(num, end="")
        print()
