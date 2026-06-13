from glyph_forge import str2img, convert_image_to_01_list

def print_2D_num_list(num_list: list[list[int]]) -> None:
    """Print the given list of 2D numbers

    Args:
        num_list (list[list[int]])
    """
    for tmp_num_list in num_list:
        for num in tmp_num_list:
            print(num, end="")
        print()

def test_can_print_the_given_list_of_2D_numbers():
    img = str2img.str2img("般若波羅蜜多", 6, 1, 20)
    gray_list = convert_image_to_01_list.img_2_gray_list(img)
    wb_list = convert_image_to_01_list.gray_list_2_wb_list(gray_list)

    print_2D_num_list(wb_list)