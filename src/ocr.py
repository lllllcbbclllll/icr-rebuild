"""PaddleOCR-VL 封裝:吃圖片路徑,回傳辨識後的 Markdown 字串。

這一層只負責 OCR 辨識,不做任何欄位抽取或語意判斷。
"""

from __future__ import annotations

from functools import lru_cache

from paddleocr import PaddleOCRVL


@lru_cache(maxsize=1)
def _get_engine() -> PaddleOCRVL:
    return PaddleOCRVL()


def image_to_markdown(image_path: str) -> str:
    """對單張圖片執行 PaddleOCR-VL 辨識,回傳 Markdown 字串。"""
    engine = _get_engine()
    results = engine.predict(image_path)
    markdown_list = [res.markdown for res in results]
    markdown_text = engine.concatenate_markdown_pages(markdown_list)
    return markdown_text.strip()
