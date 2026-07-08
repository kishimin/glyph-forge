from dataclasses import dataclass

Color = tuple[int, int, int]

DEFAULT_MAX_CHARS_PER_LINE = 5
DEFAULT_FRAME_FONT_SIZE = 20
DEFAULT_OUTPUT_FONT_SIZE = 15
DEFAULT_BACKGROUND_COLOR: Color = (255, 255, 255)
DEFAULT_TEXT_COLOR: Color = (0, 0, 0)
IMAGE_MODE_RGB = "RGB"
IMAGE_MODE_RGBA = "RGBA"
WHITE_BINARY_VALUE = 1
BLACK_BINARY_VALUE = 0


@dataclass(frozen=True)
class GlyphForgeConfig:
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE
    frame_font_size: int = DEFAULT_FRAME_FONT_SIZE
    output_font_size: int = DEFAULT_OUTPUT_FONT_SIZE
    inner_color: Color = DEFAULT_TEXT_COLOR
    outer_color: Color = DEFAULT_TEXT_COLOR
    background_color: Color = DEFAULT_BACKGROUND_COLOR

    def __post_init__(self) -> None:
        if self.max_chars_per_line < 1:
            raise ValueError("max_chars_per_line must be greater than 0")
        if self.frame_font_size < 1:
            raise ValueError("frame_font_size must be greater than 0")
        if self.output_font_size < 1:
            raise ValueError("output_font_size must be greater than 0")
