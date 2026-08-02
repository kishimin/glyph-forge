import warnings
from io import BytesIO

from PIL import Image
from starlette.datastructures import UploadFile

MAX_UPLOADED_IMAGE_BYTES = 2 * 1024 * 1024
MAX_UPLOADED_IMAGE_WIDTH = 204
MAX_UPLOADED_IMAGE_HEIGHT = 204
MAX_UPLOADED_IMAGE_PIXELS = 41_616
ALLOWED_UPLOADED_IMAGE_FORMATS = frozenset({"PNG", "JPEG", "WEBP"})


class _UploadImageValidationError(ValueError):
    pass


def _validate_image_metadata(img: Image.Image) -> None:
    if img.format not in ALLOWED_UPLOADED_IMAGE_FORMATS:
        raise _UploadImageValidationError(
            "frame_image format must be PNG, JPEG, or WEBP"
        )
    if getattr(img, "is_animated", False) or getattr(img, "n_frames", 1) > 1:
        raise _UploadImageValidationError("frame_image must not be animated")
    if img.width > MAX_UPLOADED_IMAGE_WIDTH or img.height > MAX_UPLOADED_IMAGE_HEIGHT:
        raise _UploadImageValidationError(
            "frame_image width and height must not exceed 204 pixels"
        )
    if img.width * img.height > MAX_UPLOADED_IMAGE_PIXELS:
        raise _UploadImageValidationError(
            "frame_image pixel count must not exceed 41616"
        )


def _decode_image(image_bytes: bytes) -> Image.Image:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(image_bytes)) as img:
                _validate_image_metadata(img)
                img.load()
                _validate_image_metadata(img)
                return img.copy()
    except _UploadImageValidationError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValueError("frame_image exceeds safe decode limits") from error
    except Exception as error:
        raise ValueError("frame_image must be a valid image") from error


async def load_uploaded_image(frame_image: UploadFile) -> Image.Image:
    image_bytes = await frame_image.read(MAX_UPLOADED_IMAGE_BYTES + 1)
    if len(image_bytes) > MAX_UPLOADED_IMAGE_BYTES:
        raise ValueError(
            f"frame_image must not exceed {MAX_UPLOADED_IMAGE_BYTES} bytes"
        )
    return _decode_image(image_bytes)
