from io import BytesIO

from fastapi import FastAPI, HTTPException, responses

from app.schemas import GenerateImageRequest
from glyph_forge.services.convert_to_image import text_2_text_img

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/images")
def generate_image(generateImageRequest: GenerateImageRequest):
    if not generateImageRequest.inner_text:
        raise HTTPException(
            status_code=422, detail="Enter a non-empty value for inner_text"
        )
    if not generateImageRequest.outer_text:
        raise HTTPException(
            status_code=422, detail="Enter a non-empty value for outer_text"
        )
    img = text_2_text_img(
        flame_text=generateImageRequest.frame_text,
        inner_text=generateImageRequest.inner_text,
        outer_text=generateImageRequest.outer_text,
        config=generateImageRequest.to_config(),
    )
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return responses.StreamingResponse(buffer, media_type="image/png")
