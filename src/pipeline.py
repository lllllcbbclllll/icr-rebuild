from src.ocr import image_to_markdown
from src.extract import extract_invoice
from src.schemas import ExtractionResult
import time

def process_invoice(image_path: str):
    t0 = time.perf_counter()
    markdown = image_to_markdown(image_path)
    ocr_ms = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    invoice = extract_invoice(markdown)
    llm_ms = (time.perf_counter() - t1) * 1000

    return ExtractionResult(
        status="ok",
        data=invoice,
        ocr_ms=ocr_ms,
        llm_ms=llm_ms,
    )

if __name__ == "__main__":
    result = process_invoice("data/samples/eletronic_01.png")
    print(result.model_dump(by_alias=True))