import asyncio
import websockets
import sounddevice as sd
import numpy as np
import simpleaudio as sa
import soundfile as sf
import io

SAMPLE_RATE = 16000
TARGET_DURATION = 5  # 5초 분량
CHUNK_DURATION = 0.5
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
BUFFER_SIZE = int(SAMPLE_RATE * TARGET_DURATION)

async def send_audio(websocket):
    loop = asyncio.get_event_loop()
    audio_buffer = []

    def callback(indata, frames, time, status):
        if status:
            print(f"마이크 상태 오류: {status}")
        audio_buffer.append((indata * 32767).astype(np.int16))

        total_samples = sum(len(chunk) for chunk in audio_buffer)
        if total_samples >= BUFFER_SIZE:
            print(f"{TARGET_DURATION}초 분량 모음 완료, 전송")
            combined = np.concatenate(audio_buffer)
            audio_bytes = combined.tobytes()
            asyncio.run_coroutine_threadsafe(websocket.send(audio_bytes), loop)
            audio_buffer.clear()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=callback,
        dtype='float32',
        blocksize=CHUNK_SIZE
    ):
        print("마이크로부터 음성 전송 중...")
        while True:
            try:
                result = await websocket.recv()
                print(f"서버 응답 수신")

                if isinstance(result, bytes):
                    print("오디오 수신, 재생 중...")

                    # WAV 데이터 → numpy array로 변환해서 재생
                    wav_fp = io.BytesIO(result)
                    data, samplerate = sf.read(wav_fp, dtype='int16')

                    play_obj = sa.play_buffer(
                        data.tobytes(),
                        num_channels=1,
                        bytes_per_sample=2,
                        sample_rate=samplerate
                    )
                    # play_obj.wait_done()  # 필요 시 블로킹

                else:
                    print(f"텍스트 응답: {result}")

            except websockets.exceptions.ConnectionClosed:
                print("서버와의 연결이 종료되었습니다.")
                break

async def main():
    uri = "ws://localhost:8000"
    async with websockets.connect(uri) as websocket:
        print("WebSocket 연결됨, 마이크 시작!")
        await send_audio(websocket)

try:
    asyncio.run(main())
except Exception as e:
    print(f"클라이언트 에러 발생: {e}")
