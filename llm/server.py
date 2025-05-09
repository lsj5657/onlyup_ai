import asyncio
import websockets
import whisper
import numpy as np
import tempfile
import soundfile as sf
from gtts import gTTS
from pydub import AudioSegment
import io
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

model = whisper.load_model("base")
SAMPLE_RATE = 16000

async def transcribe_audio(websocket):
    print("클라이언트 연결됨")
    try:
        async for message in websocket:
            print(f"전체 오디오 수신 (크기: {len(message)} bytes)")
            audio_array = np.frombuffer(message, dtype=np.int16)

            # 오디오 파일로 저장
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                tmp_path = tmpfile.name
                sf.write(tmp_path, audio_array, SAMPLE_RATE)

            try:
                print("WAV 파일 저장 완료, Whisper STT 시작")
                result = model.transcribe(tmp_path, language="ko")
                text = result["text"]
                print(f"인식 결과: {text}")

                if text.strip():
                    # TTS 생성
                    print("TTS 생성 중...")
                    tts = gTTS(text, lang='ko')
                    mp3_fp = io.BytesIO()
                    tts.write_to_fp(mp3_fp)
                    mp3_fp.seek(0)

                    # mp3 -> wav 변환
                    audio = AudioSegment.from_file(mp3_fp, format="mp3")
                    wav_fp = io.BytesIO()
                    audio.export(wav_fp, format="wav")
                    wav_fp.seek(0)
                    audio_bytes = wav_fp.read()

                    # WAV 바이너리 전송
                    await websocket.send(audio_bytes)
                    print("오디오 전송 완료")
                else:
                    print("빈 결과, 전송 안 함")

            except Exception as e:
                print(f"STT/TTS 처리 중 에러: {e}")

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
