from PIL import Image
from glyph_forge.convert_text_to_image import text_2_img
from glyph_forge.convert_image_to_01_list import (
    gray_list_2_wb_list,
    img_2_gray_list
)
from glyph_forge.fill_wb_list_with_text import wb_list_2_wb_text_list

def text_2_text_img(flame_text: str, inner_text: str, outer_text: str, horizontal_len: int, vertical_len: int, text_size: int, final_text_size: int) -> Image.Image:
    """Execute the processing in batches and save the resulting list of characters as an image

    Args:
        flame_text (str)
        inner_text (str)
        outer_text (str)
        horizontal_len (int)
        vertical_len (int)
        text_size (int)
        final_text_size (int)

    Returns:
        Image.Image
    """
    img = text_2_img(flame_text, horizontal_len, vertical_len, text_size)
    gray_list = img_2_gray_list(img)
    wb_list = gray_list_2_wb_list(gray_list)
    wb_text_list = wb_list_2_wb_text_list(wb_list, inner_text, outer_text)

    all_text = ""
    for tmp_list in wb_text_list:
        for text in tmp_list:
            all_text += text

    img = text_2_img(all_text, horizontal_len * text_size, vertical_len * text_size, final_text_size)

    return img