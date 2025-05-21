import asyncio
import websockets
import tempfile
import json
import numpy as np
import soundfile as sf
from dotenv import load_dotenv
from google.cloud import speech
from fastapi import WebSocket
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

SAMPLE_RATE = 48000
SILENCE_THRESHOLD = 100
SILENCE_FRAMES = 3
BUFFER_SECONDS = 5
BUFFER_SIZE = SAMPLE_RATE * BUFFER_SECONDS

client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=SAMPLE_RATE,
    language_code="ko-KR"
)

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)

def extract_action_and_message(text: str):
    action = "WAIT"
    message = text.strip()
    if "행동:" in text:
        parts = text.split("행동:")
        message = parts[0].strip()
        action_line = parts[1].strip().splitlines()[0]
        if "[" in action_line and "]" in action_line:
            extracted = action_line.split("]")[0][1:].strip().upper()
            if extracted in {"NEXT", "REPLAY", "WAIT"}:
                action = extracted
    if message.lower().startswith("메시지:"):
        message = message[len("메시지:"):].strip(" '\"\n")
    return action, message


async def transcribe_and_respond(websocket: WebSocket):
    await websocket.accept()
    print("✅ WebSocket 연결 수락됨")

    try:
        # 초기 메시지: 레시피 JSON 수신
        init_message = await websocket.receive_text()
        recipe_steps = json.loads(init_message)

        if not isinstance(recipe_steps, list) or not all(isinstance(s, str) for s in recipe_steps):
            raise ValueError("레시피는 문자열 리스트여야 합니다.")

        print("📥 레시피 수신 완료:")
        for i, step in enumerate(recipe_steps, 1):
            print(f"  {i}. {step}")

        await websocket.send_text("레시피 수신 완료")

        # 첫 단계 전송
        await websocket.send_text(json.dumps({
            "type": "step",
            "message": recipe_steps[0]
        }))

        step_index = 0
        buffer = bytearray()
        silence_counter = 0
        previous_transcript = ""

        while True:
            data = await websocket.receive_bytes()
            buffer.extend(data)
            audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            energy = np.sqrt(np.mean(audio_chunk ** 2))
            silence_counter = silence_counter + 1 if energy < SILENCE_THRESHOLD else 0

            if silence_counter >= SILENCE_FRAMES or len(buffer) >= BUFFER_SIZE:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                    sf.write(tmpfile.name, np.frombuffer(buffer, dtype=np.int16), SAMPLE_RATE)
                    tmp_path = tmpfile.name

                with open(tmp_path, "rb") as f:
                    audio_data = f.read()

                audio = speech.RecognitionAudio(content=audio_data)
                response = client.recognize(config=config, audio=audio)

                if response.results:
                    transcript = response.results[0].alternatives[0].transcript.strip()
                    if transcript and transcript != previous_transcript:
                        print(f"📝 인식된 발화: {transcript}")

                        system_prompt = (
                            f"너는 요리 도우미야. 사용자의 발화를 듣고 행동을 [NEXT], [REPLAY], [WAIT] 중에서 정확하게 하나만 판단해줘.\n\n"
                            f"[현재 단계]: '{recipe_steps[step_index]}'\n\n"
                            f"[행동 기준]\n"
                            f"- 다음 표현이 들어 있으면 무조건 [NEXT]\n"
                            f"→ '다 했어', '끝났어', '완료', '다음 단계', '넘어가자', '다 만들었어'\n"
                            f"- 다음 표현이 들어 있으면 무조건 [REPLAY]\n"
                            f"→ '뭐라고', '다시', '다시 말해줘', '못 들었어', '한 번 더'\n"
                            f"- 위에 해당하지 않으면 [WAIT]\n\n"
                            f"[출력 형식]\n"
                            f"메시지: (사용자에게 읽어줄 말만 써. 절대 '메시지:'를 다시 쓰지 마!)\n"
                            f"행동: [NEXT|REPLAY|WAIT]"
                        )

                        messages = [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=transcript)
                        ]
                        response = llm.invoke(messages)
                        action, message = extract_action_and_message(response.content)

                        print(f"🤖 LLM 응답: {message} / 행동: [{action}]")

                        if action == "REPLAY":
                            await websocket.send_text(json.dumps({
                                "type": "speak",
                                "message": recipe_steps[step_index]
                            }))
                        elif action == "NEXT":
                            step_index += 1
                            if step_index < len(recipe_steps):
                                await websocket.send_text(json.dumps({
                                    "type": "step",
                                    "message": recipe_steps[step_index]
                                }))
                            else:
                                await websocket.send_text(json.dumps({
                                    "type": "end",
                                    "message": "🎉 요리를 완료했습니다!"
                                }))
                                break

                        previous_transcript = transcript

                buffer = bytearray()
                silence_counter = 0

    except Exception as e:
        print(f"❗ WebSocket 서버 처리 중 오류 발생: {e}")
        await websocket.close()