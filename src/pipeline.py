from src.ocr import image_to_markdown
from src.extract import extract_invoice
from pydantic import ValidationError
from src.schemas import InvoiceData, ExtractionResult
import time
from google.genai.errors import APIError

def process_invoice(image_path: str):
    # ---- OCR ----
    t0 = time.perf_counter()
    try:
        markdown = image_to_markdown(image_path)
    except Exception as e:
        return ExtractionResult(
            status="failed",
            error_type="ocr_failed",
            error_detail=str(e),
            ocr_ms=(time.perf_counter() - t0) * 1000,
        )
    ocr_ms = (time.perf_counter() - t0) * 1000

    # ---- LLM ----
    t1 = time.perf_counter()
    try:
        raw = extract_invoice(markdown)
    except APIError as e:
        return ExtractionResult(
            status="failed",
            error_type=<依 e.code 判斷>,
            error_detail=str(e),
            ocr_ms=ocr_ms,
            llm_ms=(time.perf_counter() - t1) * 1000,
        )
    except ValueError as e:
        return ExtractionResult(... error_type="empty_response" ...)
    llm_ms = (time.perf_counter() - t1) * 1000

    try:
        invoice = InvoiceData.model_validate_json(raw)
    except ValidationError as e:
        return ExtractionResult(
            status="failed",
            error_type="validation_failed",
            error_detail=e.errors(),
            raw_output=raw,
            ocr_ms=ocr_ms,
            llm_ms=llm_ms,
        )
    
    return ExtractionResult(
        status="ok",
        data=invoice,
        raw_output=raw,
        ocr_ms=ocr_ms,
        llm_ms=llm_ms,
    )

def _classify_api_error(code: int) -> str:
    if code == 429:
        return "api_rate_limited"
    if code >= 500:
        return "api_unavailable"
    return "api_invalid_request"

if __name__ == "__main__":
    result = process_invoice("data/samples/eletronic_01.png")
    print(result.model_dump(by_alias=True))