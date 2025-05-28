from dotenv import load_dotenv
import os

load_dotenv()

# 환경 변수 가져오기
CLOVA_API_URL = os.getenv("CLOVA_API_URL")
CLOVA_KEY = os.getenv("CLOVA_KEY")
