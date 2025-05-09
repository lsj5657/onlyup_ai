import asyncio
import websockets
import sounddevice as sd
import numpy as np
import simpleaudio as sa
import io
import soundfile as sf
from gtts import gTTS
from pydub import AudioSegment

# 🎯 마이크 기본 디바이스 정보 가져오기
device_info = sd.query_devices(0, 'input')
SAMPLE_RATE = int(device_info['default_samplerate'])
print(f"👉 사용 샘플레이트: {SAMPLE_RATE} Hz")

CHUNK_DURATION = 0.5  # 0.5초 청크
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

async def send_audio(websocket):
    loop = asyncio.get_event_loop()

    def callback(indata, frames, time, status):
        if status:
            print(f"⚠️ 마이크 상태 오류: {status}")
        else:
            print(f"🎧 청크 캡처됨, 전송 중... (크기: {len(indata)})")

        audio_bytes = indata.tobytes()
        asyncio.run_coroutine_threadsafe(websocket.send(audio_bytes), loop)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=callback,
        dtype='int16',      # LINEAR16 포맷
        blocksize=CHUNK_SIZE
    ):
        print("🎤 실시간 마이크 전송 중... (중지: Ctrl+C)")
        while True:
            try:
                result = await websocket.recv()

                if isinstance(result, bytes):
                    print("🔊 오디오 응답 수신, 재생 중...")
                    wav_fp = io.BytesIO(result)
                    data, samplerate = sf.read(wav_fp, dtype='int16')

                    play_obj = sa.play_buffer(
                        data.tobytes(),
                        num_channels=1,
                        bytes_per_sample=2,
                        sample_rate=samplerate
                    )
                else:
                    print(f"📝 서버 인식 결과: {result}")
                    print(f"받은 데이터 타입: {type(result)}, 크기: {len(result)}")

                    # 🆕 클라이언트에서 직접 TTS 생성 및 재생
                    if result.strip():
                        print("🗣️ 클라이언트에서 TTS 생성 및 재생 시작...")
                        tts = gTTS(result, lang='ko')
                        mp3_fp = io.BytesIO()
                        tts.write_to_fp(mp3_fp)
                        mp3_fp.seek(0)

                        # mp3 -> wav 변환
                        audio = AudioSegment.from_file(mp3_fp, format="mp3")
                        wav_fp = io.BytesIO()
                        audio.export(wav_fp, format="wav")
                        wav_fp.seek(0)
                        data, samplerate = sf.read(wav_fp, dtype='int16')

                        play_obj = sa.play_buffer(
                            data.tobytes(),
                            num_channels=1,
                            bytes_per_sample=2,
                            sample_rate=samplerate
                        )
                        print("✅ 클라이언트 TTS 재생 완료")

            except websockets.exceptions.ConnectionClosed:
                print("🚫 서버와의 연결 종료")
                break

async def main():
    uri = "ws://localhost:8000"
    async with websockets.connect(uri) as websocket:
        print("✅ WebSocket 연결됨, 실시간 스트리밍 시작")
        await send_audio(websocket)

try:
    asyncio.run(main())
except Exception as e:
    print(f"❗ 클라이언트 에러 발생: {e}")
