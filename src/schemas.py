# 設計決策：單一 model，validator 不進 JSON Schema。
# 因此模型生成不受約束，validation failure 可作為品質訊號。
# 若 v2 要加 Field(pattern=...) 提升成功率，需拆成
# InvoiceRaw(寬鬆，給模型) / InvoiceData(嚴格，驗證) 以保留量測能力。

import re
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

class InvoiceData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    invoice_period: str | None = Field(default=None, alias="發票年期別")
    invoice_number: str | None = Field(default=None, alias="發票號碼")
    transaction_date: str | None = Field(default=None, alias="交易日期")
    seller_name: str | None = Field(default=None, alias="賣方名稱")
    seller_tax_id: str | None = Field(default=None, alias="賣方統編")
    total_amount: Decimal | None = Field(default=None, alias="合計")

    @field_validator("invoice_number")
    @classmethod
    def validate_invoice_number(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{2}\d{8}$", v):
            raise ValueError(f"發票號碼格式錯誤(應為 2 碼英文 + 8 碼數字): {v}")
        return v

    @field_validator("seller_tax_id")
    @classmethod
    def validate_seller_tax_id(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not re.match(r"^\d{8}$", v):
            raise ValueError(f"賣方統編格式錯誤(應為 8 碼數字): {v}")
        return v

    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(f"交易日期格式錯誤(應為 YYYY-MM-DD HH:MM:SS): {v}")
        return v

    @field_validator("invoice_period")
    @classmethod
    def validate_invoice_period(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if not re.match(r"^\d{2,3}年(0[1-9]|1[0-2])-(0[1-9]|1[0-2])月$", v):
            raise ValueError(f"發票年期別格式錯誤(應為 民國YYY年MM-MM月): {v}")
        return v

    @field_validator("total_amount", mode="before")
    @classmethod
    def blank_amount_to_none(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return v

class ExtractionResult(BaseModel):
    status: Literal["ok", "failed"]
    data: InvoiceData | None = None
    ocr_ms: float | None = None
    llm_ms: float | None = None
    fields_total: int = len(InvoiceData.model_fields)

if __name__ == "__main__":
    # 模擬 Mistral structured output 會吐出來的 dict(中文 key)
    fake_mistral_output = {
        "發票年期別": "113年01-02月",
        "發票號碼": "AB12345678",
        "交易日期": "2024-01-15 12:30:00",
        "賣方名稱": "測試商行",
        "賣方統編": "12345678",
        "合計": "1500",
    }

    invoice = InvoiceData(**fake_mistral_output)
    print("情境一:正常資料")
    print(invoice.model_dump(by_alias=True))

    # 故意帶一個格式錯誤的值,確認 validator 真的有攔下來
    bad_output = dict(fake_mistral_output)
    bad_output["發票號碼"] = "A1234567"  # 只有 1 碼英文,應該要噴錯
    try:
        InvoiceData(**bad_output)
    except Exception as e:
        print("\n情境二:格式錯誤(預期中的驗證失敗)")
        print(e)

    # LLM 給空字串,代表沒抓到
    blank_output = dict(fake_mistral_output)
    blank_output["發票號碼"] = ""
    blank_output["合計"] = ""
    blank = InvoiceData(**blank_output)
    print("\n情境三:空字串應變成 None")
    print(blank.model_dump(by_alias=True))

    # LLM 乾脆沒給那個 key
    missing_output = dict(fake_mistral_output)
    del missing_output["賣方統編"]
    missing = InvoiceData(**missing_output)
    print("\n情境四:整個 key 缺席也應變成 None")
    print(missing.model_dump(by_alias=True))
