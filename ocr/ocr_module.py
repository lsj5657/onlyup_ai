import requests
import time
import uuid

def call_clova_ocr(api_url, secret_key, image_base64):
    payload = {
        "version": "V2",
        "requestId": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "images": [{
            "format": "png",
            "name": "receipt",
            "data": image_base64
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "X-OCR-SECRET": secret_key
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        ocr_result = response.json()
        return response.status_code, extract_items_and_counts(ocr_result)
    else:
        return response.status_code, None

def extract_items_and_counts(response_json):
    items_info = {}

    try:
        items = response_json['images'][0]['receipt']['result']['subResults'][0]['items']
        for item in items:
            name = item.get('name', {}).get('text', '')
            count = item.get('count', {}).get('text', '')
            if name and count:
                items_info[name] = count
    except (KeyError, IndexError):
        print("응답 포맷이 예상과 다릅니다.")

    return items_info
