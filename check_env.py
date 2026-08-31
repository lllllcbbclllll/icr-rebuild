from paddleocr import PaddleOCR
from mistralai.client import Mistral
from dotenv import load_dotenv
import os

load_dotenv()

ocr = PaddleOCR()
print("OCR ok")

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
r = client.chat.complete(
    model="mistral-small-latest",
    messages=[{"role": "user", "content": "say ok"}],
)
print("Mistral ok:", r.choices[0].message.content)