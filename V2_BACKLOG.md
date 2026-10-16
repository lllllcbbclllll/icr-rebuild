# V2 Backlog

v1 範圍：單張圖片 → OCR → LLM 抽取 → Pydantic 驗證 → JSON。
以下都是 v1 之後才做的事。列在這裡是為了「知道它存在但現在不做」。

---

## 一、評估基礎建設

優先做這一區。沒有評估層，下面所有「對比實驗」都做不了。

### QR code 自動 ground truth ⭐ 最高價值
- 電子發票證明聯的 QR code 內含結構化資料：發票字軌號碼、開立日期（民國年）、
  隨機碼、銷售額、總計額、買賣雙方統編。金額為十六進位編碼。
- 規格書見財政部電子發票整合服務平台。
- 用 opencv 解碼（`opencv-contrib-python` 已安裝，內建 QR 解碼，不需另裝套件）。
- **意義**：每張發票自帶零誤差標註，解掉長期的標註資料瓶頸。
  拍 100 張就有 100 筆 ground truth，不需人工標記。
- 限制：只有電子發票證明聯有 QR，傳統發票沒有。
  → 有 QR 的做規模化自動評估；傳統發票做困難案例的手工分析。兩者目的不同。

### promptfoo 評估層
- 批次測試、prompt 版本對比。
- prompt 以檔名做版控（`invoice_v1.md`、`invoice_v2.md`），promptfoo 可直接指定多檔對比。

### 指標
- per-field precision / recall / F1
- validation failure rate（比 ground truth 比對更早能看到的訊號）
- 錯誤分類統計，至少要能分開：
  1. API 呼叫失敗（基礎設施）
  2. 回傳非合法 JSON（格式崩壞）
  3. JSON 合法但 Pydantic 擋下（格式錯誤）
  4. 驗證通過但全為 None（抽取失敗，會靜默通過，需另外判斷）

### 模型版本控制
- promptfoo 的 providers 設定同樣須釘死版本，不可用 -latest 別名。
- 每次評估結果需連同 model ID 一起記錄，否則跨時間的數據無法比較。
- 已觀察到的版本差異：同一份 OCR 輸入與 prompt 下，
  gemini-3.6-flash 的「賣方名稱」為空，gemini-3.5-flash 抽到
  「燦坤實業股份有限公司」。單一欄位的 recall 因模型版本而異。
  → 這類差異若無 per-field 比對會完全看不到，是評估層存在的直接理由。

### 效能：規模化評估的時間成本(實測)
單張處理實測(gemini-3.5-flash 免費層、M4/16GB)：
- OCR：約 25 秒/張(每次執行都重新載入模型，@lru_cache 只在同一 process 內有效)
- LLM：約 12-13.5 秒/張，三次測試穩定，非啟動成本，是免費層常態延遲
  (已排除 client 建立與連線握手，重用 client 救不了)

推算至評估規模：
- 100 張一輪 ≈ OCR 42 分 + LLM 22 分 ≈ 1 小時
- 3 個 prompt 版本 × 每版 3 次(需量測 variance) = 9 輪 ≈ 9 小時

因此兩件事從「優化」升級為「必要」：
1. **OCR 快取必須架構化**。同一批圖片在不同 prompt 版本間，
   OCR 結果應完全重用 —— 那 42 分鐘只該付一次。
   目前 data/ocr_cache/ 是手動存檔，需正式納入 pipeline。
2. **LLM 呼叫需並行**。但免費層有 RPM 上限，並行度有天花板，需節流控制。

備註：效能問題在單張測試時不可見，規模化評估時成為主要瓶頸。

---

## 二、對比實驗

每一條都是 promptfoo 的題目。做完可以寫成內容。

### HTML table 清洗 vs 不清洗
PaddleOCR-VL 輸出的表格是 HTML（含 `style='text-align: center; word-wrap: break-word;'`
這類樣式屬性），對 LLM 是純雜訊且吃 token。
比較：清洗成精簡 Markdown table vs 原樣送入，對準確度與 token 數的影響。

### prompt 約束 vs schema 約束
`field_validator` 不會進 JSON Schema，`Field(pattern=...)` 會。
- 加 pattern：模型生成時就被約束，準確率上升，但量不到模型原本的能力
  （validation failure rate 會永遠是 0）
- 不加：看得到真實錯誤分佈
比較兩者效果。若要同時取得「強約束」與「可量測」，需拆成
`InvoiceRaw`（寬鬆，給模型）/ `InvoiceData`（嚴格，驗證）兩個 model。

### 純 OCR 文字 vs OCR + 原圖並用
v1 架構只傳純文字給 LLM，圖片沒有傳過去。
（因此 prompt 中「參考原始圖片」類規則在 v1 為無效指令，已移除。）

### few-shot examples
自評為目前最大的 prompt gap。注意：累積否定式規則會造成 prompt 膨脹與遵循度下降，
正面規則 + 反例優於一長串禁止事項。

---

## 三、能力擴充

### 欄位
- 加回：發票名稱、買方名稱、買方統編、稅額
- 品項明細 `items: list[Item]` — **這時候巢狀結構才真的需要**
  （v1 用扁平是因為每個欄位一對一；有重複資料才需要階層）

### 跨欄位驗證（`model_validator`，即第四級驗證）
- 未稅 + 稅額 ≈ 合計
- 統編 checksum（不只驗 8 碼數字，驗是否為合法統編）
  → 能抓到 OCR 把 3 認成 8 這類單字元錯誤
- 交易日期不得為未來

---

## 四、系統化

- **Agent 式自我修正**：驗證失敗時讓模型自行決定如何處理，
  而非寫死 retry 邏輯。這才是 agent 架構（tool use + loop + 自主決策）。
- FastAPI 包成服務
- Streamlit / Gradio 介面（上傳、看結果、看評估）
- Docker 化 + 部署（Railway / Render / Fly.io），取得公開網址

### 錯誤重試策略
- 區分可重試錯誤（429 rate limit、逾時、5xx）與不可重試錯誤（401、403、schema 錯誤）
- 指數退避（exponential backoff）、最大重試次數
- mistralai SDK 內建 RetryConfig 可用
- 這是 agent 式自我修正的第一步

---

## 五、難度階梯

依序推進，不要一次跳到最難：

1. 乾淨電子發票
2. 自己拍的實體發票（光線、角度）
3. 點陣字傳統發票
4. 影印 / 傳真件
5. 皺褶、歪斜嚴重

### 已知的 OCR 失效模式（traditional_01.jpg 實測）
數字辨識全對（631 / 631 / 1000 / 369），中文字有系統性錯誤：

| 正確 | OCR 結果 | 類型 |
|---|---|---|
| 收執聯 | 收款联 | 字元錯 + 簡體 |
| 老先覺 | 老先赞 | 字元錯 |
| 花壇 | 花镇 | 字元錯 + 簡體 |
| 餐飲消費 | 餐欲消费 | 字元錯 + 簡體 |
| 實收 | 宝收 | 字元錯 |
| 找零 | 找款 | 字元錯 |
| 01-user | B1-USER | 0 → B |
| 631TX | （整行消失） | **漏字，recall failure** |

兩個系統性發現：
1. **繁簡混雜**（额 / 费 / 联 / 镇 / 税）— PaddleOCR 中文模型以簡體為主，
   是系統性偏差不是隨機錯誤。驗店名不能只做字串比對。
2. **整行漏失** — 認錯是 precision 問題，漏掉是 recall 問題，成因與修法不同。

→ 可獨立寫成一篇：「PaddleOCR-VL 在點陣字發票上的失效模式分析」。
   有實測數據，不是二手資料。

---

## 已知待爆的坑

- `Decimal` 轉 JSON Schema 會產生 `anyOf: [number, string]`，
  加上 Optional 變成三路 union。structured output 的 strict 模式對巢狀 anyOf
  支援程度各家不一，可能報錯或靜默降級。
  → 若 Mistral 回報 schema 錯誤，這裡是第一嫌疑犯。
  解法：改 `str | None` 在 validator 內轉 Decimal，或用 `Annotated` 覆寫 JSON Schema。

- `temperature=0` 不保證完全 determinism。浮點運算順序等因素會讓同輸入偶爾產生
  不同輸出。評估時同張圖跑兩次結果不同，不一定是 bug。
