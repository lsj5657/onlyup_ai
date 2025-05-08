import asyncio
import websockets
import whisper
import numpy as np
import tempfile
import soundfile as sf
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


model = whisper.load_model("base")
SAMPLE_RATE = 16000
MINIMUM_AUDIO_SIZE = SAMPLE_RATE * 2  # 2초 분량 (32000 bytes)

async def transcribe_audio(websocket):
    print("클라이언트 연결됨")
    try:
        async for message in websocket:
            print(f"전체 오디오 수신 (크기: {len(message)} bytes)")
            audio_array = np.frombuffer(message, dtype=np.int16)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                tmp_path = tmpfile.name
                sf.write(tmp_path, audio_array, SAMPLE_RATE)

            try:
                print("WAV 파일 저장 완료, Whisper STT 시작")
                result = model.transcribe(tmp_path, language="ko")
                text = result["text"]
                print(f"인식 결과: {text}")
                if text.strip():
                    await websocket.send(text)
                else:
                    print("빈 결과, 전송 안 함")
            except Exception as e:
                print(f"STT 처리 중 에러: {e}")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"클라이언트 연결 종료: {e}")
    except Exception as e:
        print(f"서버 에러: {e}")


async def main():
    print("서버 실행 중 (ws://0.0.0.0:8000)")
    async with websockets.serve(transcribe_audio, "0.0.0.0", 8000):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
