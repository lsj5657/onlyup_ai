import asyncio
import websockets
import sounddevice as sd
import numpy as np
import simpleaudio as sa
import io
import soundfile as sf
from gtts import gTTS
from pydub import AudioSegment
import json

recipe_steps = [
    "먼저 양파를 깍둑썰기 해주세요.",
    "프라이팬에 기름을 두르고 양파를 볶아주세요.",
    "양파가 투명해지면 계란을 넣고 잘 저어줍니다.",
    "소금을 한 꼬집 넣고 마무리합니다."
]

device_info = sd.query_devices(0, 'input')
SAMPLE_RATE = int(device_info['default_samplerate'])
CHUNK_DURATION = 0.5
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

async def send_audio(websocket):
    loop = asyncio.get_event_loop()

    def callback(indata, frames, time, status):
        if status:
            print(f"⚠️ 마이크 상태 오류: {status}")
        else:
            asyncio.run_coroutine_threadsafe(websocket.send(indata.tobytes()), loop)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=callback,
        dtype='int16',
        blocksize=CHUNK_SIZE
    ):
        print("🎤 음성 전송 중... (Ctrl+C 중단)")
        while True:
            try:
                result = await websocket.recv()
                data = json.loads(result)

                msg_type = data.get("type")
                message = data.get("message", "").strip()
                if not message:
                    continue

                if msg_type == "speak":
                    print(f"🗣️ 사용자 요청 응답: {message}")
                elif msg_type == "step":
                    print(f"➡️ 다음 단계: {message}")
                elif msg_type == "end":
                    print(f"🎉 완료 안내: {message}")
                    break

                # TTS 재생
                tts = gTTS(message, lang='ko')
                mp3_fp = io.BytesIO()
                tts.write_to_fp(mp3_fp)
                mp3_fp.seek(0)
                audio = AudioSegment.from_file(mp3_fp, format="mp3")
                wav_fp = io.BytesIO()
                audio.export(wav_fp, format="wav")
                wav_fp.seek(0)
                data, samplerate = sf.read(wav_fp, dtype='int16')

                sa.play_buffer(
                    data.tobytes(),
                    num_channels=1,
                    bytes_per_sample=2,
                    sample_rate=samplerate
                )

            except websockets.exceptions.ConnectionClosed:
                print("🚫 서버 연결 종료")
                break

async def main():
    uri = "ws://localhost:8000"
    async with websockets.connect(uri) as websocket:
        # 1. 레시피 전송
        await websocket.send(json.dumps(recipe_steps))

        # 2. 서버 응답 대기
        init_ack = await websocket.recv()
        print(f"📡 서버 응답: {init_ack}")

        # 3. 이후 음성 전송 시작
        await send_audio(websocket)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❗ 클라이언트 에러: {e}")
