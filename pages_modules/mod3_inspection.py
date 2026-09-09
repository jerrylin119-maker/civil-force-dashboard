"""
模組三：督勤管理與報告產出機
全景掌握臺東縣轄內四大隊 33 所分隊半年督勤覆蓋率，支援新業務重點擴充、預設項目現場勾選，並總結為【優良：優績 / 口頭嘉勉】與【缺失：劣蹟註記 / 請主管立即改善】雙軌處置，一鍵產出公務 Word 報告
"""
import json
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path

from database import get_db, FireUnit, Inspection, InspectionFocusItem
from config import REPORTS_DIR, load_preset_notes, save_preset_notes
from export_helper import (
    generate_inspection_docx,
    synthesize_inspection_sentence,
    synthesize_defect_sentence
)

# 預設常態與新業務督勤重點範本
DEFAULT_PRESET_FOCUS_TEXT = (
    "1. 本科建置義消專長資料庫是否有定期更新及設定專用網址為書籤\n"
    "2. 抽查本月義消定期訓練及出勤紀錄是否核實\n"
    "3. 抽查分隊辦理義消申請議員建議補助款是否熟悉相關規定事項\n"
    "4. 抽查大隊或分隊辦理訓練是否依訓練安全管理程序書執行\n"
    "5. 詢問對於今年本局推動的義消制度是否了解"
)



def render_inspection_module():
    st.markdown(
        """
        <div class="main-header">
            <h1>🛡️ 模組三：督勤管理與報告產出機</h1>
            <p>臺東縣四大隊分隊半年督導覆蓋率 ➔ 預先產出督勤重點 ➔ 現場勾選評估 ➔ 總結【優績/口頭嘉勉】與【劣蹟註記/請主管立即改善】處置</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    db = get_db()
    try:
        today = date.today()
        six_months_ago = today - timedelta(days=180)

        # 讀取轄內所有消防大隊與分隊
        units = db.query(FireUnit).all()
        all_inspections = db.query(Inspection).order_by(Inspection.inspect_date.desc()).all()
        
        # 讀取預先設定的重點項目庫
        db_focus_items = db.query(InspectionFocusItem).filter(InspectionFocusItem.is_active == True).all()

        # 計算統計指標
        unit_stats = []
        for u in units:
            unit_insps_6m = [i for i in all_inspections if i.target_unit == u.unit_name and i.inspect_date >= six_months_ago]
            unit_insps_all = [i for i in all_inspections if i.target_unit == u.unit_name]
            
            count_6m = len(unit_insps_6m)
            last_date = unit_insps_all[0].inspect_date if unit_insps_all else None
            days_since_last = (today - last_date).days if last_date else 999
            
            if count_6m == 0:
                status_level = "low"
                status_text = "🔴 0 次 (半年未督勤)"
            elif count_6m == 1:
                status_level = "medium"
                status_text = "🟡 1 次 (已督導1次)"
            else:
                status_level = "high"
                status_text = f"🟢 {count_6m} 次 (覆蓋良好)"

            unit_stats.append({
                "name": u.unit_name,
                "type": u.unit_type,
                "district": u.district or "臺東大隊轄區",
                "count_6m": count_6m,
                "last_date": last_date,
                "days_since_last": days_since_last,
                "status_level": status_level,
                "status_text": status_text
            })

        total_units = len(units)
        high_count = len([us for us in unit_stats if us["status_level"] == "high"])
        med_count = len([us for us in unit_stats if us["status_level"] == "medium"])
        low_count = len([us for us in unit_stats if us["status_level"] == "low"])
        coverage_rate = int(((total_units - low_count) / total_units * 100)) if total_units > 0 else 0

        # 功能分頁
        tab_coverage, tab_record, tab_settings, tab_history = st.tabs([
            "🗺️ 臺東四大隊分隊半年督勤覆蓋率全覽",
            "📝 現場督勤填報與處置結論產出",
            "⚙️ 督導重點項目庫管理 (含新業務擴充)",
            "📁 歷史督勤檔案庫 (實體報告查詢)"
        ])

        # ==========================================
        # TAB 1: 半年督導覆蓋率看板 (無任何優先排序)
        # ==========================================
        with tab_coverage:
            st.subheader("🗺️ 臺東縣消防局轄區半年督勤覆蓋率全景")
            
            # KPI 指標卡片
            c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
            with c_kpi1:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">總受督消防單位數</div>
                        <div class="kpi-value" style="color: #1e293b;">{total_units} <span style="font-size: 1rem;">所</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with c_kpi2:
                rate_color = "#10b981" if coverage_rate >= 80 else "#f59e0b"
                st.markdown(
                    f"""
                    <div class="kpi-card" style="border-top: 3px solid {rate_color};">
                        <div class="kpi-title">半年督勤覆蓋率</div>
                        <div class="kpi-value" style="color: {rate_color};">{coverage_rate}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with c_kpi3:
                st.markdown(
                    f"""
                    <div class="kpi-card" style="border-top: 3px solid #ef4444;">
                        <div class="kpi-title" style="color: #b91c1c;">🔴 半年內 0 次</div>
                        <div class="kpi-value" style="color: #dc2626;">{low_count} <span style="font-size: 1rem;">所</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with c_kpi4:
                st.markdown(
                    f"""
                    <div class="kpi-card" style="border-top: 3px solid #10b981;">
                        <div class="kpi-title" style="color: #15803d;">🟢 覆蓋良好 (&gt;=2次)</div>
                        <div class="kpi-value" style="color: #16a34a;">{high_count} <span style="font-size: 1rem;">所</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

            # 轄區單位色彩全覽網格
            st.markdown("### 🏢 臺東縣消防局轄區各大隊分隊督導覆蓋狀態")
            
            group_by_mode = st.radio("分組顯示方式", ["🏢 依四大隊及專屬分隊分組 (臺東、關山、成功、大武、局本部專屬任務隊)", "🏷️ 依單位類別分組 (消防大隊、消防分隊、專屬分隊)"], horizontal=True)

            if "四大隊" in group_by_mode:
                districts_order = [
                    "臺東大隊轄區",
                    "臺東大隊(離島)",
                    "關山大隊轄區",
                    "成功大隊轄區",
                    "大武大隊轄區",
                    "局本部專屬任務隊"
                ]
                existing_districts = list(set([u.district for u in units if u.district]))
                ordered_districts = [d for d in districts_order if d in existing_districts] + [d for d in existing_districts if d not in districts_order]
                
                for dist in ordered_districts:
                    st.write(f"##### 📍 {dist}")
                    dist_units = [us for us in unit_stats if us["district"] == dist]
                    
                    cols = st.columns(4)
                    for idx, u_stat in enumerate(dist_units):
                        c = cols[idx % 4]
                        with c:
                            days_txt = f"上次：{u_stat['days_since_last']} 天前" if u_stat['days_since_last'] < 900 else "尚未有紀錄"
                            css_class = f"coverage-{u_stat['status_level']}"
                            st.markdown(
                                f"""
                                <div class="coverage-unit-card {css_class}">
                                    <div style="font-weight: 700; font-size: 0.95rem;">{u_stat['name']}</div>
                                    <div style="font-size: 0.8rem; margin-top: 4px;">{u_stat['status_text']}</div>
                                    <div style="font-size: 0.75rem; opacity: 0.85; margin-top: 2px;">{days_txt}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
            else:
                categories = sorted(list(set([u.unit_type for u in units])))
                for cat in categories:
                    st.write(f"##### 🏢 {cat}")
                    cat_units = [us for us in unit_stats if us["type"] == cat]
                    
                    cols = st.columns(4)
                    for idx, u_stat in enumerate(cat_units):
                        c = cols[idx % 4]
                        with c:
                            days_txt = f"上次：{u_stat['days_since_last']} 天前" if u_stat['days_since_last'] < 900 else "尚未有紀錄"
                            css_class = f"coverage-{u_stat['status_level']}"
                            st.markdown(
                                f"""
                                <div class="coverage-unit-card {css_class}">
                                    <div style="font-weight: 700; font-size: 0.95rem;">{u_stat['name']}</div>
                                    <div style="font-size: 0.8rem; margin-top: 4px;">{u_stat['status_text']}</div>
                                    <div style="font-size: 0.75rem; opacity: 0.85; margin-top: 2px;">{days_txt}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

        # ==========================================
        # TAB 2: 現場督勤填報與處置結論產出
        # ==========================================
        with tab_record:
            st.subheader("📝 現場督勤查核填報與處置結論產出")
            
            st.markdown(
                """
                <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 10px 14px; border-radius: 6px; font-size: 0.9rem; color: #1e3a8a; margin-bottom: 1rem;">
                    💡 <b>督勤考核處置機制</b>：<br>
                    • <b>無須打分數</b>，依現場查核實況判定：<br>
                    &nbsp;&nbsp;🌟 <b>整體優良處置</b>：判定為<b>「優績」</b>（提報獎勵）或<b>「口頭嘉勉」</b>。<br>
                    &nbsp;&nbsp;⚠️ <b>缺失改善處置</b>：判定為<b>「劣蹟註記」</b>或<b>「請主管立即改善」</b>（或無重大缺失）。<br>
                    • 點擊<b>「🚀 一鍵生成公務督勤報告」</b>，系統自動排版生成標準公務 Word (.docx) 檔並永久存檔！
                </div>
                """,
                unsafe_allow_html=True
            )

            # 取得當前預先產出之重點項目清單
            active_focus_items = []
            if db_focus_items:
                for idx, it in enumerate(db_focus_items, 1):
                    active_focus_items.append({"idx": idx, "name": it.item_name, "category": it.category})
            else:
                raw_lines = [line.strip() for line in DEFAULT_PRESET_FOCUS_TEXT.split("\n") if line.strip()]
                for idx, line in enumerate(raw_lines, 1):
                    clean_name = line.lstrip("0123456789.、: -")
                    active_focus_items.append({"idx": idx, "name": clean_name if clean_name else line, "category": "常態督勤"})

            # 現場臨時追加新業務督勤項目折疊區
            with st.expander("➕ 因應新業務/專案臨時追加督勤項目 (選填)", expanded=False):
                col_n1, col_n2, col_n3 = st.columns([1.2, 2.5, 1])
                with col_n1:
                    new_item_cat = st.selectbox("新業務類別", ["新業務專案", "防災士與韌性社區", "科技救災與無人機", "演訓與常訓", "裝備與防汛", "法規與福利宣導", "其他"], key="temp_cat")
                with col_n2:
                    new_item_txt = st.text_input("輸入新業務查核重點名稱", placeholder="例：無人機科技救災飛手證照與圖資傳輸測試", key="temp_txt")
                with col_n3:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("➕ 新增至本次清單", use_container_width=True):
                        if new_item_txt.strip():
                            new_f_obj = InspectionFocusItem(
                                category=new_item_cat,
                                item_name=new_item_txt.strip(),
                                description="因應新業務即時新增",
                                is_active=True
                            )
                            db.add(new_f_obj)
                            db.commit()
                            st.success(f"✅ 已成功將新業務項目【{new_item_txt.strip()}】加入督導清單！")
                            st.rerun()

            with st.form("inspection_form"):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    unit_options = [u.unit_name for u in units]
                    f_unit = st.selectbox("受督導單位 *", unit_options)
                    f_date = st.date_input("督勤日期 *", value=today)
                with r_col2:
                    current_user = st.session_state.get("user")
                    default_inspector = current_user.get("display_name", "民力科同仁") if current_user else "民力科同仁"
                    f_inspector = st.text_input("督勤同仁姓名 *", value=default_inspector)

                st.markdown("---")
                st.markdown("#### 🔍 督導重點事項現場查核與勾選 (共 %d 項)" % len(active_focus_items))
                
                # 針對 5 大重點項目提供精確對應之現況說明範例
                ITEM_SPECIFIC_PLACEHOLDERS = {
                    "義消專長資料庫": "例：分隊已將專長資料庫網址設為瀏覽器書籤，本月已完成新增2名具救護專長義消基本資料。",
                    "定期訓練及出勤紀錄": "例：抽查8月份常訓簽到名冊25名全員核實簽到，APP出勤時數與協勤紀錄相符。",
                    "議員建議補助款": "例：承辦同仁熟悉議員補助款請領程序、核銷單據黏貼與器材保管標籤規範。",
                    "訓練安全管理程序書": "例：訓練安全檢核表落實填報，教官助教比符合規範，現場設有專責安全官管制。",
                    "義消制度": "例：幹部與同仁均清楚了解今年度義消福利保險升級、出勤津貼核發與新式考核制度。"
                }

                preset_notes_dict = load_preset_notes()
                st.info("💡 **填報說明**：各重點項目之「狀況說明」可**直接點選下拉選單快速套用**，亦可**直接在下方自訂欄位打字**（有打字則優先採用自訂內容）。若需新增或修改下拉選項，請至上方 **「⚙️ 督導重點項目庫管理」** 維護。")

                checked_items = []
                for it in active_focus_items:
                    it_idx = it["idx"]
                    it_name = it["name"]
                    it_cat = it.get("category", "常態督勤")
                    
                    # 匹配精確範例文字與狀況詞庫
                    matched_placeholder = "例：現場查核符合規定，運作正常。"
                    matched_preset_list = ["查核良好，運作正常。", "現場符合常態業務管理規範。"]
                    for k, ph in ITEM_SPECIFIC_PLACEHOLDERS.items():
                        if k in it_name or k in it_cat:
                            matched_placeholder = ph
                            if k in preset_notes_dict:
                                matched_preset_list = preset_notes_dict[k]
                            break
                    
                    cat_tag = f"<span style='background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;'>{it_cat}</span>"
                    st.markdown(f"**📌 重點 {it_idx}** {cat_tag} ：**{it_name}**", unsafe_allow_html=True)
                    
                    c_res, c_note = st.columns([1, 2.5])
                    with c_res:
                        res = st.selectbox(
                            "查核結果",
                            ["☑ 符合規範 / 良好", "☒ 待改善 / 需追蹤", "ℹ 宣導提醒 / 政策轉達", "➖ 不適用 / 本次未查"],
                            key=f"insp_res_{it_idx}"
                        )
                    with c_note:
                        preset_dropdown_opts = matched_preset_list + ["✍️ 自行手動輸入 (請在下方欄位打字)..."]
                        chosen_preset = st.selectbox(
                            "⚡ 現場狀況快捷選單 (點選即採用此範本)",
                            preset_dropdown_opts,
                            key=f"insp_sel_{it_idx}"
                        )
                        custom_input = st.text_input(
                            "📝 自訂狀況說明 / 數據 (若選上方選項可留空；若在此輸入則優先以此內容為準)",
                            placeholder=matched_placeholder,
                            key=f"insp_custom_{it_idx}"
                        )

                    # 決定最終採用的 note 文字：若有自訂輸入則用自訂輸入，否則採用下拉選單文字
                    if custom_input and custom_input.strip():
                        final_note = custom_input.strip()
                    elif "自行手動輸入" not in chosen_preset:
                        final_note = chosen_preset
                    else:
                        final_note = "查核良好"

                    clean_res = res.split(" / ")[0]
                    checked_items.append({
                        "category": it_cat,
                        "name": it_name,
                        "result": clean_res,
                        "note": final_note
                    })
                    st.markdown("<div style='border-bottom: 1px dashed #cbd5e1; margin: 6px 0 10px 0;'></div>", unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("#### ⚖️ 督導總結處置判定 (免評分，改以具體處置判定)")

                c_conc1, c_conc2 = st.columns(2)
                with c_conc1:
                    st.markdown("##### 🌟 優良成效處置判定")
                    f_merit = st.radio(
                        "優良考評結果",
                        ["優績 (表現優異，提報局端行政獎勵)", "口頭嘉勉 (現場肯定並予以口頭嘉勉)", "符合良好 (符合常態業務管理規範)"],
                        index=1,
                        help="整體優良部分評定為優績或口頭嘉勉。"
                    )
                    f_strengths = st.text_area(
                        "優良事蹟具體說明",
                        placeholder="例：1. 義消專長資料庫維護完善且落實定期更新。\n2. 常訓出席率達95%且落實訓練安全管理程序書，幹部向心力高。"
                    )

                with c_conc2:
                    st.markdown("##### ⚠️ 缺失改善處置判定")
                    f_demerit = st.radio(
                        "缺失處置要求",
                        ["無重大缺失事項 (查核良好，無缺失列管)", "請主管立即改善 (限期改善，請分隊長立即督導改善並回報)", "劣蹟註記 (嚴重缺失，列入年度考評劣蹟註記)"],
                        index=0,
                        help="有缺失部分評定為請主管立即改善或劣蹟註記。"
                    )
                    f_deficiencies = st.text_area(
                        "缺失事項與改善要求說明",
                        placeholder="例：1. 請分隊長督導於一週內完成義消專長資料庫網址書籤設定與資料補正。\n2. 辦理常訓請確實指派安全官落實安全管制並回傳佐證。"
                    )

                # 簡化字串
                clean_merit = f_merit.split(" (")[0]
                clean_demerit = f_demerit.split(" (")[0]

                submit_insp = st.form_submit_button("🚀 一鍵生成公務督勤報告並存檔", type="primary", use_container_width=True)

                if submit_insp:
                    if not f_unit or not f_inspector:
                        st.error("請確認填寫受督單位與督勤同仁姓名！")
                    else:
                        # 自動彙整督導所見良好事項與缺失事項 (未檢查者自動濾除，已檢查者轉換為通順公文語句)
                        good_items = []
                        defect_items = []
                        for it in checked_items:
                            res_val = it['result']
                            if any(k in res_val for k in ["待改善", "需追蹤", "缺失", "不符", "☒"]):
                                defect_sentence = synthesize_defect_sentence(it)
                                if defect_sentence:
                                    defect_items.append(f"{len(defect_items)+1}. {defect_sentence}")
                            else:
                                good_sentence = synthesize_inspection_sentence(it)
                                if good_sentence:
                                    good_items.append(f"{len(good_items)+1}. {good_sentence}")

                        # 組合「二、 督導所見事項彙整」
                        merit_summary_map = {
                            "口頭嘉勉": "給予口頭嘉勉",
                            "優績": "給予優績",
                            "符合良好": "符合良好"
                        }
                        merit_phrase = merit_summary_map.get(clean_merit, f"給予{clean_merit}")
                        
                        sec2_parts = []
                        if good_items:
                            sec2_parts.extend(good_items)
                        else:
                            sec2_parts.append("現場各項常態業務查核運作良好。")
                            
                        if f_strengths and f_strengths.strip():
                            sec2_parts.append(f"\n**【補充說明】**：\n{f_strengths.strip()}")
                            
                        sec2_parts.append(f"\n📌 **總結處置**：現場整體運作良好，**{merit_phrase}**。")
                        sec2_md = "\n".join(sec2_parts)

                        # 組合「三、 督導缺失事項與處置要求」
                        demerit_summary_map = {
                            "劣蹟註記": "給予劣蹟註記",
                            "請主管立即改善": "請主管立即改善",
                            "無重大缺失事項": "無重大缺失事項"
                        }
                        demerit_phrase = demerit_summary_map.get(clean_demerit, f"給予{clean_demerit}")

                        sec3_parts = []
                        if defect_items:
                            sec3_parts.extend(defect_items)
                        if f_deficiencies and f_deficiencies.strip():
                            sec3_parts.append(f"\n**【改善要求】**：\n{f_deficiencies.strip()}")
                            
                        if sec3_parts or clean_demerit in ["劣蹟註記", "請主管立即改善"]:
                            if not sec3_parts:
                                sec3_parts.append("現場查有待改善事項，列管督導。")
                            sec3_parts.append(f"\n⚠️ **處置要求**：現場查核缺失事項列管追蹤，**{demerit_phrase}**。")
                            sec3_md = "\n".join(sec3_parts)
                        else:
                            sec3_md = "經現場各項重點查核，本次督勤無重大缺失事項。"

                        # 格式化完整督勤報告 Markdown 文本
                        report_md = f"""# 臺東縣消防局民力科 督勤與業務查核紀錄表

- **受督導單位**：{f_unit}
- **督勤日期**：{f_date.strftime('%Y-%m-%d')}
- **督勤人員**：{f_inspector}
- **綜合督勤處置**：🌟 【優良處置】：`{clean_merit}` ｜ ⚠️ 【缺失處置】：`{clean_demerit}`

---

### 一、 督導重點事項查核與宣導紀要
"""
                        for idx, it in enumerate(checked_items, 1):
                            res_icon = it['result']
                            cat_label = f"[{it.get('category', '重點')}] " if it.get('category') != '常態督勤' else ""
                            report_md += f"{idx}. **{cat_label}{it['name']}**\n   - 查核結果：`{res_icon}` ｜ 現場狀況：{it['note']}\n"

                        report_md += f"""
---

### 二、 督導所見事項彙整（處置判定：【{clean_merit}】）
{sec2_md}

---

### 三、 督導缺失事項與處置要求（處置判定：【{clean_demerit}】）
{sec3_md}

---
*督勤同仁簽章：{f_inspector}　　受督單位主管簽章：___________　　科長核閱：___________*
"""

                        # 1. 存入 SQLite 資料庫
                        new_insp = Inspection(
                            target_unit=f_unit,
                            inspect_date=f_date,
                            inspector=f_inspector,
                            focus_items=json.dumps(checked_items, ensure_ascii=False),
                            score=0,
                            merit_status=clean_merit,
                            demerit_status=clean_demerit,
                            strengths=f_strengths,
                            deficiencies=f_deficiencies,
                            report_text=report_md,
                            status="已存檔"
                        )
                        db.add(new_insp)
                        db.commit()

                        # 2. 生成標準 Word (.docx) 並儲存至本地實體目錄
                        docx_buf = generate_inspection_docx(
                            unit_name=f_unit,
                            inspect_date=f_date.strftime('%Y-%m-%d'),
                            inspector=f_inspector,
                            focus_items=checked_items,
                            strengths=f_strengths,
                            deficiencies=f_deficiencies,
                            merit_status=clean_merit,
                            demerit_status=clean_demerit,
                            report_text=report_md
                        )
                        
                        file_base_name = f"臺東縣消防局督勤報告_{f_unit}_{f_date.strftime('%Y%m%d')}_{f_inspector}_{new_insp.id}"
                        docx_file_path = REPORTS_DIR / f"{file_base_name}.docx"
                        md_file_path = REPORTS_DIR / f"{file_base_name}.md"

                        try:
                            with open(docx_file_path, "wb") as f_docx:
                                f_docx.write(docx_buf.getvalue())
                            with open(md_file_path, "w", encoding="utf-8") as f_md:
                                f_md.write(report_md)
                        except Exception as e:
                            pass

                        st.session_state["latest_insp_id"] = new_insp.id
                        st.session_state["latest_insp_obj"] = {
                            "unit": f_unit,
                            "date": f_date.strftime('%Y-%m-%d'),
                            "inspector": f_inspector,
                            "merit": clean_merit,
                            "demerit": clean_demerit,
                            "items": checked_items,
                            "strengths": f_strengths,
                            "deficiencies": f_deficiencies,
                            "report_md": report_md,
                            "docx_buf": docx_buf.getvalue(),
                            "docx_path": str(docx_file_path)
                        }
                        st.success(f"🎉 【{f_unit}】督勤紀錄已成功存檔！Word 文件已自動儲存至本機檔案庫！")
                        st.rerun()

            # 若剛完成存檔，提供即時預覽與 Word/MD 下載
            if "latest_insp_obj" in st.session_state and st.session_state["latest_insp_obj"]:
                latest = st.session_state["latest_insp_obj"]
                st.markdown("---")
                st.markdown("### 📄 最新產出之公務督勤報告")
                
                # 儲存位置告知橫幅
                st.markdown(
                    f"""
                    <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-left: 5px solid #16a34a; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px;">
                        <b>💾 報告實體儲存位置</b>：<br>
                        • <b>本地電腦目錄</b>：<code>{latest.get('docx_path', 'civil_force_dashboard/reports/inspections/')}</code><br>
                        • <b>處置結論</b>：🌟 優良判定：<b>{latest.get('merit', '口頭嘉勉')}</b> ｜ ⚠️ 缺失判定：<b>{latest.get('demerit', '無重大缺失')}</b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                with st.container(border=True):
                    st.markdown(latest["report_md"])

                # 匯出按鈕群
                d_c1, d_c2, d_c3 = st.columns(3)
                with d_c1:
                    st.download_button(
                        label="📥 下載標準公務 Word (.docx) 報告",
                        data=latest.get("docx_buf", b""),
                        file_name=f"臺東縣消防局督勤報告_{latest['unit']}_{latest['date']}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True
                    )
                with d_c2:
                    st.download_button(
                        label="📥 下載 Markdown (.md) 檔",
                        data=latest["report_md"],
                        file_name=f"臺東縣消防局督勤報告_{latest['unit']}_{latest['date']}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                with d_c3:
                    st.download_button(
                        label="📥 下載純文字 (.txt) 檔",
                        data=latest["report_md"],
                        file_name=f"臺東縣消防局督勤報告_{latest['unit']}_{latest['date']}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

        # ==========================================
        # TAB 3: 督導重點項目與狀況說明選項維護
        # ==========================================
        with tab_settings:
            st.subheader("⚙️ 督導重點項目與現場狀況說明選項維護")
            st.markdown(
                """
                <div style="background: #f8fafc; border-left: 4px solid #0284c7; padding: 10px 14px; border-radius: 6px; font-size: 0.9rem; color: #334155; margin-bottom: 1.2rem;">
                    💡 <b>維護說明</b>：您可以在此直接編輯<b>督導重點項目清單</b>，以及自訂各重點項目的<b>現場狀況說明下拉選單選項</b>。儲存後現場填報表單將<b>即時同步更新</b>！
                </div>
                """,
                unsafe_allow_html=True
            )

            # ── 區塊 1：督導重點項目清單整批維護 ──
            st.markdown("#### 📌 1. 督導重點項目清單維護")
            
            if db_focus_items:
                current_db_text = "\n".join([f"{idx}. [{it.category}] {it.item_name}" for idx, it in enumerate(db_focus_items, 1)])
            else:
                current_db_text = DEFAULT_PRESET_FOCUS_TEXT

            with st.form("save_focus_items_form"):
                focus_text_input = st.text_area(
                    "當前督導重點清單 (每行一項，儲存後現場填報表單將立即採用此清單)：",
                    value=current_db_text,
                    height=160
                )

                if st.form_submit_button("💾 儲存並更新督導重點項目清單", type="primary", use_container_width=True):
                    lines = [l.strip() for l in focus_text_input.split("\n") if l.strip()]
                    if not lines:
                        st.error("請至少保留一項督勤重點！")
                    else:
                        db.query(InspectionFocusItem).delete()
                        for l in lines:
                            cat_val = "常態督勤"
                            clean_l = l
                            if "[" in l and "]" in l:
                                try:
                                    cat_val = l.split("[")[1].split("]")[0]
                                    clean_l = l.split("]")[1].strip()
                                except Exception:
                                    pass
                            
                            clean_l = clean_l.lstrip("0123456789.、: -")
                            item_obj = InspectionFocusItem(
                                category=cat_val,
                                item_name=clean_l if clean_l else l,
                                description="",
                                is_active=True
                            )
                            db.add(item_obj)
                        db.commit()
                        st.success("🎉 督導重點清單已成功更新！現場填報表單已即時同步！")
                        st.rerun()

            # ── 單筆快速新增區塊 ──
            with st.expander("➕ 單筆快速新增個別督導重點項目", expanded=False):
                with st.form("add_single_focus_form", clear_on_submit=True):
                    a_c1, a_c2 = st.columns([1.2, 2.8])
                    with a_c1:
                        add_cat = st.selectbox("重點類別", ["義消專長資料庫", "訓練與出勤紀錄", "補助款規定熟悉度", "訓練安全管理", "義消推動制度了解", "常態督勤", "其他專案"])
                    with a_c2:
                        add_name = st.text_input("督導重點項目名稱 *", placeholder="例：抽查本月義消定期訓練及出勤紀錄是否核實")
                    
                    if st.form_submit_button("➕ 加入重點項目清單", type="primary", use_container_width=True):
                        if not add_name.strip():
                            st.error("請輸入項目名稱！")
                        else:
                            item_obj = InspectionFocusItem(
                                category=add_cat,
                                item_name=add_name.strip(),
                                description="",
                                is_active=True
                            )
                            db.add(item_obj)
                            db.commit()
                            st.success(f"🎉 已成功新增【{add_cat}】{add_name.strip()}！")
                            st.rerun()

            st.markdown("---")

            # ── 區塊 2：各督導項目的現場狀況說明下拉選單選項維護 ──
            st.markdown("#### 📝 2. 自訂各重點項目的「現場狀況說明下拉選單選項」")
            st.caption("直接選擇重點項目，編輯其下拉選單中的常用狀況句子（每行代表一個下拉選單選項）：")
            
            curr_presets = load_preset_notes()
            preset_keys = list(curr_presets.keys())
            
            p_c1, p_c2 = st.columns([1.2, 2.8])
            with p_c1:
                sel_preset_cat = st.selectbox("選擇要維護選項的重點項目：", preset_keys, key="edit_preset_cat_sel")
                new_custom_cat = st.text_input("➕ 或新增重點項目類別名稱：", placeholder="例：新制宣導事項", key="new_preset_cat_inp")
                if st.button("➕ 新增此類別選項庫", use_container_width=True):
                    if new_custom_cat.strip() and new_custom_cat.strip() not in curr_presets:
                        curr_presets[new_custom_cat.strip()] = ["現場查核符合規範，運作良好。"]
                        save_preset_notes(curr_presets)
                        st.success(f"已新增【{new_custom_cat.strip()}】狀況選項庫！")
                        st.rerun()

            with p_c2:
                target_cat = sel_preset_cat
                existing_lines = "\n".join(curr_presets.get(target_cat, []))
                edited_lines = st.text_area(
                    f"【{target_cat}】下拉選單選項清單 (每行代表一個選項)：",
                    value=existing_lines,
                    height=180,
                    key=f"preset_lines_area_{target_cat}"
                )
                
                col_btn_p1, col_btn_p2 = st.columns([1.2, 1])
                with col_btn_p1:
                    if st.button("💾 儲存並更新此項目狀況選項", type="primary", use_container_width=True, key="save_preset_notes_btn"):
                        new_list = [line.strip() for line in edited_lines.split("\n") if line.strip()]
                        if not new_list:
                            new_list = ["查核良好，運作正常。"]
                        curr_presets[target_cat] = new_list
                        save_preset_notes(curr_presets)
                        st.success(f"🎉 已成功更新【{target_cat}】下拉選單選項（共 {len(new_list)} 項）！現場填報表單已即時同步！")
                        st.rerun()
                with col_btn_p2:
                    if st.button("🔄 重置為預設公版選項", use_container_width=True, key="reset_preset_notes_btn"):
                        from config import DEFAULT_ITEM_PRESET_NOTES
                        if target_cat in DEFAULT_ITEM_PRESET_NOTES:
                            curr_presets[target_cat] = list(DEFAULT_ITEM_PRESET_NOTES[target_cat])
                            save_preset_notes(curr_presets)
                            st.info(f"已重置【{target_cat}】為預設公版選項！")
                            st.rerun()

        # ==========================================
        # TAB 4: 歷史督勤檔案庫 (實體儲存檔案查詢)
        # ==========================================
        with tab_history:
            st.subheader("📁 歷史督勤紀錄與實體檔案庫")
            
            st.markdown(
                f"""
                <div style="background: #f8fafc; border-left: 4px solid #0284c7; padding: 10px 14px; border-radius: 6px; font-size: 0.9rem; color: #0369a1; margin-bottom: 1rem;">
                    📂 <b>報告儲存實體路徑</b>：<code>{REPORTS_DIR}</code><br>
                    所有督勤紀錄皆已永久存入資料庫，可依受督單位或同仁篩選，並隨時重新下載 Word 檔。
                </div>
                """,
                unsafe_allow_html=True
            )
            
            h_f1, h_f2 = st.columns([1, 1])
            with h_f1:
                hist_unit = st.selectbox("依受督單位篩選", ["全部單位"] + [u.unit_name for u in units])
            with h_f2:
                hist_inspector = st.selectbox("依督勤同仁篩選", ["全部人員"] + sorted(list(set([i.inspector for i in all_inspections]))))

            filtered_insps = all_inspections
            if hist_unit != "全部單位":
                filtered_insps = [i for i in filtered_insps if i.target_unit == hist_unit]
            if hist_inspector != "全部人員":
                filtered_insps = [i for i in filtered_insps if i.inspector == hist_inspector]

            st.write(f"共查詢到 **{len(filtered_insps)}** 筆歷史督勤紀錄：")

            for insp in filtered_insps:
                m_txt = getattr(insp, 'merit_status', '口頭嘉勉') or '口頭嘉勉'
                dm_txt = getattr(insp, 'demerit_status', '無重大缺失') or '無重大缺失'
                
                with st.expander(f"📌 {insp.inspect_date.strftime('%Y-%m-%d')} ｜ 【{insp.target_unit}】 ｜ 督勤員：{insp.inspector} ｜ 處置：🌟 {m_txt} / ⚠️ {dm_txt}"):
                    st.markdown(f"**督勤日期：** {insp.inspect_date.strftime('%Y-%m-%d')} ｜ **督勤同仁：** {insp.inspector}")
                    st.markdown(f"**綜合處置判定：** 🌟 優良考評：`{m_txt}` ｜ ⚠️ 缺失要求：`{dm_txt}`")
                    
                    # 解析 focus_items
                    items_list = []
                    if insp.focus_items:
                        try:
                            items_list = json.loads(insp.focus_items)
                        except Exception:
                            items_list = []

                    if items_list:
                        st.markdown("**🔍 督導重點事項勾選與查核紀錄：**")
                        for it in items_list:
                            name = it.get("name", "")
                            res = it.get("result", "")
                            note = it.get("note", "")
                            cat = it.get("category", "")
                            cat_label = f"[{cat}] " if cat and cat != '常態督勤' else ""
                            st.markdown(f"- **{cat_label}{name}**：`{res}` ｜ {note}")

                    if insp.strengths:
                        st.markdown(f"**🌟 現場優良事蹟（處置：【{m_txt}】）：**\n{insp.strengths}")
                    if insp.deficiencies:
                        st.markdown(f"**⚠️ 缺失改善要求（處置：【{dm_txt}】）：**\n{insp.deficiencies}")

                    # 操作按鈕群
                    col_b1, col_b2, col_b3 = st.columns([1.2, 1.2, 1])
                    with col_b1:
                        # 重新生成 Word 檔案下載
                        h_buf = generate_inspection_docx(
                            unit_name=insp.target_unit,
                            inspect_date=insp.inspect_date.strftime('%Y-%m-%d'),
                            inspector=insp.inspector,
                            focus_items=items_list,
                            strengths=insp.strengths or "",
                            deficiencies=insp.deficiencies or "",
                            merit_status=m_txt,
                            demerit_status=dm_txt,
                            report_text=insp.report_text or ""
                        )
                    # 操作按鈕列
                    col_b1, col_b2, col_b3 = st.columns([1.5, 1.2, 1.2])
                    with col_b1:
                        # 重新生成 Word 檔案下載
                        h_buf = generate_inspection_docx(
                            unit_name=insp.target_unit,
                            inspect_date=insp.inspect_date.strftime('%Y-%m-%d'),
                            inspector=insp.inspector,
                            focus_items=items_list,
                            strengths=insp.strengths or "",
                            deficiencies=insp.deficiencies or "",
                            merit_status=m_txt,
                            demerit_status=dm_txt,
                            report_text=insp.report_text or ""
                        )
                        st.download_button(
                            label="📥 下載 Word 報告",
                            data=h_buf,
                            file_name=f"臺東縣消防局督勤報告_{insp.target_unit}_{insp.inspect_date.strftime('%Y%m%d')}_{insp.id}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"dl_hist_{insp.id}",
                            use_container_width=True
                        )

                    with col_b2:
                        show_edit_form = st.checkbox("✏️ 編輯此筆紀錄", key=f"toggle_edit_{insp.id}")

                    with col_b3:
                        show_delete_confirm = st.checkbox("🗑️ 刪除此筆紀錄", key=f"toggle_del_{insp.id}")

                    # ── 區塊 B：刪除確認對話卡片（直接顯示，絕不被收合擋住） ──
                    if show_delete_confirm:
                        st.markdown(
                            f"""
                            <div style="background: #fef2f2; border: 1.5px solid #f87171; border-left: 5px solid #dc2626; border-radius: 6px; padding: 10px 14px; margin: 10px 0;">
                                <b style="color: #991b1b;">⚠️ 請確認是否要永久刪除【{insp.target_unit}】於 {insp.inspect_date.strftime('%Y-%m-%d')} 的督勤紀錄？</b><br>
                                <span style="font-size: 0.85rem; color: #7f1d1d;">此操作將從資料庫中永久抹除該紀錄，無法復原。</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        c_del_btn1, c_del_btn2 = st.columns([1.5, 3])
                        with c_del_btn1:
                            if st.button("❌ 確認永久刪除", type="primary", key=f"confirm_delete_btn_{insp.id}", use_container_width=True):
                                item_to_remove = db.query(Inspection).filter(Inspection.id == insp.id).first()
                                if item_to_remove:
                                    db.delete(item_to_remove)
                                    db.commit()
                                    st.success(f"🎉 已成功刪除【{insp.target_unit}】的督勤紀錄！")
                                    st.rerun()

                    # ── 區塊 A：編輯修改督勤紀錄表單 ──
                    if show_edit_form:
                        st.markdown("---")
                        with st.form(f"edit_insp_form_{insp.id}"):
                            st.markdown(f"#### ✏️ 編輯【{insp.target_unit}】督勤紀錄")
                            st.markdown("##### 🏢 基本資訊修改")
                            ec1, ec2, ec3 = st.columns(3)
                            with ec1:
                                all_unit_names = [u.unit_name for u in units]
                                u_idx = all_unit_names.index(insp.target_unit) if insp.target_unit in all_unit_names else 0
                                edit_unit = st.selectbox("受督導單位", all_unit_names, index=u_idx, key=f"eu_{insp.id}")
                            with ec2:
                                edit_date = st.date_input("督勤日期", value=insp.inspect_date, key=f"ed_{insp.id}")
                            with ec3:
                                edit_inspector = st.text_input("督勤人員", value=insp.inspector, key=f"eins_{insp.id}")

                            st.markdown("##### ⚖️ 處置判定修改")
                            em1, em2 = st.columns(2)
                            with em1:
                                merit_opts = ["口頭嘉勉", "優績", "符合良好"]
                                m_idx = merit_opts.index(m_txt) if m_txt in merit_opts else 0
                                edit_merit = st.selectbox("優良處置判定", merit_opts, index=m_idx, key=f"em_{insp.id}")
                            with em2:
                                demerit_opts = ["無重大缺失事項", "請主管立即改善", "劣蹟註記"]
                                dm_idx = demerit_opts.index(dm_txt) if dm_txt in demerit_opts else 0
                                edit_demerit = st.selectbox("缺失處置判定", demerit_opts, index=dm_idx, key=f"edm_{insp.id}")

                            st.markdown("##### 🔍 查核項目與現場狀況修改")
                            edited_items = []
                            for it_i, it_obj in enumerate(items_list):
                                st.write(f"**項目 {it_i+1}：{it_obj.get('name', '查核項目')}**")
                                c_er, c_en = st.columns([1, 2.5])
                                with c_er:
                                    res_options = ["☑ 符合規範", "☒ 待改善", "ℹ 宣導提醒", "➖ 不適用"]
                                    cur_res = it_obj.get('result', '☑ 符合規範')
                                    clean_cur_res = cur_res.split(" / ")[0]
                                    matching_res_idx = next((ri for ri, ro in enumerate(res_options) if clean_cur_res in ro), 0)
                                    e_res = st.selectbox("結果", res_options, index=matching_res_idx, key=f"eres_{insp.id}_{it_i}")
                                with c_en:
                                    e_note = st.text_input("狀況說明", value=it_obj.get('note', ''), key=f"enote_{insp.id}_{it_i}")
                                
                                edited_items.append({
                                    "category": it_obj.get("category", "重點"),
                                    "name": it_obj.get("name", ""),
                                    "result": e_res.split(" / ")[0],
                                    "note": e_note.strip() if e_note.strip() else "查核良好"
                                })

                            st.markdown("##### 📝 補充說明與改善要求")
                            edit_str = st.text_area("補充優良說明", value=insp.strengths or "", height=70, key=f"estr_{insp.id}")
                            edit_def = st.text_area("改善要求說明", value=insp.deficiencies or "", height=70, key=f"edef_{insp.id}")

                            if st.form_submit_button("💾 儲存修改並更新報告", type="primary", use_container_width=True):
                                # 重新合成 Markdown 報告
                                good_items_e = []
                                defect_items_e = []
                                for it_e in edited_items:
                                    res_val_e = it_e['result']
                                    if any(k in res_val_e for k in ["待改善", "需追蹤", "缺失", "不符", "☒"]):
                                        ds = synthesize_defect_sentence(it_e)
                                        if ds:
                                            defect_items_e.append(f"{len(defect_items_e)+1}. {ds}")
                                    else:
                                        gs = synthesize_inspection_sentence(it_e)
                                        if gs:
                                            good_items_e.append(f"{len(good_items_e)+1}. {gs}")

                                m_phrase = {"口頭嘉勉": "給予口頭嘉勉", "優績": "給予優績", "符合良好": "符合良好"}.get(edit_merit, f"給予{edit_merit}")
                                dm_phrase = {"劣蹟註記": "給予劣蹟註記", "請主管立即改善": "請主管立即改善", "無重大缺失事項": "無重大缺失事項"}.get(edit_demerit, f"給予{edit_demerit}")

                                sec2_p = []
                                if good_items_e:
                                    sec2_p.extend(good_items_e)
                                else:
                                    sec2_p.append("現場各項常態業務查核運作良好。")
                                if edit_str.strip():
                                    sec2_p.append(f"\n**【補充說明】**：\n{edit_str.strip()}")
                                sec2_p.append(f"\n📌 **總結處置**：現場整體運作良好，**{m_phrase}**。")
                                sec2_text = "\n".join(sec2_p)

                                sec3_p = []
                                if defect_items_e:
                                    sec3_p.extend(defect_items_e)
                                if edit_def.strip():
                                    sec3_p.append(f"\n**【改善要求】**：\n{edit_def.strip()}")
                                if sec3_p or edit_demerit in ["劣蹟註記", "請主管立即改善"]:
                                    if not sec3_p:
                                        sec3_p.append("現場查有待改善事項，列管督導。")
                                    sec3_p.append(f"\n⚠️ **處置要求**：現場查核缺失事項列管追蹤，**{dm_phrase}**。")
                                    sec3_text = "\n".join(sec3_p)
                                else:
                                    sec3_text = "經現場各項重點查核，本次督勤無重大缺失事項。"

                                new_report_md = f"""# 臺東縣消防局民力科 督勤與業務查核紀錄表

- **受督導單位**：{edit_unit}
- **督勤日期**：{edit_date.strftime('%Y-%m-%d')}
- **督勤人員**：{edit_inspector}
- **綜合督勤處置**：🌟 【優良處置】：`{edit_merit}` ｜ ⚠️ 【缺失處置】：`{edit_demerit}`

---

### 一、 督導重點事項查核與宣導紀要
"""
                                for idx_e, it_e in enumerate(edited_items, 1):
                                    cat_l = f"[{it_e.get('category', '重點')}] " if it_e.get('category') != '常態督勤' else ""
                                    new_report_md += f"{idx_e}. **{cat_l}{it_e['name']}**\n   - 查核結果：`{it_e['result']}` ｜ 現場狀況：{it_e['note']}\n"

                                new_report_md += f"""
---

### 二、 督導所見事項彙整（處置判定：【{edit_merit}】）
{sec2_text}

---

### 三、 督導缺失事項與處置要求（處置判定：【{edit_demerit}】）
{sec3_text}

---
*督勤同仁簽章：{edit_inspector}　　受督單位主管簽章：___________　　科長核閱：___________*
"""

                                # 更新資料庫物件
                                insp.target_unit = edit_unit
                                insp.inspect_date = edit_date
                                insp.inspector = edit_inspector
                                insp.merit_status = edit_merit
                                insp.demerit_status = edit_demerit
                                insp.focus_items = json.dumps(edited_items, ensure_ascii=False)
                                insp.strengths = edit_str.strip()
                                insp.deficiencies = edit_def.strip()
                                insp.report_text = new_report_md
                                db.commit()
                                st.success(f"🎉 已成功更新【{edit_unit}】的督勤紀錄與報告！")
                                st.rerun()

    finally:
        db.close()
