from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel
from ocr.processor import process_receipt
from config import CLOVA_API_URL, CLOVA_KEY
import os

app = FastAPI()  # ✅ 앱 인스턴스

# ✅ WebSocket 엔드포인트
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    from llm.server import transcribe_and_respond
    await transcribe_and_respond(websocket)

# ✅ 테스트용 GET API
@app.get("/test")
async def test():
    return { "message": "hello world" }

# ✅ POST /ocr 요청 바디 스키마
class OCRRequest(BaseModel):
    image_base64: str


@app.post("/ocr")
async def ocr_handler(request: OCRRequest):
    image_base64 = request.image_base64

    if not CLOVA_API_URL or not CLOVA_KEY:
        raise HTTPException(status_code=500, detail="OCR API 설정 누락")

    try:
        result = process_receipt(image_base64, CLOVA_API_URL, CLOVA_KEY)
        return {"ingredients": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 처리 중 오류: {e}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
