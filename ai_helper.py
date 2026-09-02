"""
民力科業務執行與督勤彙整看板系統 - AI 智能模組 (Gemini Vision OCR & 文本生成)
具備高相容性手機影像壓縮、自動重試與 Google Gemini API (gemini-flash-lite / flash) 雙引擎
"""
import os
import json
import re
import base64
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from PIL import Image
import io

import streamlit as st
from config import BASE_DIR, DEFAULT_GEMINI_KEY

KEY_FILE_PATH = BASE_DIR / "gemini_key.txt"
ENV_FILE_PATH = BASE_DIR / ".env"

CANDIDATE_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

def save_gemini_api_key(api_key: str):
    """將 API Key 永久儲存至本機檔案與 Session State"""
    clean_key = api_key.strip()
    st.session_state["gemini_api_key"] = clean_key
    os.environ["GEMINI_API_KEY"] = clean_key
    try:
        with open(KEY_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(clean_key)
    except Exception:
        pass

def get_gemini_api_key() -> str:
    """取得 Gemini API Key (包含預設內建金鑰，確保雲端手機免設定直接可用)"""
    if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"]:
        return st.session_state["gemini_api_key"].strip()
    
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    
    if KEY_FILE_PATH.exists():
        try:
            with open(KEY_FILE_PATH, "r", encoding="utf-8") as f:
                k = f.read().strip()
                if k:
                    return k
        except Exception:
            pass

    if ENV_FILE_PATH.exists():
        try:
            with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        k = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if k:
                            return k
        except Exception:
            pass
    
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"].strip()
    except Exception:
        pass
    
    return DEFAULT_GEMINI_KEY


def optimize_image_for_ocr(image_input) -> Optional[bytes]:
    """
    將使用者上傳或拍照的圖片（支援 HEIC / PNG / JPEG / WEBP）進行智慧色彩轉換、等比例縮放與壓縮
    限制於 1280px 以內 (<250KB)，避免超出 Base64 API Payload 限制並大幅提升辨識速度
    """
    try:
        if isinstance(image_input, bytes):
            pil_img = Image.open(io.BytesIO(image_input))
        elif hasattr(image_input, "read"):
            if hasattr(image_input, "seek"):
                image_input.seek(0)
            img_bytes = image_input.read()
            if hasattr(image_input, "seek"):
                image_input.seek(0)
            pil_img = Image.open(io.BytesIO(img_bytes))
        elif isinstance(image_input, Image.Image):
            pil_img = image_input
        else:
            return None

        # 轉換色彩模式為 RGB (避免 PNG 透明度或 CMYK 報錯)
        if pil_img.mode in ("RGBA", "P", "LA", "CMYK"):
            pil_img = pil_img.convert("RGB")

        # 等比例縮放至長邊最大 1280px
        max_dim = 1280
        w, h = pil_img.size
        if max(w, h) > max_dim:
            if w > h:
                new_w = max_dim
                new_h = int(h * (max_dim / w))
            else:
                new_h = max_dim
                new_w = int(w * (max_dim / h))
            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=85, optimize=True)
        return buf.getvalue()
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return None


def call_gemini_rest(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/jpeg",
    api_key: Optional[str] = None
) -> Optional[str]:
    """
    使用 Google Gemini REST API 呼叫 (Header x-goog-api-key 驗證，超高相容性)
    """
    key = api_key or get_gemini_api_key()
    if not key:
        return None

    parts = [{"text": prompt}]
    if image_bytes:
        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": b64_data
            }
        })

    payload = {
        "contents": [
            {
                "parts": parts
            }
        ]
    }
    json_data = json.dumps(payload).encode("utf-8")

    # 依序嘗試呼叫 CANDIDATE_MODELS
    for model_name in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        try:
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": key.strip(),
                    "User-Agent": "CivilForceDashboard/2.2"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                candidates = resp_data.get("candidates", [])
                if candidates:
                    parts_resp = candidates[0].get("content", {}).get("parts", [])
                    if parts_resp and "text" in parts_resp[0]:
                        return parts_resp[0]["text"].strip()
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue

    return None


def test_gemini_connection(api_key: str) -> Tuple[bool, str]:
    """測試 Gemini API Key 連線狀態"""
    if not api_key:
        return False, "未提供 API Key"
    
    clean_key = api_key.strip()
    
    for model_name in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        payload = {"contents": [{"parts": [{"text": "Ping! 請回覆『連線正常』。"}]}]}
        json_data = json.dumps(payload).encode("utf-8")
        try:
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": clean_key,
                    "User-Agent": "CivilForceDashboard/2.2"
                }
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                candidates = resp_data.get("candidates", [])
                if candidates:
                    parts_resp = candidates[0].get("content", {}).get("parts", [])
                    txt = parts_resp[0]["text"].strip() if parts_resp else "連線正常"
                    return True, f"成功連線至 Google Gemini ({model_name})！回應：{txt}"
        except urllib.error.HTTPError as he:
            if he.code in [400, 401, 403]:
                continue
            continue
        except Exception:
            continue

    return False, "連線測試失敗：請確認網路連線或 API Key 是否正確複製。"


def extract_event_from_image(image_input, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    使用 Gemini Vision 解析會議通知單、邀請卡、訃聞之照片並提取結構化事件資訊
    """
    key = api_key or get_gemini_api_key()
    
    # 進行影像優化縮放
    img_bytes = optimize_image_for_ocr(image_input)
    if not img_bytes:
        st.error("❌ 圖片讀取失敗，請確認檔案格式是否正確。")
        return {}
        
    prompt = """
你是一位專業精準的消防局與民力科公務秘書。請仔細閱讀並分析所提供的開會通知單、公文、邀請卡或公祭訃聞圖片。
請務必精準辨識圖片中的真實文字內容，並以「純 JSON 格式」輸出，不要包含任何 markdown 標記以外的多餘文字。

【重要辨識與推算規則】：
1. 嚴格依據圖片中實際印刷文字辨識「開會事由 / 活動名稱」、「開會時間」、「地點」、「主持人/出席者」與「備註」。
2. 日期請將民國年精確換算為西元年（例如民國115年換算為 2026年，115年8月27日 -> 2026-08-27；民國113年 -> 2024年）。
3. 時間請轉為 24 小時制 HH:MM（例如「上午10時30分」轉換為「10:30」，「下午2時」轉換為「14:00」）。

請嚴格遵循以下 JSON 欄位結構輸出：
{
  "title": "事由或活動名稱（例如：召開臺東縣消防局115年度8月份第二次專案會議）",
  "event_date": "活動日期，格式必須為 YYYY-MM-DD（請精確換算民國年為西元年）",
  "event_time": "活動時間，格式為 HH:MM（24小時制，例如 10:30）",
  "location": "具體開會地點（例如：本局4樓災害應變中心）",
  "event_type": "分類（必須為以下其中一項：會議通知、公祭訃聞、邀請卡/典禮、局內公務活動、常訓/演練、其他）",
  "attendees": "指定出席長官、主持人或受邀人員（例如：盧東發局長、林副局長建誠、民力科長等）",
  "notes": "備註與重要聯絡資訊（包含視訊會議網址、聯絡人分機、服裝要求等）"
}
"""

    try:
        resp_text = call_gemini_rest(prompt=prompt, image_bytes=img_bytes, api_key=key)
        if resp_text:
            cleaned_text = resp_text.strip()
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()
            
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                if "title" in result and "event_date" in result:
                    return result
    except Exception as e:
        st.error(f"❌ Gemini Vision 辨識失敗 ({str(e)})")
        return {}

    st.error("❌ 無法完成圖片辨識，請確認網路連線與金鑰狀態。")
    return {}


def extract_event_from_text(text_input: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    使用 Gemini 解析貼上的文字通知 (如 LINE 群組訊息、Email 邀請、訃聞公祭說明等)，提取結構化行程資訊
    """
    key = api_key or get_gemini_api_key()
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    prompt = f"""
你是一位專業的消防局與民力科公務秘書。請仔細閱讀並分析以下使用者貼上的公務通知、會議訊息、邀請或公祭訃聞文字。
今日基準日期為：{today_str}（民國 {today.year - 1911} 年 {today.month} 月 {today.day} 日）。
請從文字中精準提取關鍵行程資訊，並以「純 JSON 格式」輸出，不要包含任何 markdown 標記以外的多餘文字。

請嚴格遵循以下 JSON 欄位結構輸出：
{{
  "title": "事由或活動名稱",
  "event_date": "活動日期，格式必須為 YYYY-MM-DD（若為民國年請精確轉換為西元年）",
  "event_time": "活動時間，格式為 HH:MM（24小時制）",
  "location": "具體地點",
  "event_type": "分類（必須為以下其中一項：會議通知、公祭訃聞、邀請卡/典禮、局內公務活動、常訓/演練、其他）",
  "attendees": "指定出席長官、受邀單位或承辦同仁",
  "notes": "備註事項（包含服裝規定、攜帶文件、聯絡窗口等重要提醒）"
}}

【通知文字內容】：
{text_input}
"""

    try:
        resp_text = call_gemini_rest(prompt=prompt, api_key=key)
        if resp_text:
            cleaned = resp_text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                res = json.loads(json_match.group(0))
                if "title" in res and "event_date" in res:
                    return res
    except Exception as e:
        st.error(f"❌ 文字解析失敗：{str(e)}")
        return {}

    return {}


def extract_doc_followup_from_text(doc_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    使用 Gemini 分析貼上的重要業務計畫、專案要點或公文全文 (主旨、說明、各段落)，智慧擷取續辦重點與應辦步驟
    """
    key = api_key or get_gemini_api_key()
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    prompt = f"""
你是一位資深的政府機關秘書與民力業務專案專家。請仔細閱讀並分析以下使用者貼上的「重要計畫內容 / 專案實施要點 / 公文簽呈 / 函文段落」。
這是同仁需要後續進行「業務續辦、推動列管或依限回覆」的重要案件。
請從文字中萃取出：項目類型、字號/計畫編號、案由/主旨、來文機關/主辦單位、精確推算執行時限與依據條款、急迫等級、業務類別、建議承辦人、目前辦理狀況，以及最重要的【具體續辦/實施步驟清單 (Action Checklist)】。

【基準日期】：今日日期為 {today_str}（民國 {today.year - 1911} 年 {today.month} 月 {today.day} 日）。
請根據計畫或公文內提及之時程條款（如「文到7日內」、「於115年9月5日前」等），自動換算推算出精確西元日期 (YYYY-MM-DD)。

請嚴格遵循以下純 JSON 格式輸出：
{{
  "item_type": "項目類型（必須為以下其中一項：重要業務計畫、公文續辦、專案列管計畫、演訓專案、採購專案）",
  "doc_number": "公文字號或計畫編號",
  "subject": "計畫名稱或公文主旨",
  "issuing_unit": "來文機關、指導單位或主辦科室",
  "deadline": "執行期限/預定完成日/回覆期限，格式為 YYYY-MM-DD",
  "deadline_desc": "時限條款依據或里程碑原文說明",
  "priority": "急迫等級（最速件 / 速件 / 普通件 / 專案列管）",
  "category": "業務類別（演訓與常年訓練 / 裝備器材採購 / 福利保險與慰問 / 義消組織與人事 / 救難團體輔導 / 綜合行政業務）",
  "assignee": "建議負責承辦人或負責股別",
  "current_progress": "【目前辦理狀況】",
  "followup_actions": "具體應續辦/實施事項清單（條列式 1. 2. 3.）",
  "key_summary": "1-2 句話說明本案的核心交辦重點與列管目的"
}}

【輸入文字內容】：
{doc_text}
"""

    try:
        resp_text = call_gemini_rest(prompt=prompt, api_key=key)
        if resp_text:
            cleaned = resp_text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                res = json.loads(json_match.group(0))
                if "subject" in res and "deadline" in res:
                    return res
    except Exception as e:
        st.error(f"❌ 解析失敗：{str(e)}")
        return {}

    return {}


def extract_doc_followup_from_image(image_input, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    使用 Gemini Vision 解析公文截圖或掃描檔
    """
    key = api_key or get_gemini_api_key()
    img_bytes = optimize_image_for_ocr(image_input)
    if not img_bytes:
        st.error("❌ 圖片讀取失敗，請確認檔案格式。")
        return {}

    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    prompt = f"""
你是一位資深的消防局與民力科公務秘書。請仔細閱讀並分析這張公文截圖或掃描檔。
今日基準日期為：{today_str}（民國 {today.year - 1911} 年 {today.month} 月 {today.day} 日）。
請從公文圖片中萃取出：項目類型、字號/計畫編號、主旨、發文機關、辦理期限、時限依據、急迫等級、業務類別、建議承辦人、目前辦理狀況，以及最重要的【具體續辦事項步驟清單 (Action Checklist)】。

請以純 JSON 格式輸出：
{{
  "item_type": "項目類型（重要業務計畫 / 公文續辦 / 專案列管計畫 / 演訓專案 / 採購專案）",
  "doc_number": "公文字號或計畫編號",
  "subject": "主旨或計畫摘要",
  "issuing_unit": "發文機關或主辦科室",
  "deadline": "辦理期限 (YYYY-MM-DD)",
  "deadline_desc": "時限條款原文",
  "priority": "急迫等級 (最速件 / 速件 / 普通件 / 專案列管)",
  "category": "業務類別 (演訓與常年訓練 / 裝備器材採購 / 福利保險與慰問 / 義消組織與人事 / 救難團體輔導 / 綜合行政業務)",
  "assignee": "建議承辦人",
  "current_progress": "目前辦理狀況",
  "followup_actions": "具體應續辦事項清單 (條列式 1. 2. 3.)",
  "key_summary": "核心重點說明"
}}
"""

    try:
        resp_text = call_gemini_rest(prompt=prompt, image_bytes=img_bytes, api_key=key)
        if resp_text:
            cleaned = resp_text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                res = json.loads(json_match.group(0))
                if "subject" in res and "deadline" in res:
                    return res
    except Exception as e:
        st.error(f"❌ 辨識失敗：{str(e)}")
        return {}

    return {}


def generate_speech_content(
    theme: str,
    speech_type: str,
    target_audience: str,
    key_points: str,
    tone: str,
    speaker: str = "局長",
    custom_instruction: str = "",
    api_key: Optional[str] = None
) -> str:
    """
    使用 Gemini 根據主題與長官風格生成公務致詞稿
    """
    key = api_key or get_gemini_api_key()

    prompt = f"""
你是一位專門為消防局局長、科長撰寫高規格公務致詞稿與新聞稿的資深新聞秘書。
請根據以下提供的活動資訊與要求，為講者【{speaker}】撰寫一篇結構完整、用詞典雅大器且振奮人心的【{speech_type}】。

【活動基本資訊】：
- 主題活動名稱：{theme}
- 稿件類型：{speech_type}
- 主要對象/受眾：{target_audience}
- 核心傳達重點與事蹟：{key_points}
- 語氣風格：{tone}
- 額外特定要求/長官口吻：{custom_instruction}

【致詞稿結構要求】：
1. **開場問候**：向在場貴賓（民意代表、友軍單位、義消總幹部等）致意，營造莊重且親切的氛圍。
2. **肯定與感謝**：肯定全體義消、協勤志工與警消同仁無私奉獻與英勇付出，並點出具體事蹟。
3. **政策方針與展望**：結合消防局最新民力政策重點、裝備提升或訓練革新，展現長官格局與對未來的期許。
4. **結尾祝福**：祝賀活動圓滿成功，祝福全體同仁、貴賓身體健康、闔家平安、出勤救災一切平安順遂。

請直接輸出格式優美的高品質 Markdown 格式稿件，包含段落標題、長官講話停頓點提示（如 [微笑致意]、[堅定語氣] 等小標籤）。
"""

    if key:
        try:
            resp_text = call_gemini_rest(prompt=prompt, api_key=key)
            if resp_text and len(resp_text) > 50:
                return resp_text.strip()
        except Exception:
            pass

    return f"""# 🚒 【{theme}】{speaker}致詞稿\n\n**發布日期**：{datetime.now().strftime('%Y年%m月%d日')} ｜ **講者**：{speaker} ｜ **語氣風格**：{tone}\n\n---\n\n各位長官、在座熱心奉獻的義消弟兄姊妹、各位媒體女士先生、警消同仁，大家早安、大家好！[微笑致意]\n\n今天非常高興，能夠代表消防局全體同仁，在【{theme}】這個深具意義的日子裡，與大家齊聚一堂。\n\n### 一、 肯定辛勞與無私奉獻\n各位義消夥伴與協勤民力，一直以來都是我們消防局最堅實的後盾。無論是深夜的火警搶救、颱風豪雨的防汛搜救，抑或是平時的防火防災宣導，大家總是拋下身邊的工作與家庭，第一時間趕赴現場，為守護鄉親的身家財產安全全力以赴！[眼神堅定，致上最高敬意]\n\n### 二、 核心施政與裝備精進\n誠如大家所見，{key_points}。局裡未來將持續爭取更充實的預算，為大家升級更安全的個人防護裝備、強化專業科技訓練，並落實各項福利保障，讓每位走在救災前線的民力英雄，都能在最安全的環境下出勤、平安歸來！\n\n### 三、 祝賀與結語\n最後，再次感謝全體義消夥伴與各界長官的大力支持。祝福今天的活動圓滿成功，也祝福在場所有的長官、貴賓與同仁，身體健康、家庭美滿、工作順利、每次出勤救災都平安圓滿！\n\n謝謝大家！[全場鞠躬致謝]"""


def generate_press_content(
    headline: str,
    event_summary: str,
    key_quotes: str,
    hero_story: str,
    speaker: str = "局長",
    api_key: Optional[str] = None
) -> str:
    """
    使用 Gemini 生成標準公務新聞稿
    """
    key = api_key or get_gemini_api_key()

    prompt = f"""
你是一位資深的政府機關新聞聯絡人。請根據以下活動素材，撰寫一篇符合公務發布規範、具備高吸睛度與正面形象的【新聞發布稿】。

【新聞素材】：
- 新聞主標題/主題：{headline}
- 事件背景與活動摘要：{event_summary}
- 長官談話重點（引述{speaker}發言）：{key_quotes}
- 感人事蹟/亮點故事：{hero_story}

【新聞稿格式要求】：
1. **新聞主標題與副標題**（簡潔有力、亮眼大器）
2. **導言（第一段）**：包含人、事、時、地、物等 5W1H 核心要素
3. **主體內容（第二至三段）**：詳述活動亮點、具體成效及長官引言
4. **感人或具體事蹟亮點（第四段）**：強化民力熱心奉獻之形象
5. **新聞聯絡人資訊欄**：單位、發稿日期、聯絡人與公務電話

請直接輸出符合公務發稿標準的 Markdown 文本。
"""

    if key:
        try:
            resp_text = call_gemini_rest(prompt=prompt, api_key=key)
            if resp_text and len(resp_text) > 50:
                return resp_text.strip()
        except Exception:
            pass

    return f"""# 📰 【新聞發布】{headline}\n\n**發稿單位**：消防局民力科 ｜ **發稿日期**：{datetime.now().strftime('%Y年%m月%d日')} ｜ **聯絡人**：民力科新聞聯絡窗口\n\n---\n\n### 【主旨導言】\n為強化全縣防救災能量、凝聚民力向心力，消防局於今日隆重舉行「{headline}」。活動現場冠蓋雲集，充分展現義消民力與警消攜手守護鄉親安全的堅定決心。\n\n### 【長官期許與施政亮點】\n{speaker}於會中特別指出：「{key_quotes if key_quotes else '民力是消防最堅強的後盾，感謝全體義消夥伴長年無私奉獻。'}」消防局近年來積極爭取中央與地方資源，全面汰換升級防護裝備，並結合智慧科技與社區韌性推動，打造更完善的救災防護網。\n\n### 【現場感人事蹟與具體成效】\n{hero_story if hero_story else '活動中特別表揚多位長年協勤之資深義消幹部，其熱心公益、捨己為人的精神，深獲地方鄉親高度肯定與讚揚。'}"""

# 函式名稱相容別名
generate_speech = generate_speech_content
generate_press_release = generate_press_content
