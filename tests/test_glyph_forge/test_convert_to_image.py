from glyph_forge.services.convert_to_image import text_2_text_img

def test_can_save_as_an_image():
    img = text_2_text_img("カニ", "エビ", " ", 2, 1, 20, 15)

    img.save("../output/ebikani.png")
