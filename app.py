from fastapi import FastAPI, WebSocket
from llm.server import transcribe_and_respond

app = FastAPI()  # ✅ 먼저 선언해야 함

@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await transcribe_and_respond(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
