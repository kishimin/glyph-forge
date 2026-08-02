import multiprocessing
from collections.abc import Callable
from io import BytesIO
from multiprocessing.connection import Connection
from typing import Any, Protocol

from PIL import Image


class ImageGenerationTimeout(Exception):
    pass


class ImageGenerationValueError(ValueError):
    pass


class ImageGenerationWorkerError(RuntimeError):
    pass


class _StoppableProcess(Protocol):
    def is_alive(self) -> bool: ...

    def join(self, timeout: float | None = None) -> None: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...


def _run_and_send_result(
    connection: Connection,
    operation: Callable[..., Image.Image],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    try:
        image = operation(*args, **kwargs)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        connection.send(("ok", buffer.getvalue()))
    except ValueError as error:
        connection.send(("value_error", str(error)))
    except Exception as error:
        connection.send(("worker_error", f"{type(error).__name__}: {error}"))
    finally:
        connection.close()


def _stop_process(process: _StoppableProcess) -> None:
    if not process.is_alive():
        process.join()
        return

    process.terminate()
    process.join(timeout=1)
    if process.is_alive():
        process.kill()
        process.join()


def run_image_generation_in_process(
    operation: Callable[..., Image.Image],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    timeout_seconds: float,
) -> bytes:
    context = multiprocessing.get_context("spawn")
    parent_connection, child_connection = context.Pipe(duplex=False)
    process = context.Process(
        target=_run_and_send_result,
        args=(child_connection, operation, args, kwargs),
        daemon=True,
    )
    process.start()
    child_connection.close()

    try:
        if not parent_connection.poll(timeout_seconds):
            raise ImageGenerationTimeout
        try:
            result_type, payload = parent_connection.recv()
        except EOFError as error:
            raise ImageGenerationWorkerError(
                "image generation worker exited without a result"
            ) from error
    finally:
        _stop_process(process)
        parent_connection.close()

    if result_type == "ok":
        return payload
    if result_type == "value_error":
        raise ImageGenerationValueError(payload)
    raise ImageGenerationWorkerError(payload)
