from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def text_2_img(input_text: str, horizontal_len: int, vertical_len: int, text_size: int) -> Image.Image:
    """Convert the given string into an image

    Args:
        input_text (str)
        horizontal_len (int)
        vertical_len (int)
        text_size (int)

    Returns:
        Image.Image
    """
    img = Image.new("RGBA", (text_size * horizontal_len, text_size * vertical_len) , "white")
    draw = ImageDraw.Draw(img)

    font_path = Path(__file__).parent / "fonts" / "ipaexg.ttf"
    font = ImageFont.truetype(font=font_path, size=text_size)

    # Draw characters one by one
    horizontal_count = 0
    vertical_count = 0
    for char in input_text:
        if vertical_count >= vertical_len:
            break
        # Draw one character at a time in the specified position
        draw.text((horizontal_count * text_size, vertical_count * text_size), char, fill=(0, 0, 0), font=font)
        horizontal_count += 1
        if horizontal_count >= horizontal_len:
            horizontal_count = 0
            vertical_count += 1

    return img
