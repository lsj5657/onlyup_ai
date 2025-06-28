from dotenv import load_dotenv
import os
import openai
import ast

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_refrigerated_ingredients(data_dict):
    prompt = f"""
다음은 OCR을 통해 추출된 식품명과 수량 목록입니다. 이 목록에서 **냉장 보관 식재료만 추출**해 주세요.

📌 조건:
- 의미상 식재료에 해당하면 포함 (표준 목록 무시)
- 완제품, 음료, 조리식품, 소스류 등은 제외
- 단위는 g로 추정 (수량 × 일반적인 1개당 무게 기준)
- 유통기한은 냉장 보관 기준 일수로 추정 (숫자만, 단위 없음)
- 이름, 무게, 유통기한만 출력

📌 출력 형식:
[
  {{'ingredient': '이름', 'weight_g': '총중량g', 'shelf_life_days': 숫자}},
  ...
]

OCR 인식 결과:
{data_dict}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 OCR 식재료 정보를 정리해주는 보조 시스템이야."},
            {"role": "user", "content": prompt}
        ]
    )

    try:
        return ast.literal_eval(response['choices'][0]['message']['content'])
    except Exception as e:
        print("⚠️ 응답 파싱 실패:", e)
        return []
