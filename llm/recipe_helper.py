from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)

recipe_steps = [
    "먼저 양파를 깍둑썰기 해주세요.",
    "프라이팬에 기름을 두르고 양파를 볶아주세요.",
    "양파가 투명해지면 계란을 넣고 잘 저어줍니다.",
    "소금을 한 꼬집 넣고 마무리합니다.",
]

step_index = 0

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
    return action, message

# 시작 메시지
print("🍳 요리를 시작합니다!")
print("🔊 음성 출력:", recipe_steps[step_index])  # 첫 단계 안내

while step_index < len(recipe_steps):
    user_input = input("👤 사용자: ")

    system_prompt = (
        f"너는 레시피 요리 도우미야. 사용자의 발화를 보고 지금 단계에서 무엇을 해야 할지 판단해. "
        f"현재 단계는 {step_index + 1}단계이고 내용은 다음과 같아: '{recipe_steps[step_index]}'.\n"
        f"- 사용자가 완료했다고 말하면 행동: [NEXT]\n"
        f"- 다시 설명해달라고 하면 행동: [REPLAY]\n"
        f"- 그 외의 경우는 행동: [WAIT]\n"
        f"메시지는 사용자에게 TTS로 읽어줄 내용이야.\n\n"
        f"[출력 형식]\n메시지: ~~~~\n행동: [NEXT|REPLAY|WAIT]"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]

    try:
        response = llm.invoke(messages)
        action, message = extract_action_and_message(response.content)

        print("🤖 LLM 응답:")
        print(f"메시지:", message)
        print(f"행동: [{action}]")


        if action == "NEXT":
            step_index += 1
            if step_index < len(recipe_steps):
                print("➡️ 다음 단계 안내:")
                print("🔊 음성 출력:", recipe_steps[step_index])
            else:
                print("🎉 요리를 완료했습니다!")
                break
        elif action == "REPLAY":
            print("🔁 현재 단계 다시 안내:")
            print("🔊 음성 출력:", recipe_steps[step_index])
        else:
            print("⏳ 다음 단계로 넘어가지 않음. 현재 단계를 유지합니다.")

    except Exception as e:
        print(f"❗ 오류 발생: {e}")
