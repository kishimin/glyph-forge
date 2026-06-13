from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def str2img(input_str: str, horizontal_length: int, vertical_length: int, char_size: int) -> Image:
    """Convert the given string into an image

    Args:
        input_str (str)
        horizontal_length (int)
        vertical_length (int)
        char_size (int)

    Returns:
        Image
    """
    img = Image.new("RGBA", (char_size * horizontal_length, char_size * vertical_length) , "white")
    draw = ImageDraw.Draw(img)

    font_path = Path(__file__).parent / "fonts" / "ipaexg.ttf"
    font = ImageFont.truetype(font=font_path, size=char_size)

    # Draw characters one by one
    horizontal_count = 0
    vertical_count = 0
    for char in input_str:
        if vertical_count >= vertical_length:
            break
        # Draw one character at a time in the specified position
        draw.text((horizontal_count * char_size, vertical_count * char_size), char, fill=(0, 0, 0), font=font)
        horizontal_count += 1
        if horizontal_count >= horizontal_length:
            horizontal_count = 0
            vertical_count += 1

    return img
