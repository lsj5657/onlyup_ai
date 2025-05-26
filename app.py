from fastapi import FastAPI, WebSocket
from llm.server import transcribe_and_respond

app = FastAPI()  # ✅ 먼저 선언해야 함

# ✅ WebSocket 엔드포인트
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await transcribe_and_respond(websocket)

# ✅ 테스트용 GET API
@app.get("/test")
async def test():
    return { "message": "hello world" }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
