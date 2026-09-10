from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from src.ocr import image_to_markdown
from src.schemas import InvoiceData

load_dotenv()

def extract_invoice(markdown: str) -> str:
    prompt = (Path(__file__).parent.parent / "prompts" / "invoice_v1.md").read_text()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    r = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=markdown,
        config=types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=0,
            response_mime_type="application/json",
            response_schema=InvoiceData,
        ),
    )

    if r.text is None:
        raise ValueError("模型回傳空內容")

    return r.text


if __name__ == "__main__":
    markdown = image_to_markdown("data/samples/eletronic_01.png")
    print(extract_invoice(markdown))