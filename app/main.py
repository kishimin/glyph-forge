from io import BytesIO

import anyio
from fastapi import FastAPI, HTTPException, Request, responses
from PIL import Image
from starlette.datastructures import UploadFile

from app.image_worker import (
    ImageGenerationTimeout,
    ImageGenerationValueError,
    run_image_generation_in_process,
)
from app.request_limits import (
    IMAGE_GENERATION_TIMEOUT_SECONDS,
    IMAGE_REQUEST_QUEUE_TIMEOUT_SECONDS,
    MAX_CONCURRENT_IMAGE_REQUESTS,
    MAX_WAITING_IMAGE_REQUESTS,
    RATE_LIMIT_BURST_SIZE,
    RATE_LIMIT_REQUESTS_PER_MINUTE,
    ConcurrentRequestLimiter,
    ImageRequestLimitsMiddleware,
    RequestBodyTooLarge,
    TokenBucketRateLimiter,
    image_generation_capacity_response,
    request_with_body_limit,
)
from app.schemas import (
    MAX_FILL_TEXT_LENGTH,
    MAX_OUTPUT_FONT_SIZE,
    MIN_OUTPUT_FONT_SIZE,
    GenerateImageRequest,
    normalize_render_text,
    validate_fill_pair,
)
from app.uploaded_image import (
    MAX_UPLOADED_IMAGE_BYTES,
    decode_uploaded_image,
    read_uploaded_image_bytes,
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
app.state.image_rate_limiter = TokenBucketRateLimiter(
    requests_per_minute=RATE_LIMIT_REQUESTS_PER_MINUTE,
    burst_size=RATE_LIMIT_BURST_SIZE,
)
app.state.image_concurrency_limiter = ConcurrentRequestLimiter(
    max_concurrent=MAX_CONCURRENT_IMAGE_REQUESTS,
    max_waiting=MAX_WAITING_IMAGE_REQUESTS,
    wait_timeout_seconds=IMAGE_REQUEST_QUEUE_TIMEOUT_SECONDS,
)
app.state.image_generation_timeout_seconds = IMAGE_GENERATION_TIMEOUT_SECONDS
app.add_middleware(
    ImageRequestLimitsMiddleware,
    rate_limiter=app.state.image_rate_limiter,
    concurrent_limiter=app.state.image_concurrency_limiter,
)

# Existing text fields are tightly bounded; 64 KiB leaves room for their multipart
# headers while keeping the complete request close to the accepted 2 MiB image.
MULTIPART_OVERHEAD_BYTES = 64 * 1024
MAX_FRAME_FILE_REQUEST_BYTES = MAX_UPLOADED_IMAGE_BYTES + MULTIPART_OVERHEAD_BYTES


@app.get("/health")
def health():
    return {"status": "ok"}


def _png_response(image_bytes: bytes) -> responses.StreamingResponse:
    return responses.StreamingResponse(BytesIO(image_bytes), media_type="image/png")


async def _run_image_generation(render_image, *args, **kwargs):
    try:
        image_bytes = await anyio.to_thread.run_sync(
            run_image_generation_in_process,
            render_image,
            args,
            kwargs,
            app.state.image_generation_timeout_seconds,
        )
    except ImageGenerationTimeout:
        return image_generation_capacity_response()
    except ImageGenerationValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _png_response(image_bytes)


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


async def _uploaded_image_bytes(form) -> bytes:
    frame_image = form.get("frame_image")
    if not isinstance(frame_image, UploadFile):
        raise ValueError("frame_image must be uploaded")
    return await read_uploaded_image_bytes(frame_image)


def _render_uploaded_frame_image(
    image_bytes: bytes,
    inner_text: str,
    outer_text: str,
    config: GlyphForgeConfig,
) -> Image.Image:
    frame_img = decode_uploaded_image(image_bytes)
    return render_image_frame_art_image(
        frame_img,
        inner_text,
        outer_text,
        config=config,
    )


@app.post("/images")
async def generate_image(generate_image_request: GenerateImageRequest):
    return await _run_image_generation(
        render_glyph_art_image,
        generate_image_request.frame_text,
        generate_image_request.inner_text,
        generate_image_request.outer_text,
        config=generate_image_request.to_config(),
    )


@app.post("/images/x-icon")
async def generate_x_icon_image(generate_image_request: GenerateImageRequest):
    return await _run_image_generation(
        render_x_icon_image,
        generate_image_request.frame_text,
        generate_image_request.inner_text,
        generate_image_request.outer_text,
        config=generate_image_request.to_config(),
    )


@app.post("/images/background")
async def generate_background_image(generate_image_request: GenerateImageRequest):
    return await _run_image_generation(
        render_background_image,
        generate_image_request.frame_text,
        generate_image_request.inner_text,
        generate_image_request.outer_text,
        config=generate_image_request.to_config(),
    )


@app.post("/images/frame-file")
async def generate_image_from_frame_file(request: Request):
    try:
        limited_request = request_with_body_limit(
            request,
            MAX_FRAME_FILE_REQUEST_BYTES,
        )
        form = await limited_request.form(max_files=1, max_fields=5)
        image_bytes = await _uploaded_image_bytes(form)
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
        return await _run_image_generation(
            _render_uploaded_frame_image,
            image_bytes,
            inner_text,
            outer_text,
            config,
        )
    except RequestBodyTooLarge as error:
        raise HTTPException(
            status_code=413,
            detail="request body is too large",
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
