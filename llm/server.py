import asyncio
import websockets
from google.cloud import speech
import warnings
import tempfile
import soundfile as sf
import numpy as np
import time

warnings.filterwarnings("ignore", category=UserWarning)

SAMPLE_RATE = 48000
BUFFER_SECONDS = 5
BUFFER_SIZE = SAMPLE_RATE * BUFFER_SECONDS
SILENCE_THRESHOLD = 100       # 무음으로 간주할 에너지 기준
SILENCE_FRAMES = 3            # 몇 프레임 연속 무음이면 버퍼를 전송할지

client = speech.SpeechClient()

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=SAMPLE_RATE,
    language_code="ko-KR"
)

async def transcribe_audio(websocket):
    print("✅ 클라이언트 연결됨")
    buffer = bytearray()
    start_time = None
    silence_counter = 0
    previous_transcript = ""

    try:
        async for message in websocket:
            print(f"🎧 오디오 청크 수신! 크기: {len(message)} bytes")
            buffer.extend(message)

            if start_time is None:
                start_time = time.time()

            # 🎯 무음 여부 판단
            audio_chunk = np.frombuffer(message, dtype=np.int16).astype(np.float32)
            energy = np.sqrt(np.mean(audio_chunk**2))

            if energy < SILENCE_THRESHOLD:
                silence_counter += 1
                print(f"🔇 무음 감지 {silence_counter}/{SILENCE_FRAMES}")
            else:
                silence_counter = 0

            # 무음이 일정 시간 지속되면 STT 수행
            if silence_counter >= SILENCE_FRAMES or (len(buffer) >= BUFFER_SIZE):
                print(f"🚀 STT 조건 충족 → 데이터 모음 완료, STT 요청 시작")

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                    audio_array = np.frombuffer(buffer, dtype=np.int16)
                    sf.write(tmpfile.name, audio_array, SAMPLE_RATE)
                    tmp_path = tmpfile.name

                with open(tmp_path, "rb") as f:
                    audio_data = f.read()

                audio = speech.RecognitionAudio(content=audio_data)
                response = client.recognize(config=config, audio=audio)

                if response.results:
                    transcript = response.results[0].alternatives[0].transcript.strip()
                    if transcript and transcript != previous_transcript:
                        print(f"📝 인식 결과: {transcript}")
                        await websocket.send(transcript)
                        previous_transcript = transcript
                    else:
                        print("⚠️ 중복 또는 빈 인식 결과")
                else:
                    print("⚠️ 인식 결과 없음")

                buffer = bytearray()
                start_time = None
                silence_counter = 0

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
