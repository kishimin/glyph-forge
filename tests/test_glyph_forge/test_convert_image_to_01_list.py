from glyph_forge.convert_text_to_image import text_2_img
from glyph_forge.convert_image_to_01_list import (gray_list_2_wb_list, img_2_gray_list)
from test_glyph_forge.output import print_2D_num_list

def test_can_print_the_given_list_of_2D_numbers():
    img = text_2_img("般若波羅蜜多", 6, 1, 20)
    gray_list = img_2_gray_list(img)
    wb_list = gray_list_2_wb_list(gray_list)

    print_2D_num_list(wb_list)