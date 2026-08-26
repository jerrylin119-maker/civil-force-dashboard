"""
模組二：會議/邀請/訃聞圖文辨識與公務行事曆 (OCR + AI)
支援【貼上文字通知】與【手機拍照/圖片上傳】，AI 智能結構化提取並一鍵轉入科內行事曆與 Google 日曆
"""
import os
import calendar
import urllib.parse
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from PIL import Image

from database import get_db, CalendarEvent
from config import EVENT_TYPE_OPTIONS, UPLOAD_DIR
from ai_helper import extract_event_from_image, extract_event_from_text, get_gemini_api_key
from export_helper import generate_calendar_ics

def get_google_calendar_url(ev: CalendarEvent) -> str:
    """生成 Google Calendar 網頁版一鍵加入行程連結"""
    d_str = ev.event_date.strftime("%Y%m%d")
    t_str = ev.event_time.replace(":", "") if ev.event_time else "090000"
    if len(t_str) == 4:
        t_str += "00"
    
    # 預設行程長度 1 小時
    dt_start = f"{d_str}T{t_str}"
    try:
        start_hour = int(t_str[:2])
        end_hour = min(23, start_hour + 1)
        dt_end = f"{d_str}T{end_hour:02d}{t_str[2:]}"
    except Exception:
        dt_end = dt_start

    details = f"【行程類別】：{ev.event_type}\n【出席長官/同仁】：{ev.attendees or '無'}\n【備註事項】：{ev.notes or '無'}\n\n（由民力科業務看板系統轉入）"
    
    params = {
        "action": "TEMPLATE",
        "text": f"【民力科】{ev.title}",
        "dates": f"{dt_start}/{dt_end}",
        "details": details,
        "location": ev.location or "消防局"
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

def render_calendar_module():
    st.markdown(
        """
        <div class="main-header">
            <h1>📅 模組二：會議/邀請/訃聞圖文辨識與行事曆</h1>
            <p>支援【直接貼上文字通知】與【手機拍照/圖片上傳】➔ AI 智能結構化提取 ➔ 一鍵轉入科內行事曆與 Google 日曆</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_text_input, tab_photo_ocr, tab_timeline, tab_month, tab_manage = st.tabs([
        "📝 方式一：直接貼上通知文字轉入",
        "📸 方式二：手機拍照 / 圖片 OCR 轉入",
        "⏳ 科內行事曆時間軸 (含 Google 日曆同步)",
        "📆 月曆全景檢視",
        "🗂️ 行程資料庫與 iCal 匯出"
    ])

    db = get_db()
    try:
        today = date.today()
        events = db.query(CalendarEvent).order_by(CalendarEvent.event_date.asc(), CalendarEvent.event_time.asc()).all()

        # ==========================================
        # TAB 1: 方式一：直接貼上通知文字轉入
        # ==========================================
        with tab_text_input:
            st.subheader("📝 貼上文字通知 (LINE 群組 / Email 邀請 / 訃聞文字) ➔ AI 解析轉入")
            
            st.markdown(
                """
                <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; border-radius: 6px; font-size: 0.9rem; color: #166534; margin-bottom: 1rem;">
                    💡 <b>文字快速轉入</b>：直接將 LINE 訊息、開會通告或公奠通知貼入下方，點擊<b>「✨ 啟動 AI 文字結構化解析」</b>，系統將自動提取事由、時間地點與出席人員，讓您一鍵存入科內行事曆！
                </div>
                """,
                unsafe_allow_html=True
            )

            # 快速範例按鈕群
            st.write("##### ⚡ 快速載入示範文字體驗：")
            c_eg1, c_eg2, c_eg3 = st.columns(3)
            with c_eg1:
                if st.button("📋 載入【局務主管會報】通知範例", use_container_width=True):
                    st.session_state["pasted_demo_text"] = f"事由：召開113年第三季消防局局務主管暨民力業務研討會報\n時間：{(today + timedelta(days=3)).strftime('%Y年%m月%d日')} 上午09:30\n地點：消防局本部6樓大簡報室\n主席：局長\n出席同仁：王科長、張股長、業務承辦同仁\n備註：請著常服出席，並備妥常訓籌備進度簡報。"
            with c_eg2:
                if st.button("🕊️ 載入【公祭訃聞奠禮】通知範例", use_container_width=True):
                    st.session_state["pasted_demo_text"] = f"訃聞通知：義消第一大隊故前副總隊長告別奠禮\n日期：{(today + timedelta(days=5)).strftime('%Y年%m月%d日')} (星期五)\n時間：上午08:30公奠 (家奠07:30)\n地點：市立第一殯儀館 景行廳\n出席人員：局長、主任秘書、王科長、義消各大隊長\n備註：請於08:00前現場集合整隊，著公務深色服裝或義消正服。"
            with c_eg3:
                if st.button("🚒 載入【裝備捐贈儀式】邀請範例", use_container_width=True):
                    st.session_state["pasted_demo_text"] = f"邀請函：宏達科技集團捐贈消防特搜救災警備車暨器材典禮\n時間：{(today + timedelta(days=7)).strftime('%Y年%m月%d日')} 上午10:00\n地點：信義分隊前大廣場\n出席長官：局長、民力科王科長、林科員\n備註：儀式約1小時，含致詞、頒發感謝狀及車輛器材展示。"

            default_text_val = st.session_state.get("pasted_demo_text", "")

            pasted_event_text = st.text_area(
                "請在此貼上通知文字內容：",
                value=default_text_val,
                height=180,
                placeholder="例：\n事由：113年度義勇消防人員常年訓練開訓精神動員\n時間：113年9月2日 下午14:00\n地點：消防訓練中心 綜合演練場\n出席人員：王科長、張股長、陳科員\n備註：請著公務制服出席。"
            )

            if st.button("✨ 啟動 AI 文字結構化解析並填入行程表單", type="primary", use_container_width=True):
                if not pasted_event_text.strip():
                    st.error("請先貼上通知文字內容！")
                else:
                    with st.spinner("🤖 Gemini 正在精準分析人事時地物並換算日期中..."):
                        parsed_data = extract_event_from_text(pasted_event_text)
                        st.session_state["parsed_event_data"] = parsed_data
                        st.session_state["saved_img_path"] = ""
                        st.rerun()

        # ==========================================
        # TAB 2: 方式二：手機拍照 / 圖片 OCR 轉入
        # ==========================================
        with tab_photo_ocr:
            st.subheader("📸 手機相機拍照或圖檔上傳 ➔ AI 視覺 OCR 辨識轉入")
            
            input_method = st.radio("選擇圖片來源方式", ["📱 手機相機即時拍照", "💻 本地檔案上傳 (JPG/PNG/WEBP)"], horizontal=True)
            
            uploaded_image = None
            if "手機相機" in input_method:
                camera_file = st.camera_input("請對準開會通知單、邀請卡或公祭訃聞拍照")
                if camera_file:
                    uploaded_image = camera_file
            else:
                upload_file = st.file_uploader("選擇公文/邀請卡/訃聞圖檔", type=["png", "jpg", "jpeg", "webp"])
                if upload_file:
                    uploaded_image = upload_file

            if uploaded_image is not None:
                img_col1, img_col2 = st.columns([1, 1.2])
                with img_col1:
                    st.image(uploaded_image, caption="📷 上傳之原始公文/通知圖檔", use_container_width=True)
                    
                    if st.button("✨ 啟動 Gemini Vision 視覺 OCR 智能辨識", type="primary", use_container_width=True):
                        with st.spinner("🤖 Gemini 視覺模型正在深度掃描圖片文字、日期、時間與地點中..."):
                            parsed_data = extract_event_from_image(uploaded_image)
                            st.session_state["parsed_event_data"] = parsed_data
                            
                            # 儲存圖片至本機 uploads
                            file_ext = uploaded_image.name.split(".")[-1] if hasattr(uploaded_image, "name") and "." in uploaded_image.name else "jpg"
                            save_filename = f"event_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                            save_path = UPLOAD_DIR / save_filename
                            try:
                                pil_img = Image.open(uploaded_image)
                                pil_img.save(save_path)
                                st.session_state["saved_img_path"] = str(save_path)
                            except Exception:
                                st.session_state["saved_img_path"] = ""
                            st.rerun()

        # ==========================================
        # 通用確認與存入行事曆表單 (不管是貼文字或拍照辨識皆在此確認)
        # ==========================================
        if "parsed_event_data" in st.session_state and st.session_state["parsed_event_data"]:
            parsed = st.session_state["parsed_event_data"]
            st.markdown("---")
            st.success("✅ **AI 辨識提取完成！請核對下列資訊，確認後點擊「💾 一鍵存入科內行事曆」：**")

            with st.form("confirm_event_form"):
                try:
                    default_event_date = datetime.strptime(parsed.get("event_date", ""), "%Y-%m-%d").date()
                except Exception:
                    default_event_date = today + timedelta(days=3)

                f_title = st.text_input("活動/會議/公奠事由 *", value=parsed.get("title", ""))
                
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    f_date = st.date_input("活動日期 *", value=default_event_date)
                with c_d2:
                    f_time = st.text_input("時間 (24小時制，如 09:30, 14:00)", value=parsed.get("event_time", "09:00"))
                
                f_loc = st.text_input("地點 (含會議室/殯儀館廳別)", value=parsed.get("location", ""))
                
                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    parsed_type = parsed.get("event_type", "會議通知")
                    type_idx = EVENT_TYPE_OPTIONS.index(parsed_type) if parsed_type in EVENT_TYPE_OPTIONS else 0
                    f_type = st.selectbox("行程類別", EVENT_TYPE_OPTIONS, index=type_idx)
                with c_t2:
                    f_attendees = st.text_input("指定出席長官 / 承辦人員", value=parsed.get("attendees", "科長、承辦人"))
                
                f_notes = st.text_area("備註事項 (服裝要求、家奠/公奠時間、攜帶文件)", value=parsed.get("notes", ""))

                btn_save_event = st.form_submit_button("💾 一鍵存入科內行事曆資料庫", type="primary", use_container_width=True)

                if btn_save_event:
                    if not f_title:
                        st.error("請填寫活動事由！")
                    else:
                        new_event = CalendarEvent(
                            title=f_title.strip(),
                            event_date=f_date,
                            event_time=f_time.strip(),
                            location=f_loc.strip(),
                            event_type=f_type,
                            attendees=f_attendees.strip(),
                            raw_image_path=st.session_state.get("saved_img_path", ""),
                            notes=f_notes.strip() if f_notes else "",
                            status="預定"
                        )
                        db.add(new_event)
                        db.commit()
                        st.session_state["parsed_event_data"] = None
                        st.session_state["pasted_demo_text"] = ""
                        st.success("🎉 行程已成功加入科內行事曆！已同步呈現於【時間軸視圖】與【月曆】！")
                        st.rerun()

        # ==========================================
        # TAB 3: 科內行事曆時間軸 (含 Google 日曆同步)
        # ==========================================
        with tab_timeline:
            st.subheader("⏳ 科內即將到來公務行程時間軸")
            
            today_events = [e for e in events if e.event_date == today]
            this_week_events = [e for e in events if today < e.event_date <= today + timedelta(days=7)]
            future_events = [e for e in events if e.event_date > today + timedelta(days=7)]
            past_events = [e for e in events if e.event_date < today]

            type_colors = {
                "會議通知": "badge-info",
                "公祭訃聞": "badge-neutral",
                "邀請卡/典禮": "badge-warning",
                "局內公務活動": "badge-success",
                "常訓/演練": "badge-urgent",
                "其他": "badge-neutral"
            }

            def render_event_card(ev):
                days_diff = (ev.event_date - today).days
                badge_class = type_colors.get(ev.event_type, "badge-neutral")
                
                if days_diff == 0:
                    countdown_badge = '<span class="badge badge-urgent">🔥 今日行程</span>'
                elif days_diff > 0:
                    countdown_badge = f'<span class="badge badge-info">剩餘 {days_diff} 天</span>'
                else:
                    countdown_badge = f'<span class="badge badge-neutral">已過 {-days_diff} 天</span>'

                gcal_url = get_google_calendar_url(ev)

                with st.container(border=True):
                    h_col1, h_col2 = st.columns([3.2, 1.8])
                    with h_col1:
                        st.markdown(
                            f"""
                            <div style="font-size: 1.15rem; font-weight: 700; color: #1e3a8a;">
                                🕒 {ev.event_time} ｜ {ev.title}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with h_col2:
                        st.markdown(
                            f"""
                            <div style='text-align: right;'>
                                <span class='badge {badge_class}'>{ev.event_type}</span> {countdown_badge}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    c1, c2, c3 = st.columns([1.4, 1.4, 1.7])
                    with c1:
                        st.markdown(f"📅 <b>日期：</b> {ev.event_date.strftime('%Y-%m-%d')} ({get_chinese_weekday(ev.event_date)})", unsafe_allow_html=True)
                        st.markdown(f"📍 <b>地點：</b> {ev.location or '局本部'}", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"👥 <b>出席同仁：</b> {ev.attendees or '全體同仁'}", unsafe_allow_html=True)
                        st.markdown(f"📌 <b>狀態：</b> {ev.status}", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"📝 <b>備註：</b> {ev.notes or '無特殊備註'}", unsafe_allow_html=True)

                    # 🌟 同步 Google 日曆連結
                    st.markdown(
                        f"""
                        <div style="text-align: right; margin-top: 6px;">
                            <a href="{gcal_url}" target="_blank" style="display: inline-block; background: #ffffff; color: #2563eb; border: 1px solid #93c5fd; padding: 4px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; text-decoration: none; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                                🗓️ 一鍵同步至 Google 日曆 ↗
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            if today_events:
                st.markdown("### 🔴 今日即將進行")
                for e in today_events:
                    render_event_card(e)

            if this_week_events:
                st.markdown("### 🟡 本週行程 (未來 7 天內)")
                for e in this_week_events:
                    render_event_card(e)

            if future_events:
                st.markdown("### 🔵 未來重要行程")
                for e in future_events:
                    render_event_card(e)

            if not today_events and not this_week_events and not future_events:
                st.info("💡 目前未來尚無排定行程，歡迎由上方【貼上文字】或【拍照辨識】快速錄入！")

            if past_events:
                with st.expander(f"📁 檢視歷史過期行程 ({len(past_events)} 筆)"):
                    for e in reversed(past_events):
                        render_event_card(e)

        # ==========================================
        # TAB 4: 月曆全景檢視
        # ==========================================
        with tab_month:
            st.subheader("📆 月曆全景檢視")
            
            c_y, c_m = st.columns([1, 1])
            with c_y:
                view_year = st.selectbox("年份", [today.year - 1, today.year, today.year + 1], index=1)
            with c_m:
                view_month = st.selectbox("月份", list(range(1, 13)), index=today.month - 1)

            month_events = [e for e in events if e.event_date.year == view_year and e.event_date.month == view_month]

            st.write(f"#### {view_year} 年 {view_month} 月 預定行程彙整 (共 {len(month_events)} 項活動)")
            
            if month_events:
                month_days_events = {}
                for e in month_events:
                    day = e.event_date.day
                    if day not in month_days_events:
                        month_days_events[day] = []
                    month_days_events[day].append(e)

                for day in sorted(month_days_events.keys()):
                    day_date = date(view_year, view_month, day)
                    is_today = (day_date == today)
                    prefix = "🔥 [今日] " if is_today else ""
                    
                    st.markdown(f"##### 📌 {prefix}{view_year}/{view_month}/{day} ({get_chinese_weekday(day_date)})")
                    for ev in month_days_events[day]:
                        g_url = get_google_calendar_url(ev)
                        st.markdown(
                            f"""
                            - **[{ev.event_time}]** `{ev.event_type}` **{ev.title}** 
                              <br>&nbsp;&nbsp;&nbsp;&nbsp;📍 地點：{ev.location or '未註記'} ｜ 👥 出席：{ev.attendees or '無'} ｜ 📝 備註：{ev.notes or '無'}
                              &nbsp;&nbsp;<a href="{g_url}" target="_blank" style="font-size: 0.8rem; color: #2563eb;">[同步Google日曆 ↗]</a>
                            """,
                            unsafe_allow_html=True
                        )
                    st.markdown("---")
            else:
                st.info(f"💡 {view_year} 年 {view_month} 月尚無排定任何公務行程。")

        # ==========================================
        # TAB 5: 行程資料庫與 iCal 匯出
        # ==========================================
        with tab_manage:
            st.subheader("🗂️ 行事曆資料庫清單與 iCal 匯出")
            
            col_exp1, col_exp2 = st.columns([1, 1])
            with col_exp1:
                ics_data = generate_calendar_ics(events)
                st.download_button(
                    label="📲 匯出 iCalendar (.ics) 同步至 Google / Outlook / 蘋果日曆",
                    data=ics_data,
                    file_name=f"民力科公務行事曆_{today.strftime('%Y%m%d')}.ics",
                    mime="text/calendar",
                    use_container_width=True
                )

            table_data = []
            for e in events:
                table_data.append({
                    "ID": e.id,
                    "日期": e.event_date.strftime("%Y-%m-%d"),
                    "時間": e.event_time,
                    "事由": e.title,
                    "類別": e.event_type,
                    "地點": e.location or "",
                    "指定出席人員": e.attendees or "",
                    "備註": e.notes or "",
                    "狀態": e.status
                })
            
            if table_data:
                df_ev = pd.DataFrame(table_data)
                st.dataframe(df_ev.drop(columns=["ID"]), use_container_width=True, hide_index=True)

                st.markdown("##### 🗑️ 刪除或調整指定行程")
                del_id = st.selectbox("選擇要刪除的行程", options=[f"{e.id} - {e.event_date} {e.title}" for e in events])
                if st.button("❌ 刪除選取行程", type="secondary"):
                    target_id = int(del_id.split(" - ")[0])
                    item_to_del = db.query(CalendarEvent).filter(CalendarEvent.id == target_id).first()
                    if item_to_del:
                        db.delete(item_to_del)
                        db.commit()
                        st.success("✅ 行程已刪除！")
                        st.rerun()

    finally:
        db.close()

def get_chinese_weekday(d: date) -> str:
    """轉換為中文星期幾"""
    weekdays = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    return weekdays[d.weekday()]
