import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Barrier, Event

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

import app.main as main_module
from app.main import app
from app.request_limits import RequestQueueFull
from app.schemas import GenerateImageRequest


def _slow_image_renderer(*args, **kwargs):
    time.sleep(2)
    return Image.new("RGB", (1, 1), (255, 255, 255))


@pytest.fixture(autouse=True)
def reset_image_rate_limiter():
    limiter = getattr(app.state, "image_rate_limiter", None)
    if limiter is not None:
        limiter.reset()


def test_health_returns_ok_for_monitoring():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_image_accepts_compact_request():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "ABCDEF",
            "inner_text": "x",
            "outer_text": ".",
            "frame_font_size": 10,
            "output_font_size": 10,
            "inner_color": [255, 0, 0],
            "outer_color": [0, 0, 255],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_generate_image_rate_limit_returns_retry_after_and_exempts_health():
    client = TestClient(app)
    request_body = {
        "frame_text": "A",
        "inner_text": "x",
        "outer_text": "o",
        "frame_font_size": 8,
        "output_font_size": 10,
    }

    accepted_responses = [client.post("/images", json=request_body) for _ in range(3)]
    limited_response = client.post("/images", json=request_body)
    health_response = client.get("/health")

    assert all(response.status_code == 200 for response in accepted_responses)
    assert limited_response.status_code == 429
    assert limited_response.headers["retry-after"] == "6"
    assert limited_response.json() == {"detail": "image generation rate limit exceeded"}
    assert health_response.status_code == 200


def test_generate_image_accepts_five_concurrent_requests_without_rate_limiting():
    request_body = {
        "frame_text": "A",
        "inner_text": "x",
        "outer_text": "o",
        "frame_font_size": 8,
        "output_font_size": 10,
    }
    start_requests = Barrier(5)

    def post_image():
        start_requests.wait()
        with TestClient(app) as client:
            return client.post("/images", json=request_body)

    with ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(executor.map(lambda _: post_image(), range(5)))

    assert [response.status_code for response in responses] == [200] * 5
    assert all(response.status_code != 429 for response in responses)


def test_generate_image_capacity_limit_returns_retry_after(monkeypatch):
    client = TestClient(app)

    async def reject_request():
        raise RequestQueueFull

    monkeypatch.setattr(
        app.state.image_concurrency_limiter,
        "acquire",
        reject_request,
    )

    response = client.post(
        "/images",
        json={
            "frame_text": "A",
            "inner_text": "x",
            "outer_text": "o",
        },
    )

    assert response.status_code == 503
    assert response.headers["retry-after"] == "1"
    assert response.json() == {
        "detail": "image generation capacity is temporarily unavailable"
    }


def test_generation_timeout_releases_capacity_for_next_request(monkeypatch):
    client = TestClient(app)
    original_renderer = main_module.render_glyph_art_image
    request_body = {
        "frame_text": "A",
        "inner_text": "x",
        "outer_text": "o",
    }
    monkeypatch.setattr(
        app.state,
        "image_generation_timeout_seconds",
        0.5,
        raising=False,
    )
    monkeypatch.setattr(
        main_module,
        "render_glyph_art_image",
        _slow_image_renderer,
    )

    timed_out_response = client.post("/images", json=request_body)
    monkeypatch.setattr(
        main_module,
        "render_glyph_art_image",
        original_renderer,
    )
    monkeypatch.setattr(app.state, "image_generation_timeout_seconds", 2.0)
    next_response = client.post("/images", json=request_body)

    assert timed_out_response.status_code == 503
    assert timed_out_response.headers["retry-after"] == "1"
    assert timed_out_response.json() == {
        "detail": "image generation capacity is temporarily unavailable"
    }
    assert next_response.status_code == 200


def test_generate_image_rejects_output_above_size_limit():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "ABCDE",
            "inner_text": "x",
            "outer_text": "o",
            "frame_font_size": 128,
            "output_font_size": 64,
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "output image width must not exceed 2048"}


def test_generate_x_icon_image_returns_png():
    client = TestClient(app)

    response = client.post(
        "/images/x-icon",
        json={
            "frame_text": "FRAME_TEXT_SAMPLE",
            "inner_text": "INNER_TEXT_SAMPLE",
            "outer_text": "OUTER_TEXT_SAMPLE",
            "inner_color": [255, 183, 197],
            "outer_color": [255, 0, 0],
            "output_font_size": 24,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_generate_background_image_returns_png():
    client = TestClient(app)

    response = client.post(
        "/images/background",
        json={
            "frame_text": "FRAME_TEXT_SAMPLE",
            "inner_text": "INNER_TEXT_SAMPLE",
            "outer_text": "OUTER_TEXT_SAMPLE",
            "inner_color": [255, 183, 197],
            "outer_color": [255, 0, 0],
            "output_font_size": 24,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_generate_image_from_uploaded_frame_image_returns_png():
    client = TestClient(app)
    upload_buffer = BytesIO()
    Image.new("RGB", (2, 1), (255, 255, 255)).save(upload_buffer, format="PNG")
    upload_buffer.seek(0)

    response = client.post(
        "/images/frame-file",
        data={
            "inner_text": "INNER_TEXT_SAMPLE",
            "outer_text": "OUTER_TEXT_SAMPLE",
            "inner_color": "255,183,197",
            "outer_color": "255,0,0",
            "output_font_size": "24",
        },
        files={"frame_image": ("frame.png", upload_buffer, "image/png")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_health_responds_while_uploaded_frame_image_is_rendering(monkeypatch):
    render_started = Event()
    release_render = Event()
    health_finished = Event()

    def blocking_worker(*args, **kwargs):
        render_started.set()
        release_render.wait(timeout=2)
        image_buffer = BytesIO()
        Image.new("RGB", (1, 1), (255, 255, 255)).save(
            image_buffer,
            format="PNG",
        )
        return image_buffer.getvalue()

    def get_health(client):
        response = client.get("/health")
        health_finished.set()
        return response

    monkeypatch.setattr(
        main_module,
        "run_image_generation_in_process",
        blocking_worker,
    )
    upload_buffer = BytesIO()
    Image.new("RGB", (2, 1), (255, 255, 255)).save(upload_buffer, format="PNG")
    upload_buffer.seek(0)

    with TestClient(app) as client, ThreadPoolExecutor(max_workers=2) as executor:
        upload_future = executor.submit(
            client.post,
            "/images/frame-file",
            data={"inner_text": "x", "outer_text": "o"},
            files={"frame_image": ("frame.png", upload_buffer, "image/png")},
        )
        assert render_started.wait(timeout=1)
        health_future = executor.submit(get_health, client)

        health_responded_before_render_finished = health_finished.wait(timeout=1)
        release_render.set()
        upload_response = upload_future.result(timeout=2)
        health_response = health_future.result(timeout=2)

    assert health_responded_before_render_finished
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert upload_response.status_code == 200


def test_generate_image_from_uploaded_frame_image_rejects_invalid_file():
    client = TestClient(app)

    response = client.post(
        "/images/frame-file",
        data={
            "inner_text": "INNER_TEXT_SAMPLE",
            "outer_text": "OUTER_TEXT_SAMPLE",
        },
        files={"frame_image": ("frame.txt", BytesIO(b"not an image"), "text/plain")},
    )

    assert response.status_code == 422


def test_generate_image_from_uploaded_frame_image_rejects_file_above_size_limit():
    client = TestClient(app)

    response = client.post(
        "/images/frame-file",
        data={"inner_text": "x", "outer_text": "o"},
        files={
            "frame_image": (
                "frame.png",
                BytesIO(b"A" * (2 * 1024 * 1024 + 1)),
                "image/png",
            )
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "frame_image must not exceed 2097152 bytes"}


def test_generate_image_from_frame_file_rejects_oversized_multipart_body():
    client = TestClient(app)
    max_request_bytes = 2 * 1024 * 1024 + 64 * 1024

    response = client.post(
        "/images/frame-file",
        data={"inner_text": "x", "outer_text": "o"},
        files={
            "frame_image": (
                "frame.png",
                BytesIO(b"A" * (max_request_bytes + 1)),
                "image/png",
            )
        },
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "request body is too large"}


def test_generate_image_from_frame_file_rejects_additional_file_part():
    client = TestClient(app)
    upload_buffer = BytesIO()
    Image.new("RGB", (2, 1), (255, 255, 255)).save(upload_buffer, format="PNG")
    upload_buffer.seek(0)

    response = client.post(
        "/images/frame-file",
        data={"inner_text": "x", "outer_text": "o"},
        files=[
            ("frame_image", ("frame.png", upload_buffer, "image/png")),
            ("extra_file", ("extra.png", BytesIO(b"A"), "image/png")),
        ],
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Too many files. Maximum number of files is 1."
    }


@pytest.mark.parametrize("image_size", [(205, 1), (1, 205)])
def test_generate_image_from_uploaded_frame_image_rejects_dimensions_above_limit(
    image_size,
):
    client = TestClient(app)
    upload_buffer = BytesIO()
    Image.new("RGB", image_size, (255, 255, 255)).save(upload_buffer, format="PNG")
    upload_buffer.seek(0)

    response = client.post(
        "/images/frame-file",
        data={"inner_text": "x", "outer_text": "o"},
        files={"frame_image": ("frame.png", upload_buffer, "image/png")},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "frame_image width and height must not exceed 204 pixels"
    }


def test_generate_image_from_uploaded_frame_image_rejects_unsupported_actual_format():
    client = TestClient(app)
    upload_buffer = BytesIO()
    Image.new("RGB", (2, 1), (255, 255, 255)).save(upload_buffer, format="BMP")
    upload_buffer.seek(0)

    response = client.post(
        "/images/frame-file",
        data={"inner_text": "x", "outer_text": "o"},
        files={"frame_image": ("frame.png", upload_buffer, "image/png")},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "frame_image format must be PNG, JPEG, or WEBP"
    }


def test_generate_image_from_uploaded_frame_image_rejects_animation():
    client = TestClient(app)
    upload_buffer = BytesIO()
    frames = [
        Image.new("RGB", (2, 1), (255, 255, 255)),
        Image.new("RGB", (2, 1), (0, 0, 0)),
    ]
    frames[0].save(
        upload_buffer,
        format="PNG",
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
    )
    upload_buffer.seek(0)

    response = client.post(
        "/images/frame-file",
        data={"inner_text": "x", "outer_text": "o"},
        files={"frame_image": ("frame.png", upload_buffer, "image/png")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "frame_image must not be animated"}


def test_generate_image_accepts_short_frame_with_internal_wrapping():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "ABC",
            "inner_text": "x",
            "outer_text": ".",
        },
    )

    assert response.status_code == 200


def test_generate_image_request_does_not_expose_frame_wrapping():
    properties = GenerateImageRequest.model_json_schema()["properties"]

    assert "max_chars_per_line" not in properties


def test_generate_image_rejects_legacy_max_chars_per_line():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "ABCDE",
            "inner_text": "x",
            "outer_text": ".",
            "max_chars_per_line": 5,
        },
    )

    assert response.status_code == 422


def test_generate_image_request_normalizes_text_before_enforcing_limits():
    request = GenerateImageRequest(
        frame_text="e\u0301" * 64,
        inner_text="x" * 128,
        outer_text="." * 128,
        frame_font_size=8,
        output_font_size=10,
    )

    assert request.frame_text == "é" * 64


def test_generate_image_request_accepts_multicodepoint_graphemes_at_limits():
    astronaut = "👩‍🚀"

    request = GenerateImageRequest(
        frame_text=astronaut * 64,
        inner_text=astronaut * 128,
        outer_text=astronaut * 128,
        frame_font_size=8,
        output_font_size=10,
    )

    assert request.frame_text == astronaut * 64
    assert request.inner_text == astronaut * 128
    assert request.outer_text == astronaut * 128


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("frame_text", "A" * 65),
        ("inner_text", "x" * 129),
        ("outer_text", "." * 129),
    ],
)
def test_generate_image_request_rejects_text_above_limit(field_name, value):
    payload = {
        "frame_text": "A",
        "inner_text": "x",
        "outer_text": ".",
    }
    payload[field_name] = value

    with pytest.raises(ValidationError):
        GenerateImageRequest(**payload)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("frame_text", "   "),
        ("inner_text", "line\nbreak"),
        ("outer_text", "tab\ttext"),
        ("outer_text", "control\x00text"),
    ],
)
def test_generate_image_request_rejects_non_renderable_text(field_name, value):
    payload = {
        "frame_text": "A",
        "inner_text": "x",
        "outer_text": ".",
    }
    payload[field_name] = value

    with pytest.raises(ValidationError):
        GenerateImageRequest(**payload)


@pytest.mark.parametrize(
    ("inner_text", "outer_text"),
    [
        ("   ", "."),
        ("x", "   "),
    ],
)
def test_generate_image_request_accepts_one_whitespace_only_fill(
    inner_text, outer_text
):
    request = GenerateImageRequest(
        frame_text="A",
        inner_text=inner_text,
        outer_text=outer_text,
    )

    assert request.inner_text == inner_text
    assert request.outer_text == outer_text


def test_generate_image_request_rejects_two_whitespace_only_fills():
    with pytest.raises(ValidationError):
        GenerateImageRequest(
            frame_text="A",
            inner_text="   ",
            outer_text="   ",
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("frame_font_size", 7),
        ("frame_font_size", 129),
        ("output_font_size", 9),
        ("output_font_size", 65),
    ],
)
def test_generate_image_request_rejects_font_size_outside_limits(field_name, value):
    payload = {
        "frame_text": "A",
        "inner_text": "x",
        "outer_text": ".",
    }
    payload[field_name] = value

    with pytest.raises(ValidationError):
        GenerateImageRequest(**payload)


def test_generate_image_rejects_legacy_frame_fields():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "A",
            "inner_text": "x",
            "outer_text": ".",
            "frame_columns": 1,
            "frame_rows": 1,
        },
    )

    assert response.status_code == 422


def test_generate_image_rejects_frame_cell_padding_ratio():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "A",
            "inner_text": "x",
            "outer_text": ".",
            "frame_cell_padding_ratio": 0.2,
        },
    )

    assert response.status_code == 422


def test_generate_image_rejects_empty_frame_text():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "",
            "inner_text": "x",
            "outer_text": ".",
        },
    )

    assert response.status_code == 422


def test_generate_image_rejects_color_values_outside_rgb_range():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "A",
            "inner_text": "x",
            "outer_text": ".",
            "inner_color": [256, 0, 0],
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_form_value",
    [
        {"inner_text": "x" * 129},
        {"outer_text": "." * 129},
        {"inner_text": "line\nbreak"},
        {"output_font_size": "9"},
        {"output_font_size": "65"},
    ],
)
def test_generate_image_from_frame_file_enforces_public_input_limits(
    invalid_form_value,
):
    client = TestClient(app)
    upload_buffer = BytesIO()
    Image.new("RGB", (2, 1), (255, 255, 255)).save(upload_buffer, format="PNG")
    upload_buffer.seek(0)
    form_data = {
        "inner_text": "x",
        "outer_text": ".",
        **invalid_form_value,
    }

    response = client.post(
        "/images/frame-file",
        data=form_data,
        files={"frame_image": ("frame.png", upload_buffer, "image/png")},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("inner_text", "outer_text"),
    [
        ("   ", "."),
        ("x", "   "),
    ],
)
def test_generate_image_from_frame_file_accepts_one_whitespace_only_fill(
    inner_text, outer_text
):
    client = TestClient(app)
    upload_buffer = BytesIO()
    Image.new("RGB", (2, 1), (255, 255, 255)).save(upload_buffer, format="PNG")
    upload_buffer.seek(0)

    response = client.post(
        "/images/frame-file",
        data={
            "inner_text": inner_text,
            "outer_text": outer_text,
        },
        files={"frame_image": ("frame.png", upload_buffer, "image/png")},
    )

    assert response.status_code == 200


def test_generate_image_from_frame_file_rejects_two_whitespace_only_fills():
    client = TestClient(app)
    upload_buffer = BytesIO()
    Image.new("RGB", (2, 1), (255, 255, 255)).save(upload_buffer, format="PNG")
    upload_buffer.seek(0)

    response = client.post(
        "/images/frame-file",
        data={
            "inner_text": "   ",
            "outer_text": "   ",
        },
        files={"frame_image": ("frame.png", upload_buffer, "image/png")},
    )

    assert response.status_code == 422
