from PIL import Image, ImageDraw, ImageFont
import numpy as np

def img_2_gray_list(input_img: Image.Image) -> list[int]:
    """Converts the provided image into a grayscale(white = 1, gray = 0.5, black = 0)
        It is designed to handle even color images.

    Args:
        input_img (Image.Image)

    Returns:
        list[int]
    """
    img_width, img_height = input_img.size

    result_gray_list :list[int] = []
    for y in range(0, img_height, 1):
        tmp_gray_list :list[int] = []
        for x in range(0, img_width, 1):
            # Since four data points(r, g, b, a) are available, we will retrieve the three values r, g, and b.
            r, g, b, = input_img.getpixel((x, y))[0:3]

            grayscale: int = (r + g + b) / 3
            tmp_gray_list.append(grayscale)

        result_gray_list.append(tmp_gray_list)
    
    return result_gray_list

def gray_list_2_wb_list(input_gray_list: list[int]) -> list[list[int]]:
    """Convert the provided grayscale image into a binary image where white = 1 and black = 0.
        To prevent images with predominantly black areas from becoming entirely black,
        or images with light colors from becoming entirely white, 
        calculate the average value as a threshold and use that threshold to datetime
        the value of each pixel.
        As a result, list areas will not be converted entirely to white, nor will dark
        areas be converted entirely to black.

    Args:
        input_gray_list (list[int])

    Returns:
        list[int]
    """
    # Set the average value of the given two-dimensional array as the threshold
    threshold: float = np.mean(input_gray_list)

    result_wb_list :list[int] = []
    for tmp_gray_list in input_gray_list:
        tmp_wb_list :list[int] = []
        for tmp_gray_val in tmp_gray_list:
            if tmp_gray_val >= threshold:
                tmp_wb_list.append(1)
            else:
                tmp_wb_list.append(0)
        result_wb_list.append(tmp_wb_list)

    return result_wb_list