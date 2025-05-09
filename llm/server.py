import asyncio
import websockets
from google.cloud import speech
import warnings
import tempfile
import soundfile as sf
import numpy as np
import time  # ✅ 시간 측정 추가

warnings.filterwarnings("ignore", category=UserWarning)

SAMPLE_RATE = 48000
BUFFER_SECONDS = 5  # 5초 단위
BUFFER_SIZE = SAMPLE_RATE * BUFFER_SECONDS

client = speech.SpeechClient()

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=SAMPLE_RATE,
    language_code="ko-KR"
)

async def transcribe_audio(websocket):
    print("✅ 클라이언트 연결됨")
    buffer = bytearray()
    start_time = None  # ✅ 수신 시작 시간

    try:
        async for message in websocket:
            print(f"🎧 오디오 청크 수신! 크기: {len(message)} bytes")
            buffer.extend(message)

            # 첫 데이터 들어올 때 시작 시간 기록
            if start_time is None:
                start_time = time.time()

            time_elapsed = time.time() - start_time

            if len(buffer) >= BUFFER_SIZE and time_elapsed >= BUFFER_SECONDS:
                print(f"🚀 {BUFFER_SECONDS}초 경과 & 데이터 모음 완료, STT 요청 시작")

                # WAV 파일로 저장
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                    audio_array = np.frombuffer(buffer, dtype=np.int16)
                    sf.write(tmpfile.name, audio_array, SAMPLE_RATE)
                    tmp_path = tmpfile.name

                # Google STT 요청
                with open(tmp_path, "rb") as f:
                    audio_data = f.read()

                audio = speech.RecognitionAudio(content=audio_data)

                response = client.recognize(
                    config=config,
                    audio=audio
                )

                if response.results:
                    transcript = response.results[0].alternatives[0].transcript
                    print(f"📝 인식 결과: {transcript}")
                    await websocket.send(transcript)
                else:
                    print("⚠️ 인식 결과 없음")

                # 버퍼 & 타이머 초기화
                buffer = bytearray()
                start_time = None

    except websockets.exceptions.ConnectionClosed:
        print("❗ 클라이언트 연결 종료")
    except Exception as e:
        print(f"❗ 서버 에러: {e}")

async def main():
    print("🚀 서버 실행 중 (ws://0.0.0.0:8000)")
    async with websockets.serve(transcribe_audio, "0.0.0.0", 8000):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
