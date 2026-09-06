import time
from pathlib import Path

import pytest
from PIL import Image

from app.image_worker import ImageGenerationTimeout, run_image_generation_in_process


def _write_after_delay(started_path: str, completed_path: str) -> Image.Image:
    Path(started_path).write_text("started", encoding="utf-8")
    time.sleep(5)
    Path(completed_path).write_text("completed", encoding="utf-8")
    return Image.new("RGB", (1, 1), (255, 255, 255))


def test_timeout_stops_worker_before_later_side_effect(tmp_path):
    started_path = tmp_path / "worker-started"
    completed_path = tmp_path / "worker-completed"

    with pytest.raises(ImageGenerationTimeout):
        # Windows spawn startup varies enough that a subsecond deadline can expire
        # before the renderer starts, which would not exercise worker termination.
        run_image_generation_in_process(
            _write_after_delay,
            (str(started_path), str(completed_path)),
            {},
            2,
        )
    time.sleep(0.3)

    assert started_path.exists()
    assert not completed_path.exists()
