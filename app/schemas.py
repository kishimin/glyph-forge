from pydantic import BaseModel

from glyph_forge.services.settings import (
    DEFAULT_FRAME_FONT_SIZE,
    DEFAULT_MAX_CHARS_PER_LINE,
    DEFAULT_OUTPUT_FONT_SIZE,
    DEFAULT_TEXT_COLOR,
    Color,
    GlyphForgeConfig,
)


class GenerateImageRequest(BaseModel):
    frame_text: str
    inner_text: str
    outer_text: str
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE
    frame_font_size: int = DEFAULT_FRAME_FONT_SIZE
    output_font_size: int = DEFAULT_OUTPUT_FONT_SIZE
    inner_color: Color = DEFAULT_TEXT_COLOR
    outer_color: Color = DEFAULT_TEXT_COLOR

    def to_config(self) -> GlyphForgeConfig:
        return GlyphForgeConfig(
            max_chars_per_line=self.max_chars_per_line,
            frame_font_size=self.frame_font_size,
            output_font_size=self.output_font_size,
            inner_color=self.inner_color,
            outer_color=self.outer_color,
        )
