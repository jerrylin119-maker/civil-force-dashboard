"""
民力科業務執行與督勤彙整看板系統 - 全域設定檔
"""
import os
from pathlib import Path

# 基本路徑設定
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "civil_force.db"
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
REPORTS_DIR = BASE_DIR / "reports" / "inspections"

# 確保必要目錄存在
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 系統基本資訊
APP_TITLE = "民力科重要計畫及公文續辦管理看板系統"
APP_SUBTITLE = "Civil Force Projects, Operations & Inspection Dashboard"
APP_ICON = "🚒"
APP_VERSION = "v2.2.0"
DEFAULT_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

# 使用者身分角色
USER_ROLES = ["科長 / 決策主管", "督勤同仁 / 查核幹部", "業務承辦人 / 科員", "系統管理員"]

# 項目類型 (計畫 vs 公文)
PLAN_DOC_TYPE_OPTIONS = ["全部類型", "重要業務計畫", "公文續辦", "專案列管計畫", "演訓專案", "採購專案"]

# 處理狀態與類別
DOC_STATUS_OPTIONS = ["待續辦 / 規劃中", "辦理中 / 執行中", "已辦結 / 已完成"]
DOC_PRIORITY_OPTIONS = ["普通件", "速件", "最速件", "專案列管"]
DOC_CATEGORY_OPTIONS = ["義消組織與人事", "救難團體輔導", "裝備器材採購", "演訓與常年訓練", "福利保險與慰問", "綜合行政業務"]

# 目前辦理狀況常用快捷標籤
QUICK_PROGRESS_PRESETS = [
    "簽呈陳核中",
    "各單位名冊/資料彙整中",
    "已發文通知各分隊/大隊配合",
    "規格需求書研擬中",
    "主計/政風會辦中",
    "現場演練籌備中",
    "第1階段驗收完成",
    "辦理完成，簽陳歸檔"
]

# 行事曆事件類別
EVENT_TYPE_OPTIONS = ["會議通知", "公祭訃聞", "邀請卡/典禮", "局內公務活動", "常訓/演練", "其他"]

# 預設轄內單位主檔 (依據「臺東縣消防局組織架構」完整建置四大隊、所屬各分隊、外島與專屬任務隊，共33個受督單位)
DEFAULT_FIRE_UNITS = [
    # ── 臺東大隊轄區 (市區與離島) ──
    {"unit_name": "臺東大隊部", "unit_type": "消防大隊", "district": "臺東大隊轄區"},
    {"unit_name": "臺東分隊", "unit_type": "消防分隊", "district": "臺東大隊轄區"},
    {"unit_name": "臺東救護分隊", "unit_type": "消防分隊", "district": "臺東大隊轄區"},
    {"unit_name": "豐田分隊", "unit_type": "消防分隊", "district": "臺東大隊轄區"},
    {"unit_name": "大豐分隊", "unit_type": "消防分隊", "district": "臺東大隊轄區"},
    {"unit_name": "南王分隊", "unit_type": "消防分隊", "district": "臺東大隊轄區"},
    {"unit_name": "卑南分隊", "unit_type": "消防分隊", "district": "臺東大隊轄區"},
    {"unit_name": "知本分隊", "unit_type": "消防分隊", "district": "臺東大隊轄區"},
    {"unit_name": "特種搜救分隊", "unit_type": "消防分隊", "district": "臺東大隊轄區"},
    {"unit_name": "搜救犬分隊", "unit_type": "消防分隊", "district": "臺東大隊轄區"},
    {"unit_name": "綠島分隊", "unit_type": "消防分隊", "district": "臺東大隊(離島)"},
    {"unit_name": "蘭嶼分隊", "unit_type": "消防分隊", "district": "臺東大隊(離島)"},

    # ── 關山大隊轄區 (縱谷線) ──
    {"unit_name": "關山大隊部", "unit_type": "消防大隊", "district": "關山大隊轄區"},
    {"unit_name": "關山分隊", "unit_type": "消防分隊", "district": "關山大隊轄區"},
    {"unit_name": "池上分隊", "unit_type": "消防分隊", "district": "關山大隊轄區"},
    {"unit_name": "海端分隊", "unit_type": "消防分隊", "district": "關山大隊轄區"},
    {"unit_name": "鹿野分隊", "unit_type": "消防分隊", "district": "關山大隊轄區"},
    {"unit_name": "延平分隊", "unit_type": "消防分隊", "district": "關山大隊轄區"},
    {"unit_name": "利稻分隊", "unit_type": "消防分隊", "district": "關山大隊轄區"},

    # ── 成功大隊轄區 (東海岸線) ──
    {"unit_name": "成功大隊部", "unit_type": "消防大隊", "district": "成功大隊轄區"},
    {"unit_name": "成功分隊", "unit_type": "消防分隊", "district": "成功大隊轄區"},
    {"unit_name": "長濱分隊", "unit_type": "消防分隊", "district": "成功大隊轄區"},
    {"unit_name": "都蘭分隊", "unit_type": "消防分隊", "district": "成功大隊轄區"},
    {"unit_name": "泰源分隊", "unit_type": "消防分隊", "district": "成功大隊轄區"},
    {"unit_name": "東河分隊", "unit_type": "消防分隊", "district": "成功大隊轄區"},

    # ── 大武大隊轄區 (南迴線) ──
    {"unit_name": "大武大隊部", "unit_type": "消防大隊", "district": "大武大隊轄區"},
    {"unit_name": "大武分隊", "unit_type": "消防分隊", "district": "大武大隊轄區"},
    {"unit_name": "太麻里分隊", "unit_type": "消防分隊", "district": "大武大隊轄區"},
    {"unit_name": "金峰分隊", "unit_type": "消防分隊", "district": "大武大隊轄區"},
    {"unit_name": "大溪分隊", "unit_type": "消防分隊", "district": "大武大隊轄區"},
    {"unit_name": "達仁分隊", "unit_type": "消防分隊", "district": "大武大隊轄區"},

    # ── 局本部專屬任務隊 ──
    {"unit_name": "科技救災分隊", "unit_type": "專屬分隊", "district": "局本部專屬任務隊"},
    {"unit_name": "安檢隊", "unit_type": "專屬分隊", "district": "局本部專屬任務隊"},
]

# 預設督勤重點項目庫 (依據民力科最新實務督勤要點精確建置 5 大督勤查核重點)
DEFAULT_INSPECTION_ITEMS = [
    {
        "category": "義消專長資料庫",
        "item_name": "本科建置義消專長資料庫是否有定期更新及設定專用網址為書籤",
        "description": "查核分隊是否有定期登錄更新義消人員專長資料庫，並將專用網址加入瀏覽器書籤以利快速查詢運用。"
    },
    {
        "category": "訓練與出勤紀錄",
        "item_name": "抽查本月義消定期訓練及出勤紀錄是否核實",
        "description": "抽查本月義消常年/定期訓練簽到退簿、APP 出勤時數登錄與實際協勤紀錄是否核實無誤。"
    },
    {
        "category": "補助款規定熟悉度",
        "item_name": "抽查分隊辦理義消申請議員建議補助款是否熟悉相關規定事項",
        "description": "抽查分隊承辦同仁辦理義消申請議員建議補助款之流程、核銷單據及相關法令規範是否熟悉落實。"
    },
    {
        "category": "訓練安全管理",
        "item_name": "抽查大隊或分隊辦理訓練是否依訓練安全管理程序書執行",
        "description": "查核大隊或分隊辦理各項常年/專業訓練時，是否嚴格遵循訓練安全管理程序書落實防護與教官助教配置。"
    },
    {
        "category": "義消推動制度了解",
        "item_name": "詢問對於今年本局推動的義消制度是否了解",
        "description": "現場訪詢分隊幹部與同仁，對於今年度本局推動之各項義消新制度、福利措施與組織調整是否充分了解。"
    }
]

# 預設公務稿件分類與範本
DEFAULT_SPEECH_TEMPLATES = [
    {
        "category": "裝備車輛捐贈",
        "title": "善心企業/團體捐贈消防警備車暨救災器材儀式長官致詞",
        "content_type": "致詞稿",
        "tone": "溫馨感人",
        "template_structure": "感謝開場 -> 表揚善舉與企業責任 -> 說明裝備效益 -> 勉勵同仁守護市民 -> 祝賀結語",
        "history_examples": "各位貴賓、捐贈單位代表、各位打火弟兄姊妹大家早安！首先代表全體市民及消防局，向今日慷慨解囊的善心單位致上由衷的謝意..."
    },
    {
        "category": "常年訓練",
        "title": "年度義勇消防人員常年訓練開訓精神講話",
        "content_type": "致詞稿",
        "tone": "激勵振奮",
        "template_structure": "問候與肯定 -> 強調救災技能與安全 -> 凝聚團隊向心力 -> 預祝訓練圓滿",
        "history_examples": "各位義消幹部、各位熱血奉獻的打火兄弟姊妹大家精神好！今天看到大家精神抖擻齊聚一堂，展現無比的專業與熱忱..."
    },
    {
        "category": "表揚餐會",
        "title": "績優義消表揚大會暨顧問團聯誼餐會長官致詞",
        "content_type": "致詞稿",
        "tone": "激勵振奮",
        "template_structure": "熱情問候 -> 讚許年度卓越事蹟 -> 感激顧問團後盾 -> 展望未來願景",
        "history_examples": "感謝各位義消同仁無私奉獻，您們是城市最溫暖的守護神..."
    },
    {
        "category": "裝備車輛捐贈",
        "title": "民間愛心捐贈救災器材暨救護裝備新聞稿",
        "content_type": "新聞稿",
        "tone": "莊重正式",
        "template_structure": "吸睛主標 -> 新聞導言(人事時地物) -> 捐贈背景與善舉細節 -> 局長/長官感謝發言 -> 裝備部署效益",
        "history_examples": "【提升救災量能！民間企業熱心捐贈百萬救災裝備 守護市民安全】本局於今日舉行捐贈典禮..."
    }
]

# 督導各重點項目之「現場狀況說明快捷選單」預設常用詞庫
PRESET_NOTES_FILE = BASE_DIR / "inspection_preset_notes.json"

DEFAULT_ITEM_PRESET_NOTES = {
    "義消專長資料庫": [
        "分隊已將專長資料庫網址設為瀏覽器書籤，落實定期更新。",
        "承辦人已設定專用書籤，本月已完成新增2名具救護專長義消基本資料。",
        "已設定專用書籤，資料庫定期維護維護良好。",
        "分隊電腦尚未設定書籤，且未即時更新新進義消專長資料，已現場協助設定並請於3日內補正。",
        "查核良好，運作正常。"
    ],
    "定期訓練及出勤紀錄": [
        "抽查8月份常訓簽到名冊25名全員核實簽到，APP出勤時數與協勤紀錄相符。",
        "常年訓練名冊簽核確實，出勤時數登錄無誤。",
        "本月定期訓練出席率達95%，簽到退紀錄完整核實。",
        "部分同仁APP出勤時數未即時登錄，已現場督導承辦人提醒補登。",
        "查核良好，運作正常。"
    ],
    "議員建議補助款": [
        "承辦同仁熟悉議員補助款請領程序、核銷單據黏貼與器材保管標籤規範。",
        "補助款請領單據核銷完備，器材保管標籤齊全，查核良好。",
        "分隊承辦人員熟悉相關作業規定，依期程辦理核銷申報。",
        "單據黏貼與器材標籤未齊全，已現場輔導補正。",
        "查核良好，運作正常。"
    ],
    "訓練安全管理程序書": [
        "訓練安全檢核表落實填報，教官助教比符合規範，現場設有專責安全官管制。",
        "辦理常訓及演練落實訓練安全管理程序書，裝備檢測良好無缺失。",
        "依程序書落實各項安全檢核，安全官全程在場管制督導。",
        "現場安全官未確實佩掛識別標示，已現場提醒改善。",
        "查核良好，運作正常。"
    ],
    "義消制度": [
        "幹部與同仁均清楚了解今年度義消福利保險升級、出勤津貼核發與新式考核制度。",
        "現場向分隊同仁宣導本年度義消新制度，現場同仁均充分理解並落實推動。",
        "同仁均了解本局推動之各項義消新制與津貼福利政策。",
        "同仁對新式考核制度尚有疑義，已現場詳細說明釋疑。",
        "查核良好，運作正常。"
    ]
}

import json

def load_preset_notes() -> dict:
    """讀取各督導項目之狀況說明常用詞庫 (優先從本地 JSON，若無則載入預設)"""
    if PRESET_NOTES_FILE.exists():
        try:
            with open(PRESET_NOTES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # 確保預設 5 項鍵都存在
                    for k, v in DEFAULT_ITEM_PRESET_NOTES.items():
                        if k not in data or not data[k]:
                            data[k] = v
                    return data
        except Exception:
            pass
    return {k: list(v) for k, v in DEFAULT_ITEM_PRESET_NOTES.items()}

def save_preset_notes(notes_dict: dict) -> bool:
    """儲存使用者自訂之狀況說明詞庫至本地 JSON 檔案"""
    try:
        with open(PRESET_NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving preset notes: {e}")
        return False
