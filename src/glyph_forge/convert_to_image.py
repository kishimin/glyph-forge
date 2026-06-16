from PIL import Image
from glyph_forge.convert_text_to_image import str_2_img
from glyph_forge.convert_image_to_01_list import (
    gray_list_2_wb_list,
    img_2_gray_list
)
from glyph_forge.fill_wb_list_with_text import wb_list_2_wb_char_list

def str_2_str_img(flame_str: str, inner_str: str, outer_str: str, horizontal_len: int, vertical_len: int, str_size: int, final_str_size: int) -> Image.Image:
    """Execute the processing in batches and save the resulting list of characters as an image

    Args:
        flame_str (str)
        inner_str (str)
        outer_str (str)
        horizontal_len (int)
        vertical_len (int)
        char_size (int)
        final_char_size (int)

    Returns:
        Image.Image
    """
    img = str_2_img(flame_str, horizontal_len, vertical_len, str_size)
    gray_list = img_2_gray_list(img)
    wb_list = gray_list_2_wb_list(gray_list)
    wb_char_list = wb_list_2_wb_char_list(wb_list, inner_str, outer_str)

    all_str = ""
    for tmp_list in wb_char_list:
        for char in tmp_list:
            all_str += char

    img = str_2_img(all_str, horizontal_len * str_size, vertical_len * str_size, final_str_size)

    return img