from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

from app.main import app
from app.schemas import GenerateImageRequest


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
            "max_chars_per_line": 5,
            "frame_font_size": 10,
            "output_font_size": 10,
            "inner_color": [255, 0, 0],
            "outer_color": [0, 0, 255],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


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


def test_generate_image_rejects_non_positive_options():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "A",
            "inner_text": "x",
            "outer_text": ".",
            "max_chars_per_line": 0,
        },
    )

    assert response.status_code == 422


def test_generate_image_request_accepts_64_chars_per_line():
    request = GenerateImageRequest(
        frame_text="A" * 64,
        inner_text="x",
        outer_text=".",
        max_chars_per_line=64,
    )

    assert request.max_chars_per_line == 64


def test_generate_image_request_normalizes_text_before_enforcing_limits():
    request = GenerateImageRequest(
        frame_text="e\u0301" * 64,
        inner_text="x" * 128,
        outer_text="." * 128,
        max_chars_per_line=64,
        frame_font_size=8,
        output_font_size=10,
    )

    assert request.frame_text == "é" * 64


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


def test_generate_image_rejects_chars_per_line_above_frame_text_length():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "A",
            "inner_text": "x",
            "outer_text": ".",
            "max_chars_per_line": 2,
        },
    )

    assert response.status_code == 422


def test_generate_image_rejects_more_than_64_chars_per_line():
    client = TestClient(app)

    response = client.post(
        "/images",
        json={
            "frame_text": "A" * 65,
            "inner_text": "x",
            "outer_text": ".",
            "max_chars_per_line": 65,
        },
    )

    assert response.status_code == 422


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
