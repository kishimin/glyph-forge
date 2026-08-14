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
    DEFAULT_OUTPUT_FONT_SIZE,
    DEFAULT_TEXT_COLOR,
    GlyphForgeConfig,
)
from glyph_forge.services.unicode_text import exceeds_grapheme_limit

MAX_FRAME_TEXT_LENGTH = 64
MAX_FILL_TEXT_LENGTH = 128
MIN_FRAME_FONT_SIZE = 8
MAX_FRAME_FONT_SIZE = 128
MIN_OUTPUT_FONT_SIZE = 10
MAX_OUTPUT_FONT_SIZE = 64

FrameText = Annotated[str, Field(min_length=1)]
FillText = Annotated[str, Field(min_length=1)]
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


def normalize_render_text(
    value: str,
    name: str,
    max_length: int,
    *,
    allow_whitespace_only: bool = False,
) -> str:
    normalized_value = unicodedata.normalize("NFC", value)
    if not allow_whitespace_only and not normalized_value.strip():
        raise ValueError(f"{name} must contain a visible character")
    if any(unicodedata.category(char) == "Cc" for char in normalized_value):
        raise ValueError(f"{name} must not contain control characters")
    if exceeds_grapheme_limit(normalized_value, max_length):
        raise ValueError(f"{name} must not exceed {max_length} characters")
    return normalized_value


def validate_fill_pair(inner_text: str, outer_text: str) -> None:
    if not inner_text.strip() and not outer_text.strip():
        raise ValueError(
            "inner_text and outer_text must not both contain only whitespace"
        )


class GenerateImageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_text: FrameText
    inner_text: FillText
    outer_text: FillText
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
        return normalize_render_text(
            value,
            info.field_name,
            max_length,
            allow_whitespace_only=info.field_name != "frame_text",
        )

    @model_validator(mode="after")
    def validate_request_relationships(self) -> "GenerateImageRequest":
        validate_fill_pair(self.inner_text, self.outer_text)
        return self

    def to_config(self) -> GlyphForgeConfig:
        return GlyphForgeConfig(
            frame_font_size=self.frame_font_size,
            output_font_size=self.output_font_size,
            inner_color=self.inner_color,
            outer_color=self.outer_color,
        )
