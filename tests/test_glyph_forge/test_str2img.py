from glyph_forge.convert_text_to_image import text_2_img
import matplotlib.pyplot as plt

def test_can_be_created_from_text_to_images():
    img = text_2_img(input_text="勝利友情努力", horizontal_len=2, vertical_len=3, text_size=50)
    
    assert img is not None
    assert img.size == (100, 150)