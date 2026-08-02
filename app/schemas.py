from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from glyph_forge.services.settings import (
    DEFAULT_FRAME_FONT_SIZE,
    DEFAULT_MAX_CHARS_PER_LINE,
    DEFAULT_OUTPUT_FONT_SIZE,
    DEFAULT_TEXT_COLOR,
    GlyphForgeConfig,
)

PositiveInt = Annotated[int, Field(gt=0)]
MaxCharsPerLine = Annotated[int, Field(gt=0, le=64)]
NonEmptyString = Annotated[str, Field(min_length=1)]
RgbValue = Annotated[int, Field(ge=0, le=255)]
RgbColor = tuple[RgbValue, RgbValue, RgbValue]


class GenerateImageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_text: NonEmptyString
    inner_text: NonEmptyString
    outer_text: NonEmptyString
    max_chars_per_line: MaxCharsPerLine = DEFAULT_MAX_CHARS_PER_LINE
    frame_font_size: PositiveInt = DEFAULT_FRAME_FONT_SIZE
    output_font_size: PositiveInt = DEFAULT_OUTPUT_FONT_SIZE
    inner_color: RgbColor = DEFAULT_TEXT_COLOR
    outer_color: RgbColor = DEFAULT_TEXT_COLOR

    @model_validator(mode="after")
    def validate_explicit_chars_per_line(self) -> "GenerateImageRequest":
        if (
            "max_chars_per_line" in self.model_fields_set
            and self.max_chars_per_line > len(self.frame_text)
        ):
            raise ValueError("max_chars_per_line must not exceed frame_text length")
        return self

    def to_config(self) -> GlyphForgeConfig:
        return GlyphForgeConfig(
            max_chars_per_line=min(self.max_chars_per_line, len(self.frame_text)),
            frame_font_size=self.frame_font_size,
            output_font_size=self.output_font_size,
            inner_color=self.inner_color,
            outer_color=self.outer_color,
        )
