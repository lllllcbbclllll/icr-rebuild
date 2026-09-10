# ICR Rebuild

## 專案目的
個人技能建構專案。目標是我本人透過實作理解端到端的文件抽取系統,
不是快速產出一個能跑的 repo。

## 架構
兩段式管線:
圖片 → PaddleOCR-VL(輸出 Markdown)→ Mistral Small 3.2(欄位抽取)
→ Pydantic 驗證 → JSON

設計原則:OCR 層與 LLM 層只透過純文字/Markdown 介面溝通,兩層必須解耦,
以便日後抽換 OCR 引擎或比較「兩段式 vs vision model 直抽」。

## 目錄職責
- src/ocr.py      PaddleOCR 封裝:吃圖片路徑,回 Markdown 字串
- src/extract.py  呼叫 Mistral structured output:吃 Markdown + prompt,回 JSON
- src/schemas.py  Pydantic models 與 field validators
- src/pipeline.py 串接三層
- prompts/        prompt 獨立成檔,版本以檔名管理
- data/samples/   測試圖片(git ignored)
- data/ground_truth/ 人工標註(git ignored)

## 分工界線(重要)
- src/schemas.py 與 src/pipeline.py 由我自己撰寫。
  你可以在我要求時解釋或 review,但不要主動實作這兩個檔案。
- prompts/ 底下的內容由我自己撰寫。
- 其餘 boilerplate、SDK 呼叫寫法、錯誤處理樣板可以協助。
- 當我問「這段在做什麼」時,請解釋原理,不要直接改寫程式碼。

## 環境
- macOS, Apple Silicon
- Python 3.11, 以 uv 管理,執行一律走 `uv run python ...`
- 已安裝:paddleocr 3.7.0, paddlepaddle 3.3.1, mistralai 2.8.0, pydantic 2.13.4
- mistralai 為 2.x,SDK 寫法與 1.x 不同,不要使用 MistralClient 舊寫法
- mistralai 2.x:所有 import 走 mistralai.client(例:from mistralai.client import Mistral)
  不要使用 v1 的 from mistralai import Mistral 寫法

## 模型版本規則
- 一律使用釘死版本的 model ID(如 gemini-3.5-flash)，
  禁止使用 -latest 之類的別名(gemini-flash-latest)。
- 原因：別名指向的模型會隨時間改變，會讓評估結果無法比較。
  今天 F1 0.85、下個月 0.79，分不清是 prompt 改壞還是模型被換掉。
- 換模型版本必須是明確的決定，並記錄在 commit message 裡。
- 目前使用：gemini-3.5-flash
  (gemini-3.6-flash 因免費層 503 負載問題暫不使用)

## 現況
v1 階段:單張發票圖片 → 印出通過 Pydantic 驗證的 JSON。
評估層(promptfoo)為 v2,現在不要實作。