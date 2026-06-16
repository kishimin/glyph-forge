from glyph_forge.convert_to_image import str_2_str_img
import IPython

def test_can_save_as_an_image():
    img = str_2_str_img("カニ", "エビ", " ", 2, 1, 20, 15)

    img.save("ebikani.png")

    IPython.display.Image("ebikani.png")