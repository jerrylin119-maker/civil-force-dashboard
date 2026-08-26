"""
民力科業務執行與督勤彙整看板系統 - 資料庫層 (SQLAlchemy + SQLite)
"""
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Date, DateTime, Boolean, Float
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

from config import (
    DB_PATH, DEFAULT_FIRE_UNITS, DEFAULT_INSPECTION_ITEMS, DEFAULT_SPEECH_TEMPLATES
)

Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)


class User(Base):
    """同仁與主管帳號模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    display_name = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)  # 科長 / 督勤同仁 / 業務承辦人 / 系統管理員
    email = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class Document(Base):
    """重要計畫及公文續辦管理模型 (支援重要業務計畫、專案列管與公文續辦)"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(String(50), default="公文續辦")  # 重要業務計畫 / 公文續辦 / 專案列管計畫 / 演訓專案 / 採購專案
    doc_number = Column(String(100), nullable=False)  # 發文字號 / 計畫編號 (如：消署民字第113008899號、113民力常訓計畫-01)
    subject = Column(Text, nullable=False)           # 計畫名稱 / 公文主旨
    deadline = Column(Date, nullable=False)           # 執行期限 / 預定完成日 / 回覆期限
    deadline_desc = Column(String(200), nullable=True) # 時限條款依據 / 里程碑說明 (如：文到7日內報署、預計9月15日前開訓)
    issuing_unit = Column(String(100), nullable=True)  # 來文機關 / 主辦或指導單位 (如：內政部消防署、市府研考會)
    assignee = Column(String(50), nullable=False)     # 負責同仁 / 承辦人
    status = Column(String(20), default="辦理中")      # 待續辦 / 辦理中 / 已辦結
    priority = Column(String(20), default="普通件")    # 普通件 / 速件 / 最速件 / 專案列管
    category = Column(String(50), default="綜合行政業務") # 業務類別
    current_progress = Column(String(200), default="刻正辦理中") # 【目前辦理狀況】(如：簽呈陳核中、名冊彙整中、規格審查中)
    followup_actions = Column(Text, nullable=True)     # AI 智慧擷取之「續辦/實施重點與待辦清單 (條列/JSON)」
    notes = Column(Text, nullable=True)               # 詳細進度摘要或同仁備註
    raw_content = Column(Text, nullable=True)         # 原始貼上之計畫/公文全文或截圖 OCR 文字
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CalendarEvent(Base):
    """科內公務行事曆與圖文辨識事件模型"""
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)       # 事由/活動名稱
    event_date = Column(Date, nullable=False)         # 活動日期
    event_time = Column(String(50), default="09:00")  # 活動時間
    location = Column(String(200), nullable=True)     # 地點
    event_type = Column(String(50), default="會議通知") # 會議通知 / 公祭訃聞 / 邀請卡/典禮 / 局內公務活動 / 其他
    attendees = Column(String(200), nullable=True)    # 指定出席/承辦同仁
    raw_image_path = Column(String(300), nullable=True)# 原始圖文辨識照片路徑
    notes = Column(Text, nullable=True)               # 備註、服裝規定、公奠注意事項
    status = Column(String(20), default="預定")        # 預定 / 已參加 / 另派代 / 取消
    created_at = Column(DateTime, default=datetime.now)


class Inspection(Base):
    """督勤紀錄模型"""
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_unit = Column(String(100), nullable=False) # 督導對象 (單位名稱)
    inspect_date = Column(Date, nullable=False)       # 督勤日期
    inspector = Column(String(50), nullable=False)    # 督勤人員
    focus_items = Column(Text, nullable=True)         # JSON 字串：查核項目與結果清單
    score = Column(Integer, default=0)                # (保留欄位，不再進行分數評比)
    merit_status = Column(String(50), default="口頭嘉勉")    # 優良處置：優績 / 口頭嘉勉 / 符合良好
    demerit_status = Column(String(50), default="無重大缺失") # 缺失處置：劣蹟註記 / 請主管立即改善 / 無重大缺失
    strengths = Column(Text, nullable=True)           # 優點及具體事蹟 (優績/口頭嘉勉說明)
    deficiencies = Column(Text, nullable=True)        # 缺失與建議改善事項 (劣蹟/立即改善要求)
    report_text = Column(Text, nullable=True)         # 格式化完整督勤報告
    status = Column(String(20), default="已存檔")      # 已存檔 / 追蹤改善中 / 結案
    created_at = Column(DateTime, default=datetime.now)


class SpeechTemplate(Base):
    """致詞稿與新聞稿範本庫模型"""
    __tablename__ = "speech_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)     # 常年訓練 / 裝備車輛捐贈 / 防救災演練 / 表揚餐會 / 其他
    title = Column(String(200), nullable=False)       # 標題
    content_type = Column(String(20), default="致詞稿") # 致詞稿 / 新聞稿
    tone = Column(String(20), default="莊重正式")      # 溫馨感人 / 激勵振奮 / 莊重正式
    template_structure = Column(Text, nullable=True)  # 提示結構架構
    history_examples = Column(Text, nullable=True)    # 範本文本
    created_at = Column(DateTime, default=datetime.now)


class FireUnit(Base):
    """轄內分隊與義消單位主檔"""
    __tablename__ = "fire_units"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_name = Column(String(100), unique=True, nullable=False)
    unit_type = Column(String(50), nullable=False)
    district = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)


class InspectionFocusItem(Base):
    """督勤重點項目定義庫"""
    __tablename__ = "inspection_focus_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    item_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


def init_db():
    """初始化資料庫並載入預設種子資料"""
    Base.metadata.create_all(engine)

    # 自動檢查並遷移新增的欄位 (以防既有 SQLite 資料庫缺少欄位)
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 遷移 documents
        cursor.execute("PRAGMA table_info(documents)")
        cols_doc = [row[1] for row in cursor.fetchall()]
        if "item_type" not in cols_doc:
            cursor.execute("ALTER TABLE documents ADD COLUMN item_type VARCHAR(50) DEFAULT '公文續辦'")
        if "current_progress" not in cols_doc:
            cursor.execute("ALTER TABLE documents ADD COLUMN current_progress VARCHAR(200) DEFAULT '刻正辦理中'")
        if "issuing_unit" not in cols_doc:
            cursor.execute("ALTER TABLE documents ADD COLUMN issuing_unit VARCHAR(100)")
        if "deadline_desc" not in cols_doc:
            cursor.execute("ALTER TABLE documents ADD COLUMN deadline_desc VARCHAR(200)")
        if "followup_actions" not in cols_doc:
            cursor.execute("ALTER TABLE documents ADD COLUMN followup_actions TEXT")
        if "raw_content" not in cols_doc:
            cursor.execute("ALTER TABLE documents ADD COLUMN raw_content TEXT")
        
        # 遷移 inspections
        cursor.execute("PRAGMA table_info(inspections)")
        cols_insp = [row[1] for row in cursor.fetchall()]
        if "merit_status" not in cols_insp:
            cursor.execute("ALTER TABLE inspections ADD COLUMN merit_status VARCHAR(50) DEFAULT '口頭嘉勉'")
        if "demerit_status" not in cols_insp:
            cursor.execute("ALTER TABLE inspections ADD COLUMN demerit_status VARCHAR(50) DEFAULT '無重大缺失'")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Table migration notice: {e}")

    session = SessionLocal()

    try:
        # 1. 檢查並初始化使用者 (密碼採用 SHA256 雜湊，預設皆為 123456)
        import hashlib
        default_pwd_hash = hashlib.sha256("123456".encode("utf-8")).hexdigest()

        if session.query(User).count() == 0:
            users = [
                User(username="admin", password_hash=default_pwd_hash, display_name="系統管理員", role="系統管理員", email="admin@civilforce.gov.tw"),
                User(username="leader", password_hash=default_pwd_hash, display_name="王科長", role="科長 / 決策主管", email="chief@civilforce.gov.tw"),
                User(username="inspector1", password_hash=default_pwd_hash, display_name="張股長", role="督勤同仁 / 查核幹部", email="officer1@civilforce.gov.tw"),
                User(username="clerk1", password_hash=default_pwd_hash, display_name="陳科員", role="業務承辦人 / 科員", email="clerk1@civilforce.gov.tw"),
                User(username="clerk2", password_hash=default_pwd_hash, display_name="林科員", role="業務承辦人 / 科員", email="clerk2@civilforce.gov.tw"),
            ]
            session.add_all(users)

        # 2. 檢查並初始化單位主檔
        if session.query(FireUnit).count() == 0:
            units = [FireUnit(**u) for u in DEFAULT_FIRE_UNITS]
            session.add_all(units)

        # 3. 檢查並初始化督勤重點項目
        if session.query(InspectionFocusItem).count() == 0:
            items = [InspectionFocusItem(**it) for it in DEFAULT_INSPECTION_ITEMS]
            session.add_all(items)

        # 4. 檢查並初始化致詞/新聞稿範本
        if session.query(SpeechTemplate).count() == 0:
            stmps = [SpeechTemplate(**st) for st in DEFAULT_SPEECH_TEMPLATES]
            session.add_all(stmps)

        # 5. 檢查並初始化重要計畫及公文續辦示範資料
        if session.query(Document).count() == 0:
            today = date.today()
            sample_docs = [
                Document(
                    item_type="重要業務計畫",
                    doc_number="113民力常訓專案-01",
                    subject="113年度下半年義勇消防人員常年訓練與救災安全考核實施計畫",
                    deadline=today + timedelta(days=2),  # < 3 天 (紅色警示)
                    deadline_desc="預定9月1日前完成全區開訓簽核，並於文到10日內函報消防署",
                    issuing_unit="內政部消防署 / 本局民力科",
                    assignee="陳科員",
                    status="辦理中",
                    priority="最速件",
                    category="演訓與常年訓練",
                    current_progress="簽呈陳核至副局長室，名冊初審完竣",
                    followup_actions="1. 彙整各義消大隊受訓名冊與訓練時數表。\n2. 擬訂常訓安全考核課程表陳核長官。\n3. 函復消防署備查並發文通知各大隊配合辦理。",
                    notes="簽呈已陳核至局長室，待長官核示後發文各義消大隊配合辦理。"
                ),
                Document(
                    item_type="公文續辦",
                    doc_number="北府消民字第11300902號",
                    subject="善心企業捐贈熱顯像儀與破壞器材典禮規劃、長官講稿及新聞發布續辦案",
                    deadline=today + timedelta(days=5),  # < 7 天 (黃色提醒)
                    deadline_desc="典禮訂於下週三舉行，需於本週五前完成講稿核定與新聞稿擬定",
                    issuing_unit="消防局秘書室 / 宏達科技",
                    assignee="林科員",
                    status="辦理中",
                    priority="速件",
                    category="裝備器材採購",
                    current_progress="講稿AI初稿擬定中，已與捐贈方完成流程確認",
                    followup_actions="1. 與捐贈單位窗口確認流程與貴賓出席名單。\n2. 擬定長官致詞講稿（溫馨感人風格）。\n3. 撰寫發布新聞稿並協調公關科聯絡媒體。",
                    notes="已與捐贈方秘書完成流程確認，講稿已使用 AI 生成初稿微調中。"
                ),
                Document(
                    item_type="專案列管計畫",
                    doc_number="113特搜裝備採購-03",
                    subject="113年度義消特種搜救分隊高空繩索與破壞防護器材規格審查暨招標採購專案",
                    deadline=today + timedelta(days=1),  # < 3 天 (紅色警示)
                    deadline_desc="本季採購預算執行列管，需於明日下班前完成規格書簽陳",
                    issuing_unit="消防局採購科 / 民力科",
                    assignee="林科員",
                    status="待續辦",
                    priority="最速件",
                    category="裝備器材採購",
                    current_progress="規格需求書已草擬，待會辦政風及主計室",
                    followup_actions="1. 檢視特搜分隊提報之器材規格。\n2. 會辦主計與政風單位審查。\n3. 送交採購科辦理公開招標公告。",
                    notes="規格書初稿已擬定，預計今日召開科內審查。"
                ),
                Document(
                    item_type="公文續辦",
                    doc_number="消署民字第113007620號",
                    subject="查核第三季各分隊義消協勤出勤時數登錄、保險及各項津貼結算造冊案",
                    deadline=today + timedelta(days=1),  # < 3 天 (紅色警示)
                    deadline_desc="本季津貼撥款期限在即，請於明天中午前完成全區清冊彙整",
                    issuing_unit="消防局主計室",
                    assignee="張股長",
                    status="辦理中",
                    priority="最速件",
                    category="福利保險與慰問",
                    current_progress="尚有第二大隊2個分隊未回傳名冊，正電話催收中",
                    followup_actions="1. 電話催收第二大隊所屬分隊之紙本簽退名冊。\n2. 於系統端比對 APP 出勤打卡時數與核銷金額。\n3. 會辦主計室並簽請局長核發津貼。",
                    notes="尚有第二大隊部分分隊未回傳出勤簽核清冊，需今日電話催收。"
                ),
                Document(
                    item_type="重要業務計畫",
                    doc_number="114救難團體輔導-01",
                    subject="114年度民間防救災志願組織輔導考核與補助經費分配專案計畫",
                    deadline=today + timedelta(days=18), # 充裕
                    deadline_desc="預計下月中旬前召開跨機關審查會議並核定補助額度",
                    issuing_unit="市政府秘書處 / 民力科",
                    assignee="陳科員",
                    status="辦理中",
                    priority="普通件",
                    category="救難團體輔導",
                    current_progress="已函發各民間救難團體提報114年度補助計畫書",
                    followup_actions="1. 彙整各救難協會提報之訓練與器材補助申請表。\n2. 辦理初審並排定實地督導訪查時程。\n3. 召開審查委員會核定各隊補助金額。",
                    notes="目前已有5個民間團體送件，預計下週辦理初審。"
                ),
                Document(
                    item_type="公文續辦",
                    doc_number="民力福字第11300877號",
                    subject="受傷義消同仁急難慰問金及團體保險給付理賠申報續辦審查",
                    deadline=today + timedelta(days=14), # 充裕
                    deadline_desc="保險公司請本局於兩週內補齊診斷證明書與出勤紀錄表",
                    issuing_unit="國泰世紀產物保險公司",
                    assignee="陳科員",
                    status="辦理中",
                    priority="普通件",
                    category="福利保險與慰問",
                    current_progress="已取得醫院診斷書，正會辦救災派遣單核章",
                    followup_actions="1. 向所屬分隊調閱當日火警出勤派遣紀錄單。\n2. 協助受傷同仁家屬填寫理賠申請書並核蓋公章。\n3. 送件保險公司辦理撥款。",
                    notes="保險公司已收件審查，刻正彙整醫療單據陳核撥款。"
                ),
            ]
            session.add_all(sample_docs)

        # 6. 檢查並初始化公務行事曆示範資料
        if session.query(CalendarEvent).count() == 0:
            today = date.today()
            sample_events = [
                CalendarEvent(
                    title="113年第三季消防局局務主管暨民力業務研討會報",
                    event_date=today + timedelta(days=2),
                    event_time="09:30",
                    location="消防局本部6樓簡報室",
                    event_type="會議通知",
                    attendees="王科長、張股長、業務承辦同仁",
                    notes="請攜帶民力督勤覆蓋率報表與常訓籌備進度簡報，著常服出席。"
                ),
                CalendarEvent(
                    title="義消第一大隊前副總隊長告別奠禮 (公奠儀式)",
                    event_date=today + timedelta(days=4),
                    event_time="08:30",
                    location="市立第一殯儀館 景行廳",
                    event_type="公祭訃聞",
                    attendees="局長、主任秘書、王科長、義消各大隊長",
                    notes="08:00 前於現場集合點名整隊，著公務深色服裝或義消正服。"
                ),
                CalendarEvent(
                    title="宏達科技集團捐贈消防特搜救災警備車暨器材典禮",
                    event_date=today + timedelta(days=6),
                    event_time="10:00",
                    location="信義分隊前大廣場",
                    event_type="邀請卡/典禮",
                    attendees="局長、王科長、林科員",
                    notes="儀式預計1小時，含致詞、頒發感謝狀與車輛裝備展示拍聯訪。"
                ),
                CalendarEvent(
                    title="113年度義勇消防人員常年訓練開訓精神動員",
                    event_date=today + timedelta(days=10),
                    event_time="14:00",
                    location="消防訓練中心 綜合演練場",
                    event_type="常訓/演練",
                    attendees="王科長、張股長、陳科員",
                    notes="開訓致詞與第一梯次防護裝備實操督勤。"
                )
            ]
            session.add_all(sample_events)

        # 7. 檢查並初始化歷史督勤示範紀錄 (以 5 大最新重點項目為範例)
        if session.query(Inspection).count() == 0:
            today = date.today()
            sample_inspections = [
                Inspection(
                    target_unit="臺東分隊",
                    inspect_date=today - timedelta(days=12),
                    inspector="張股長",
                    score=0,
                    merit_status="優績",
                    demerit_status="無重大缺失",
                    focus_items=json.dumps([
                        {"category": "義消專長資料庫", "name": "本科建置義消專長資料庫是否有定期更新及設定專用網址為書籤。", "result": "☑ 符合規範", "note": "分隊已將專長資料庫網址設為書籤，本月已完成新增2名具救護專長義消基本資料。"},
                        {"category": "訓練與出勤紀錄", "name": "抽查本月義消定期訓練及出勤紀錄是否核實", "result": "☑ 符合規範", "note": "抽查8月份常訓簽到名冊25名全員核實簽到，APP出勤時數與協勤紀錄相符。"},
                        {"category": "補助款規定熟悉度", "name": "抽查分隊辦理義消申請議員建議補助款是否熟悉相關規定事項", "result": "☑ 符合規範", "note": "承辦同仁熟悉議員補助款請領程序、核銷單據黏貼與器材保管標籤規範。"},
                        {"category": "訓練安全管理", "name": "抽查大隊或分隊辦理訓練是否依訓練安全管理程序書執行", "result": "☑ 符合規範", "note": "訓練安全檢核表落實填報，教官助教比符合規範，現場設有專責安全官管制。"},
                        {"category": "義消推動制度了解", "name": "詢問對於今年本局推動的義消制度是否了解", "result": "☑ 符合規範", "note": "幹部與同仁均清楚了解今年度義消福利保險升級、出勤津貼核發與新式考核制度。"}
                    ], ensure_ascii=False),
                    strengths="1. 義消專長資料庫維護完善且落實定期更新，網址書籤設定齊全。\n2. 常訓出席率達 96% 且落實訓練安全管理程序書，幹部向心力高。",
                    deficiencies="本次查核無重大缺失事項。",
                    report_text="【臺東縣消防局民力科 督勤與業務查核紀錄表】\n受督導單位：臺東分隊\n督勤人員：張股長\n優良處置：優績 ｜ 缺失處置：無重大缺失",
                    status="已存檔"
                ),
                Inspection(
                    target_unit="關山分隊",
                    inspect_date=today - timedelta(days=25),
                    inspector="張股長",
                    score=0,
                    merit_status="口頭嘉勉",
                    demerit_status="請主管立即改善",
                    focus_items=json.dumps([
                        {"category": "義消專長資料庫", "name": "本科建置義消專長資料庫是否有定期更新及設定專用網址為書籤。", "result": "☒ 待改善", "note": "分隊電腦尚未設定書籤，且未即時更新新進義消專長資料，已現場協助設定並請於3日內補正。"},
                        {"category": "訓練與出勤紀錄", "name": "抽查本月義消定期訓練及出勤紀錄是否核實", "result": "☑ 符合規範", "note": "常年訓練名冊簽核確實，出勤時數登錄無誤。"},
                        {"category": "補助款規定熟悉度", "name": "抽查分隊辦理義消申請議員建議補助款是否熟悉相關規定事項", "result": "☑ 符合規範", "note": "補助款請領核銷單據完備。"},
                        {"category": "訓練安全管理", "name": "抽查大隊或分隊辦理訓練是否依訓練安全管理程序書執行", "result": "☑ 符合規範", "note": "實施安全檢核，教官配置確實。"},
                        {"category": "義消推動制度了解", "name": "詢問對於今年本局推動的義消制度是否了解", "result": "ℹ 宣導提醒", "note": "現場向分隊同仁說明本局新推動之義消福利保障與考核規定。"}
                    ], ensure_ascii=False),
                    strengths="縱谷線義消幹部向心力強，常訓出席踴躍。",
                    deficiencies="請分隊長督導於一週內完成義消專長資料庫網址書籤設定與新進人員專長登錄補正。",
                    report_text="【臺東縣消防局民力科 督勤與業務查核紀錄表】\n受督導單位：關山分隊\n督勤人員：張股長\n優良處置：口頭嘉勉 ｜ 缺失處置：請主管立即改善",
                    status="已存檔"
                ),
                Inspection(
                    target_unit="成功分隊",
                    inspect_date=today - timedelta(days=130),
                    inspector="陳科員",
                    score=0,
                    merit_status="口頭嘉勉",
                    demerit_status="無重大缺失",
                    focus_items=json.dumps([
                        {"category": "義消專長資料庫", "name": "本科建置義消專長資料庫是否有定期更新及設定專用網址為書籤。", "result": "☑ 符合規範", "note": "已設定專用網址書籤，資料庫定期維護。"},
                        {"category": "訓練與出勤紀錄", "name": "抽查本月義消定期訓練及出勤紀錄是否核實", "result": "☑ 符合規範", "note": "定期訓練簽到退與 APP 時數比對相符。"},
                        {"category": "補助款規定熟悉度", "name": "抽查分隊辦理義消申請議員建議補助款是否熟悉相關規定事項", "result": "☑ 符合規範", "note": "同仁對補助款規定清楚。"},
                        {"category": "訓練安全管理", "name": "抽查大隊或分隊辦理訓練是否依訓練安全管理程序書執行", "result": "☑ 符合規範", "note": "依程序書落實各項安全檢核。"},
                        {"category": "義消推動制度了解", "name": "詢問對於今年本局推動的義消制度是否了解", "result": "☑ 符合規範", "note": "同仁均了解本局推動之義消新制。"}
                    ], ensure_ascii=False),
                    strengths="海線協勤迅速，同仁對民力業務熟悉。",
                    deficiencies="本次查核無重大缺失事項。",
                    report_text="【臺東縣消防局民力科 督勤與業務查核紀錄表】\n受督導單位：成功分隊",
                    status="已存檔"
                )
            ]
            session.add_all(sample_inspections)

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Database init error: {e}")
    finally:
        session.close()


# 輔助資料庫存取方法
def get_db():
    """取得資料庫 Session Context"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass
