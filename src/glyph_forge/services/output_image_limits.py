MAX_OUTPUT_IMAGE_WIDTH = 2048
MAX_OUTPUT_IMAGE_HEIGHT = 2048
MAX_OUTPUT_IMAGE_PIXELS = 4_194_304


class OutputImageSizeExceeded(ValueError):
    pass


def validate_output_image_size(size: tuple[int, int]) -> None:
    width, height = size
    if width > MAX_OUTPUT_IMAGE_WIDTH:
        raise OutputImageSizeExceeded(
            f"output image width must not exceed {MAX_OUTPUT_IMAGE_WIDTH}"
        )
    if height > MAX_OUTPUT_IMAGE_HEIGHT:
        raise OutputImageSizeExceeded(
            f"output image height must not exceed {MAX_OUTPUT_IMAGE_HEIGHT}"
        )
    if width * height > MAX_OUTPUT_IMAGE_PIXELS:
        raise OutputImageSizeExceeded(
            f"output image pixel count must not exceed {MAX_OUTPUT_IMAGE_PIXELS}"
        )
