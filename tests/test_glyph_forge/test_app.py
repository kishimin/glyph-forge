from fastapi.testclient import TestClient

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
