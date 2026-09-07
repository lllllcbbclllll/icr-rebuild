from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from src.ocr import image_to_markdown
from src.schemas import InvoiceData

load_dotenv()

prompt = (Path(__file__).parent.parent / "prompts" / "invoice_v1.md").read_text()
markdown = image_to_markdown("data/samples/eletronic_01.png")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
r = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=markdown,
    config=types.GenerateContentConfig(
        system_instruction=prompt,
        temperature=0,
        response_mime_type="application/json",
        response_schema=InvoiceData,
    ),
)
print(r.text)