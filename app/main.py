from io import BytesIO

from fastapi import FastAPI, HTTPException, responses
from PIL import Image

from app.schemas import GenerateImageRequest
from glyph_forge.services.glyph_art_renderer import (
    render_background_image,
    render_glyph_art_image,
    render_x_icon_image,
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