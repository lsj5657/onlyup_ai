from .ocr_module import call_clova_ocr
from .ingredient_extractor import extract_refrigerated_ingredients

def process_receipt(image_base64, api_url, secret_key):
    status, extracted_data = call_clova_ocr(api_url, secret_key, image_base64)
    if status == 200 and extracted_data:
        result = extract_refrigerated_ingredients(extracted_data)
        return result
    else:
        print("OCR 실패 또는 인식된 데이터 없음")
        return []