from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


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
            "output_font_size": 2,
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
