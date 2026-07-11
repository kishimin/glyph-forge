from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from glyph_forge.services.settings import (
    DEFAULT_FRAME_CELL_PADDING_RATIO,
    DEFAULT_FRAME_FONT_SIZE,
    DEFAULT_MAX_CHARS_PER_LINE,
    DEFAULT_OUTPUT_FONT_SIZE,
    DEFAULT_TEXT_COLOR,
    GlyphForgeConfig,
)

PositiveInt = Annotated[int, Field(gt=0)]
NonEmptyString = Annotated[str, Field(min_length=1)]
RgbValue = Annotated[int, Field(ge=0, le=255)]
RgbColor = tuple[RgbValue, RgbValue, RgbValue]


class GenerateImageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_text: NonEmptyString
    inner_text: NonEmptyString
    outer_text: NonEmptyString
    max_chars_per_line: PositiveInt = DEFAULT_MAX_CHARS_PER_LINE
    frame_font_size: PositiveInt = DEFAULT_FRAME_FONT_SIZE
    output_font_size: PositiveInt = DEFAULT_OUTPUT_FONT_SIZE
    frame_cell_padding_ratio: Annotated[float, Field(ge=0)] = (
        DEFAULT_FRAME_CELL_PADDING_RATIO
    )
    inner_color: RgbColor = DEFAULT_TEXT_COLOR
    outer_color: RgbColor = DEFAULT_TEXT_COLOR

    def to_config(self) -> GlyphForgeConfig:
        return GlyphForgeConfig(
            max_chars_per_line=self.max_chars_per_line,
            frame_font_size=self.frame_font_size,
            output_font_size=self.output_font_size,
            frame_cell_padding_ratio=self.frame_cell_padding_ratio,
            inner_color=self.inner_color,
            outer_color=self.outer_color,
        )
