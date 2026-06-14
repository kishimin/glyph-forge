from glyph_forge.convert_text_to_image import str_2_img
from glyph_forge.convert_image_to_01_list import (gray_list_2_wb_list, img_2_gray_list)
from glyph_forge.fill_wb_list_with_text import wb_list_2_wb_char_list
from test_glyph_forge.output import print_2D_num_list

def test_can_fill_wb_list_with_text():
    img = str_2_img("般若波羅蜜多", 6, 1, 20)
    gray_list = img_2_gray_list(img)
    wb_list = gray_list_2_wb_list(gray_list)

    wb_char_list = wb_list_2_wb_char_list(wb_list, "般若波羅蜜多", "　")
    print_2D_num_list(wb_char_list)