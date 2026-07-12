from dataclasses import dataclass

Color = tuple[int, int, int] | tuple[int, int, int, int]

DEFAULT_MAX_CHARS_PER_LINE = 5
DEFAULT_FRAME_FONT_SIZE = 20
DEFAULT_OUTPUT_FONT_SIZE = 20
DEFAULT_FRAME_CELL_PADDING_RATIO = 0.0
UNCROPPED_FRAME_CELL_PADDING_RATIO = 0.2
DEFAULT_BACKGROUND_COLOR: Color = (255, 255, 255)
DEFAULT_TEXT_COLOR: Color = (0, 0, 0)
DEFAULT_X_ICON_SIZE = (400, 400)
DEFAULT_BACKGROUND_SIZE = (1500, 500)
DEFAULT_CANVAS_MARGIN_RATIO = 0.08
DEFAULT_CANVAS_GRID_DIVISIONS = 3
MIN_READABLE_OUTPUT_FONT_SIZE = 10
IMAGE_MODE_RGB = "RGB"
IMAGE_MODE_RGBA = "RGBA"
TRANSPARENT_BACKGROUND_COLOR = (0, 0, 0, 0)
WHITE_BINARY_VALUE = 1
BLACK_BINARY_VALUE = 0


@dataclass(frozen=True)
class GlyphForgeConfig:
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE
    frame_font_size: int = DEFAULT_FRAME_FONT_SIZE
    output_font_size: int = DEFAULT_OUTPUT_FONT_SIZE
    frame_cell_padding_ratio: float = DEFAULT_FRAME_CELL_PADDING_RATIO
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
        if self.frame_cell_padding_ratio < 0:
            raise ValueError(
                "frame_cell_padding_ratio must be greater than or equal to 0"
            )
