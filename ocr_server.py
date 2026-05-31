import base64
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from paddleocr import PaddleOCR

app = FastAPI()

# Izinkan React (frontend) mengirim data ke sini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ocr = PaddleOCR(use_angle_cls=True, lang="en")

class ImageData(BaseModel):
    image: str 

@app.post("/scan-base64/")
async def scan_base64(data: ImageData):
    # Ubah base64 dari React menjadi file gambar sementara
    img_bytes = base64.b64decode(data.image)
    with open("temp.jpg", "wb") as f:
        f.write(img_bytes)
        
    # Baca gambar
    result = ocr.ocr("temp.jpg")
    os.remove("temp.jpg") # Hapus setelah dibaca
    
    # Kumpulkan teksnya
    extracted_text = [line[1][0] for line in result[0]] if result and result[0] else []
            
    return {"data": extracted_text}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)