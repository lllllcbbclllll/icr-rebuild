# icr-rebuild

兩階段文件擷取 pipeline：把文件影像轉成經過驗證的結構化 JSON。

```
文件影像 → OCR（PaddleOCR-VL） → 純文字／Markdown → LLM 擷取（Gemini） → Pydantic 驗證 → JSON
```

## 為什麼做這個專案

我在工作上負責 LLM 文件擷取（ICR）的 prompt 設計與評測。這個專案是用公開資料、從零重建一套完整的擷取流程，目的是把「調 prompt」延伸到「設計並交付整個系統」：模組怎麼切、錯誤怎麼被看見、結果怎麼被驗證。

## 目前狀態

**v1 已完成**：OCR → LLM 擷取 → 結構化驗證，端對端可執行。

- `pipeline.py` 串接三個階段，並記錄各階段耗時
- 驗證失敗時不會中斷流程，而是保留原始輸出，方便分析模型錯在哪裡

## 設計決策

| 決策 | 理由 |
|---|---|
| OCR 與 LLM 之間只用純文字／Markdown 溝通 | 兩層解耦，任何一層都能單獨替換模型 |
| 所有欄位設為 `Optional` | 漏抓的欄位會留空而不是讓整筆失敗，才能量測 recall |
| 驗證規則不寫進給模型的 JSON Schema | 讓模型的原始錯誤樣態保持可見，而不是被 schema 掩蓋 |
| 輸出定義 schema 與驗證 schema 分開 | 「要求模型輸出什麼」和「怎麼判斷輸出對不對」是兩件事 |
| Prompt 以獨立 `.md` 檔存放、檔名帶版本 | 方便版本比較，也能直接接上 Promptfoo 做評測 |
| 驗證失敗時保留原始輸出 | 失敗本身就是要分析的資料，不該被丟掉 |

## 技術

Python · PaddleOCR-VL · Gemini（google-genai SDK）· Pydantic · uv

## 如何執行

```bash
# 安裝依賴
uv sync

# 設定 API key（不要 commit 這個檔案）
echo "GEMINI_API_KEY=你的key" > .env

# 執行
【執行指令，例如：uv run python pipeline.py 範例檔案路徑】
```

## 下一步（v2）

- [ ] 以 Promptfoo 建立自動評測，量測各欄位的 precision／recall
- [ ] 利用 QR code 自動產生 ground truth，擴大測試集
- [ ] 比較「在 prompt 中約束格式」與「用 schema 約束格式」的效果差異
- [ ] 實驗 HTML 表格清理對擷取正確率的影響
- [ ] 驗證失敗時的自我修正機制：由模型判斷如何處理失敗，而非走固定路徑
- [ ] 評估本地部署（Apple Silicon / MLX）的可行性
