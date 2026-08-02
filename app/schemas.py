import unicodedata
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from glyph_forge.services.settings import (
    DEFAULT_FRAME_FONT_SIZE,
    DEFAULT_MAX_CHARS_PER_LINE,
    DEFAULT_OUTPUT_FONT_SIZE,
    DEFAULT_TEXT_COLOR,
    GlyphForgeConfig,
)

MAX_FRAME_TEXT_LENGTH = 64
MAX_FILL_TEXT_LENGTH = 128
MIN_FRAME_FONT_SIZE = 8
MAX_FRAME_FONT_SIZE = 128
MIN_OUTPUT_FONT_SIZE = 10
MAX_OUTPUT_FONT_SIZE = 64

MaxCharsPerLine = Annotated[int, Field(gt=0, le=MAX_FRAME_TEXT_LENGTH)]
FrameText = Annotated[str, Field(min_length=1, max_length=MAX_FRAME_TEXT_LENGTH)]
FillText = Annotated[str, Field(min_length=1, max_length=MAX_FILL_TEXT_LENGTH)]
FrameFontSize = Annotated[
    int,
    Field(ge=MIN_FRAME_FONT_SIZE, le=MAX_FRAME_FONT_SIZE),
]
OutputFontSize = Annotated[
    int,
    Field(ge=MIN_OUTPUT_FONT_SIZE, le=MAX_OUTPUT_FONT_SIZE),
]
RgbValue = Annotated[int, Field(ge=0, le=255)]
RgbColor = tuple[RgbValue, RgbValue, RgbValue]


def normalize_render_text(value: str, name: str, max_length: int) -> str:
    normalized_value = unicodedata.normalize("NFC", value)
    if not normalized_value.strip():
        raise ValueError(f"{name} must contain a visible character")
    if any(unicodedata.category(char) == "Cc" for char in normalized_value):
        raise ValueError(f"{name} must not contain control characters")
    if len(normalized_value) > max_length:
        raise ValueError(f"{name} must not exceed {max_length} characters")
    return normalized_value


class GenerateImageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_text: FrameText
    inner_text: FillText
    outer_text: FillText
    max_chars_per_line: MaxCharsPerLine = DEFAULT_MAX_CHARS_PER_LINE
    frame_font_size: FrameFontSize = DEFAULT_FRAME_FONT_SIZE
    output_font_size: OutputFontSize = DEFAULT_OUTPUT_FONT_SIZE
    inner_color: RgbColor = DEFAULT_TEXT_COLOR
    outer_color: RgbColor = DEFAULT_TEXT_COLOR

    @field_validator("frame_text", "inner_text", "outer_text", mode="before")
    @classmethod
    def normalize_and_validate_text(cls, value: object, info: ValidationInfo) -> object:
        if not isinstance(value, str):
            return value
        max_length = (
            MAX_FRAME_TEXT_LENGTH
            if info.field_name == "frame_text"
            else MAX_FILL_TEXT_LENGTH
        )
        return normalize_render_text(value, info.field_name, max_length)

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
