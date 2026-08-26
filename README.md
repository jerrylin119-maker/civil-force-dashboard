# 🚒 民力科業務執行與督勤彙整看板系統
> **Civil Force Operations & Inspection Dashboard System**  
> 專為消防局民力科（義消組織、民間救難團體、防救災演訓與督勤管理）量身打造之全方位業務看板與 AI 智能輔助平台。

---

## 🌟 核心功能亮點

1. **模組一：重點公文追蹤看板**
   - **時效智慧倒數**：公文依執行期限自動排序，提供 `< 3 天` 🚨 紅色急件警示與 `< 7 天` ⚠️ 黃色提醒。
   - **承辦人分流列管**：支援承辦人、公文類別、辦理狀態（未處理 / 辦理中 / 已結案）即時篩選與快速推進。
   - **雙重檢視與匯出**：提供適合手機操作的響應式卡片視圖與適合電腦大螢幕的詳細表格，支援匯出 UTF-8 BOM CSV / Excel。

2. **模組二：會議/邀請/訃聞圖文辨識與行事曆 (OCR + AI)**
   - **手機拍照與圖檔上傳**：現場以手機相機直接拍攝公文開會通知單、邀請卡或公祭訃聞。
   - **Gemini Vision 智能提取**：自動抽取事由、日期、時間、地點、行程類別、指定出席人員與公奠/服裝等備註。
   - **多元日曆檢視**：提供行程時間軸視圖（今日/本週/未來）、月曆全景檢視，並支援一鍵匯出 `.ics` 同步至 Google / Outlook 行事曆。

3. **模組三：督勤管理與報告產出機**
   - **半年督導覆蓋率看板**：自動分析過去 180 天轄內各大隊、分隊與義消組織之督勤頻率，以 🟢 綠色、🟡 黃色、🔴 紅色熱力色標呈現。
   - **本月優先督導單位推薦**：智慧演算法依據「督導次數最少」與「距上次督勤時間最久」自動排序本月最急需督導之單位。
   - **行動化現場速記與報告生成**：現場以手機勾選重點查核項目、輸入優缺點，一鍵生成格式化報告，支援直接匯出標準公務 **Word (.docx)**、**Markdown (.md)** 與純文字檔。

4. **模組四：新聞稿與致詞稿智慧生成機**
   - **六大活動情境範本**：常年訓練、裝備車輛捐贈、防救災演練、績優表揚春酒、因公傷病慰問、組織人事等。
   - **長官致詞講稿生成**：支援 **溫馨感人**、**激勵振奮**、**莊重正式** 三種演說風格自由切換。
   - **媒體發布新聞稿**：產出具備吸睛主副標題、倒金字塔導言、長官引言與聯絡人資訊的專業新聞稿。
   - **範本庫回存傳承**：滿意稿件一鍵回存資料庫，方便同仁未來微調再利用，支援 Word (.docx) 匯出。

5. **模組五：系統設定與資料庫管理**
   - 支援 Gemini API Key 動態設定與即時連線驗證。
   - 轄內消防/義消單位主檔管理與督勤重點項目庫自訂維護。
   - 本地 SQLite 資料庫完整備份下載與示範資料重設。

---

## 📁 專案檔案架構

```
civil_force_dashboard/
├── app.py                     # Streamlit 系統主程式 (導航、登入狀態、全局排版)
├── config.py                  # 系統全域設定、分隊單位主檔預設值、督勤項目定義
├── database.py                # SQLAlchemy ORM 模型、SQLite 連線與種子資料初始化
├── auth.py                    # 使用者驗證、密碼雜湊與身分權限管理
├── ai_helper.py               # Google Gemini Vision OCR 與致詞/新聞稿生成器 (含 Fallback 降級機制)
├── export_helper.py           # 督勤報告與稿件之 Word (.docx)、Markdown、CSV、iCal 匯出工具
├── requirements.txt           # Python 依賴套件清單
├── .env.example               # 環境變數範本檔
├── README.md                  # 本系統完整使用與部署說明手冊
├── static/
│   └── custom.css             # 專屬視覺主題與手機響應式排版 CSS
├── pages_modules/
│   ├── mod1_documents.py      # 模組一：重點公文追蹤看板
│   ├── mod2_calendar.py       # 模組二：會議/邀請/訃聞圖文辨識與行事曆
│   ├── mod3_inspection.py     # 模組三：督勤管理與半年覆蓋率看板
│   ├── mod4_speech_press.py   # 模組四：新聞稿與致詞稿智慧生成機
│   └── mod5_settings.py       # 模組五：系統設定與資料庫管理
└── uploads/                   # 圖文辨識與督勤照片上傳存放目錄
```

---

## 🚀 本機快速啟動指南

### 1. 準備環境與安裝依賴
確認已安裝 Python 3.10+，於終端機執行：
```bash
cd civil_force_dashboard
pip install -r requirements.txt
```

### 2. 設定 Google Gemini API Key (選填)
您可建立 `.env` 檔案或於系統啟動後至【系統設定】頁面輸入：
```bash
# 複製範本
copy .env.example .env
# 編輯 .env 填入您的 GEMINI_API_KEY
```
> 💡 *若未設定 API Key，系統會自動切換為內建智慧範本引擎，仍可正常體驗所有介面與功能！*

### 3. 啟動系統
```bash
streamlit run app.py
```
啟動後瀏覽器會自動開啟 `http://localhost:8501`。

---

## 📱 手機端連線使用教學 (區域網路 Wi-Fi)

本系統支援同仁於同一區域網路（消防局局內 Wi-Fi 或個人熱點）使用手機瀏覽器直接連線操作：

1. 電腦啟動 Streamlit 時，終端機會顯示 **Network URL**（例如：`http://192.168.1.100:8501`）。
2. 將手機連接至相同 Wi-Fi 網路。
3. 在手機 Safari / Chrome 瀏覽器輸入該 **Network URL** 即可開啟手機端專屬響應式介面，支援直接使用手機鏡頭拍照辨識！

---

## 🔐 預設測試帳號

系統內建 4 組展示身分（密碼統一為 `123456`，亦可使用登入頁面的「免密碼一鍵登入」）：

| 帳號 | 身分姓名 | 權限角色 | 適用情境 |
| :--- | :--- | :--- | :--- |
| `leader` | 王科長 | 科長 / 決策主管 | 審閱督勤覆蓋率、公文總覽、長官致詞稿生成 |
| `inspector1` | 張股長 | 督勤同仁 / 查核幹部 | 現場督勤填報、公文催辦、查核報告 Word 匯出 |
| `clerk1` | 陳科員 | 業務承辦人 / 科員 | 公文辦理進度更新、活動拍照 OCR 錄入行事曆 |
| `admin` | 系統管理員 | 系統管理員 | 單位主檔維護、督勤項目庫自訂、資料庫管理 |

---

## ☁️ 雲端免費部署指南

### 方法一：部署至 Streamlit Community Cloud (最推薦、完全免費)
1. 將專案資料夾上傳至您的 **GitHub Repository**。
2. 前往 [Streamlit Community Cloud](https://share.streamlit.io/) 並使用 GitHub 帳號登入。
3. 點擊 **New app**，選擇該 Repository、分支設為 `main`、主檔案設為 `app.py`。
4. 在 **Advanced settings** -> **Secrets** 中貼上您的 Gemini 金鑰：
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   ```
5. 點擊 **Deploy**，約 1~2 分鐘後即可取得公開網址，供全體同仁於手機與電腦隨時存取！

### 方法二：使用 Docker 容器化部署
建立 `Dockerfile`：
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
執行建置與啟動：
```bash
docker build -t civil-force-dashboard .
docker run -d -p 8501:8501 -e GEMINI_API_KEY="your_api_key" civil-force-dashboard
```

---

## 📊 資料庫結構 (Database Schema)

- **`documents` (重點公文)**：`id`, `doc_number`, `subject`, `deadline`, `assignee`, `status`, `priority`, `category`, `notes`
- **`calendar_events` (公務行事曆)**：`id`, `title`, `event_date`, `event_time`, `location`, `event_type`, `attendees`, `raw_image_path`, `notes`, `status`
- **`inspections` (督勤紀錄)**：`id`, `target_unit`, `inspect_date`, `inspector`, `focus_items`, `score`, `strengths`, `deficiencies`, `report_text`, `status`
- **`speech_templates` (稿件範本庫)**：`id`, `category`, `title`, `content_type`, `tone`, `template_structure`, `history_examples`
- **`fire_units` (單位主檔)**：`id`, `unit_name`, `unit_type`, `district`, `is_active`
- **`inspection_focus_items` (督勤項目庫)**：`id`, `category`, `item_name`, `description`, `is_active`
- **`users` (同仁帳號)**：`id`, `username`, `password_hash`, `display_name`, `role`, `email`, `is_active`
