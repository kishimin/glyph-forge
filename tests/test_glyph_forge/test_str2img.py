from glyph_forge import str2img
import matplotlib.pyplot as plt

def test_can_be_created_from_text_to_images():
    img = str2img.str2img(input_str="勝利友情努力", horizontal_length=2, vertical_length=3, char_size=50)
    plt.imshow(img)
    plt.axis("off")
    plt.show()
