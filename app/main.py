from fastapi import FastAPI, responses
from pydantic import BaseModel
from glyph_forge.services.convert_to_image import text_2_text_img
from io import BytesIO
class GenerateImageRequest(BaseModel):
    frame_text: str
    inner_text: str
    outer_text: str

    frame_columns: int
    frame_rows: int

    frame_font_size: int
    output_font_size: int

app = FastAPI()

@app.post("/images")
def generate_image(generateImageRequest: GenerateImageRequest):
    if not generateImageRequest.inner_text:
        raise ValueError("Enter a non-empty value for inner_text")
    if not generateImageRequest.outer_text:
        raise ValueError("Enter a non-empty value for outer_text")
    img = text_2_text_img(flame_text=generateImageRequest.frame_text, inner_text=generateImageRequest.inner_text, outer_text=generateImageRequest.outer_text,
                        horizontal_len=generateImageRequest.frame_columns, vertical_len=generateImageRequest.frame_rows, 
                        text_size=generateImageRequest.frame_font_size, final_text_size=generateImageRequest.output_font_size)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return responses.StreamingResponse(buffer, media_type="image/png")