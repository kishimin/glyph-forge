from io import BytesIO

from fastapi import FastAPI, HTTPException, Request, responses
from PIL import Image
from starlette.datastructures import UploadFile

from app.schemas import (
    MAX_FILL_TEXT_LENGTH,
    MAX_OUTPUT_FONT_SIZE,
    MIN_OUTPUT_FONT_SIZE,
    GenerateImageRequest,
    normalize_render_text,
    validate_fill_pair,
)
from glyph_forge.services.glyph_art_renderer import (
    render_background_image,
    render_glyph_art_image,
    render_image_frame_art_image,
    render_x_icon_image,
)
from glyph_forge.services.settings import (
    DEFAULT_OUTPUT_FONT_SIZE,
    DEFAULT_TEXT_COLOR,
    GlyphForgeConfig,
)

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


def _png_response(img: Image.Image) -> responses.StreamingResponse:
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return responses.StreamingResponse(buffer, media_type="image/png")


def _render_or_422(render_image) -> responses.StreamingResponse:
    try:
        return _png_response(render_image())
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def _form_value(form, name: str) -> str:
    value = form.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must not be empty")
    return normalize_render_text(
        value,
        name,
        MAX_FILL_TEXT_LENGTH,
        allow_whitespace_only=True,
    )


def _form_output_font_size(form, name: str, default: int) -> int:
    value = form.get(name)
    if value is None or value == "":
        return default
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error
    if parsed_value < MIN_OUTPUT_FONT_SIZE or parsed_value > MAX_OUTPUT_FONT_SIZE:
        raise ValueError(
            f"{name} must be between "
            f"{MIN_OUTPUT_FONT_SIZE} and {MAX_OUTPUT_FONT_SIZE}"
        )
    return parsed_value


def _form_rgb_color(form, name: str):
    value = form.get(name)
    if value is None or value == "":
        return DEFAULT_TEXT_COLOR
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a comma-separated RGB color")
    parts = value.split(",")
    if len(parts) != 3:
        raise ValueError(f"{name} must be a comma-separated RGB color")
    try:
        color = tuple(int(part.strip()) for part in parts)
    except ValueError as error:
        raise ValueError(f"{name} must be a comma-separated RGB color") from error
    if any(channel < 0 or channel > 255 for channel in color):
        raise ValueError(f"{name} values must be between 0 and 255")
    return color


async def _uploaded_image(form) -> Image.Image:
    frame_image = form.get("frame_image")
    if not isinstance(frame_image, UploadFile):
        raise ValueError("frame_image must be uploaded")
    try:
        image_bytes = await frame_image.read()
        img = Image.open(BytesIO(image_bytes))
        img.load()
    except Exception as error:
        raise ValueError("frame_image must be a valid image") from error
    return img


@app.post("/images")
def generate_image(generate_image_request: GenerateImageRequest):
    return _render_or_422(
        lambda: render_glyph_art_image(
            frame_text=generate_image_request.frame_text,
            inner_text=generate_image_request.inner_text,
            outer_text=generate_image_request.outer_text,
            config=generate_image_request.to_config(),
        )
    )


@app.post("/images/x-icon")
def generate_x_icon_image(generate_image_request: GenerateImageRequest):
    return _render_or_422(
        lambda: render_x_icon_image(
            frame_text=generate_image_request.frame_text,
            inner_text=generate_image_request.inner_text,
            outer_text=generate_image_request.outer_text,
            config=generate_image_request.to_config(),
        )
    )


@app.post("/images/background")
def generate_background_image(generate_image_request: GenerateImageRequest):
    return _render_or_422(
        lambda: render_background_image(
            frame_text=generate_image_request.frame_text,
            inner_text=generate_image_request.inner_text,
            outer_text=generate_image_request.outer_text,
            config=generate_image_request.to_config(),
        )
    )


@app.post("/images/frame-file")
async def generate_image_from_frame_file(request: Request):
    try:
        form = await request.form()
        frame_img = await _uploaded_image(form)
        inner_text = _form_value(form, "inner_text")
        outer_text = _form_value(form, "outer_text")
        validate_fill_pair(inner_text, outer_text)
        config = GlyphForgeConfig(
            output_font_size=_form_output_font_size(
                form,
                "output_font_size",
                DEFAULT_OUTPUT_FONT_SIZE,
            ),
            inner_color=_form_rgb_color(form, "inner_color"),
            outer_color=_form_rgb_color(form, "outer_color"),
        )
        return _png_response(
            render_image_frame_art_image(
                frame_img,
                inner_text,
                outer_text,
                config=config,
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
