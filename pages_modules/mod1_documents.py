"""
模組一：重要計畫及公文續辦管理看板
專注於重要業務計畫、專案列管與需續辦公文之重點擷取、執行時限推算與「目前辦理狀況」即時追蹤
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db, Document, User
from config import (
    PLAN_DOC_TYPE_OPTIONS,
    DOC_STATUS_OPTIONS,
    DOC_PRIORITY_OPTIONS,
    DOC_CATEGORY_OPTIONS,
    QUICK_PROGRESS_PRESETS
)
from ai_helper import (
    extract_doc_followup_from_text,
    extract_doc_followup_from_image,
    get_gemini_api_key
)
from export_helper import generate_documents_csv

def render_documents_module():
    st.markdown(
        """
        <div class="main-header">
            <h1>📑 模組一：重要計畫及公文續辦管理看板</h1>
            <p>重要業務計畫、專案列管與重點公文續辦 ➔ AI 智能擷取關鍵重點與時限 ➔「目前辦理狀況」即時動態追蹤</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    db = get_db()
    try:
        today = date.today()

        # 讀取資料庫中所有列管計畫與公文
        docs = db.query(Document).order_by(Document.deadline.asc()).all()

        # 計算統計指標
        total_count = len(docs)
        active_docs = [d for d in docs if d.status not in ["已辦結", "已結案", "已辦結 / 已完成"]]
        completed_count = total_count - len(active_docs)
        
        plan_count = len([d for d in docs if getattr(d, 'item_type', '') in ["重要業務計畫", "專案列管計畫", "演訓專案", "採購專案"]])
        doc_count = total_count - plan_count

        urgent_count = 0   # < 3 天或已逾期
        warning_count = 0  # 3 ~ 6 天
        normal_count = 0   # >= 7 天

        for d in active_docs:
            days_left = (d.deadline - today).days
            if days_left < 3:
                urgent_count += 1
            elif days_left < 7:
                warning_count += 1
            else:
                normal_count += 1

        # 頂部 KPI 卡片
        kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
        with kpi_col1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">總列管件數</div>
                    <div class="kpi-value" style="color: #1e293b;">{total_count} <span style="font-size: 0.85rem; color: #64748b;">(計畫 {plan_count} / 公文 {doc_count})</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with kpi_col2:
            st.markdown(
                f"""
                <div class="kpi-card" style="border-top: 3px solid #ef4444;">
                    <div class="kpi-title" style="color: #b91c1c;">🚨 緊迫/逾期 (&lt;3天)</div>
                    <div class="kpi-value" style="color: #dc2626;">{urgent_count}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with kpi_col3:
            st.markdown(
                f"""
                <div class="kpi-card" style="border-top: 3px solid #f59e0b;">
                    <div class="kpi-title" style="color: #b45309;">⚠️ 即將到期 (&lt;7天)</div>
                    <div class="kpi-value" style="color: #d97706;">{warning_count}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with kpi_col4:
            st.markdown(
                f"""
                <div class="kpi-card" style="border-top: 3px solid #3b82f6;">
                    <div class="kpi-title" style="color: #1d4ed8;">⏳ 辦理/執行中</div>
                    <div class="kpi-value" style="color: #2563eb;">{len(active_docs)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with kpi_col5:
            st.markdown(
                f"""
                <div class="kpi-card" style="border-top: 3px solid #10b981;">
                    <div class="kpi-title" style="color: #15803d;">✅ 已辦結/已完成</div>
                    <div class="kpi-value" style="color: #16a34a;">{completed_count}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        # 功能分頁
        tab_ai_extract, tab_list, tab_manual = st.tabs([
            "🤖 AI 貼文 / 截圖智能擷取 (計畫/公文/簽呈/專案要點)",
            "📋 重要計畫及公文續辦追蹤看板 (含目前辦理狀況)",
            "✍️ 傳統手動快速填報"
        ])

        # ==========================================
        # TAB 1: AI 貼文 / 截圖智能擷取
        # ==========================================
        with tab_ai_extract:
            st.subheader("🤖 重要計畫與公文續辦 AI 智能擷取助手")
            st.markdown(
                """
                <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 10px 14px; border-radius: 6px; font-size: 0.9rem; color: #334155; margin-bottom: 1rem;">
                    💡 <b>功能特色</b>：支援收錄<b>「重要業務計畫、專案演訓、採購列管」</b>與<b>「需續辦之重點公文」</b>。貼上內文或上傳截圖，AI 將自動辨識<b>項目類型、字號/編號、案由、主辦機關、推算執行時限</b>，並自動初擬<b>「目前辦理狀況」</b>與<b>「具體應辦步驟清單」</b>！
                </div>
                """,
                unsafe_allow_html=True
            )

            input_type = st.radio("選擇輸入方式", ["📝 貼上文字 (計畫書摘要、公文全文、簽呈或會議要點)", "🖼️ 上傳截圖 / 簽呈照片 / 專案簡報 (JPG / PNG / WEBP)"], horizontal=True)

            if "貼上文字" in input_type:
                pasted_text = st.text_area(
                    "請在此貼上重要計畫或公文內容：",
                    height=200,
                    placeholder="例：\n【113年度義勇消防人員常年訓練與救災安全考核實施計畫】\n一、計畫目的：提升本市義勇消防同仁救災技能與火場安全防護...\n二、主辦單位：內政部消防署 / 本局民力科。\n三、實施期程：請於本月底前完成開訓簽陳，各梯次訓練於10月15日前完竣。\n四、目前辦理狀況：各義消大隊名冊已送達初審，簽呈刻正陳核副局長室..."
                )

                if st.button("✨ 啟動 AI 智能擷取計畫重點、時限與辦理狀況", type="primary", use_container_width=True):
                    if not pasted_text.strip():
                        st.error("請先貼上文字內容！")
                    else:
                        with st.spinner("🤖 Gemini 正在深度分析計畫與公文條款、推算執行時限並條列應辦步驟中..."):
                            extracted_res = extract_doc_followup_from_text(pasted_text)
                            st.session_state["doc_extracted_data"] = extracted_res
                            st.session_state["doc_raw_input"] = pasted_text
                            st.rerun()

            else:
                uploaded_doc_img = st.file_uploader("選擇或拖曳計畫書截圖 / 簽呈照片 / 公文截圖", type=["png", "jpg", "jpeg", "webp"])
                if uploaded_doc_img is not None:
                    col_img_prev, col_img_btn = st.columns([1, 1.5])
                    with col_img_prev:
                        st.image(uploaded_doc_img, caption="截圖預覽", use_container_width=True)
                    with col_img_btn:
                        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                        if st.button("✨ 啟動 Gemini Vision 截圖 OCR 辨識與計畫擷取", type="primary", use_container_width=True):
                            with st.spinner("🤖 Gemini Vision 正在 OCR 掃描截圖並提取計畫重點、時限與辦理狀況..."):
                                extracted_res = extract_doc_followup_from_image(uploaded_doc_img)
                                st.session_state["doc_extracted_data"] = extracted_res
                                st.session_state["doc_raw_input"] = "[來自截圖辨識]"
                                st.rerun()

            # 顯示 AI 擷取成果與確認存檔表單
            if "doc_extracted_data" in st.session_state and st.session_state["doc_extracted_data"]:
                ext = st.session_state["doc_extracted_data"]
                st.markdown("---")
                st.success("🎉 **AI 已成功擷取重要計畫/公文之核心重點！請核對並確認存入追蹤看板：**")

                with st.form("confirm_doc_form"):
                    c_type_col1, c_type_col2 = st.columns(2)
                    with c_type_col1:
                        def_type = ext.get("item_type", "重要業務計畫")
                        type_options = ["重要業務計畫", "公文續辦", "專案列管計畫", "演訓專案", "採購專案"]
                        type_idx = type_options.index(def_type) if def_type in type_options else 0
                        f_item_type = st.selectbox("項目類型 *", type_options, index=type_idx)
                        f_doc_num = st.text_input("字號 / 計畫編號 *", value=ext.get("doc_number", ""))
                        f_issuing = st.text_input("來文機關 / 主辦科室", value=ext.get("issuing_unit", "內政部消防署 / 本局民力科"))
                    with c_type_col2:
                        try:
                            def_deadline = datetime.strptime(ext.get("deadline", ""), "%Y-%m-%d").date()
                        except Exception:
                            def_deadline = today + timedelta(days=7)
                        
                        f_deadline = st.date_input("執行/完成期限 * (AI 依條款自動推算)", value=def_deadline)
                        f_deadline_desc = st.text_input("時限依據條款 / 里程碑說明", value=ext.get("deadline_desc", "依計畫時程推動"))
                        
                        c_sub1, c_sub2 = st.columns(2)
                        with c_sub1:
                            def_prio = ext.get("priority", "速件")
                            prio_idx = DOC_PRIORITY_OPTIONS.index(def_prio) if def_prio in DOC_PRIORITY_OPTIONS else 1
                            f_priority = st.selectbox("急迫等級", DOC_PRIORITY_OPTIONS, index=prio_idx)
                        with c_sub2:
                            def_cat = ext.get("category", "演訓與常年訓練")
                            cat_idx = DOC_CATEGORY_OPTIONS.index(def_cat) if def_cat in DOC_CATEGORY_OPTIONS else 0
                            f_category = st.selectbox("業務類別", DOC_CATEGORY_OPTIONS, index=cat_idx)

                    f_subject = st.text_area("計畫名稱 / 公文案由主旨 *", value=ext.get("subject", ""), height=70)

                    # 🌟 核心新增欄位：目前辦理狀況
                    st.markdown("#### 📌 【目前辦理狀況】 (最關鍵動態追蹤欄位)")
                    f_current_progress = st.text_input(
                        "目前最新辦理狀況說明 *",
                        value=ext.get("current_progress", "簽呈陳核中，正辦理名冊彙整與前置作業"),
                        placeholder="例：簽呈陳核至副局長室、名冊初審完竣、招標規格需求研商中..."
                    )

                    st.markdown("#### 📋 具體續辦 / 實施步驟清單 (Action Checklist)")
                    f_actions = st.text_area(
                        "應辦步驟與檢核事項",
                        value=ext.get("followup_actions", "1. 檢視本案各階段里程碑。\n2. 簽擬具體實施意見陳核長官。\n3. 發文各大隊配合辦理或依限函報。"),
                        height=100
                    )

                    c_as1, c_as2 = st.columns(2)
                    with c_as1:
                        f_assignee = st.text_input("負責承辦人/主責同仁 *", value=ext.get("assignee", "陳科員"))
                    with c_as2:
                        f_status = st.selectbox("起始狀態", ["待續辦", "辦理中", "已辦結"], index=1)

                    f_notes = st.text_input("補充備註 (選填)", value=ext.get("key_summary", ""))

                    btn_confirm_save = st.form_submit_button("💾 確認存入重要計畫及公文續辦看板", type="primary", use_container_width=True)

                    if btn_confirm_save:
                        if not f_doc_num or not f_subject or not f_assignee:
                            st.error("請確認字號/編號、名稱主旨與承辦人欄位！")
                        else:
                            new_followup_doc = Document(
                                item_type=f_item_type,
                                doc_number=f_doc_num.strip(),
                                subject=f_subject.strip(),
                                deadline=f_deadline,
                                deadline_desc=f_deadline_desc.strip(),
                                issuing_unit=f_issuing.strip(),
                                assignee=f_assignee.strip(),
                                priority=f_priority,
                                category=f_category,
                                status=f_status,
                                current_progress=f_current_progress.strip(),
                                followup_actions=f_actions.strip(),
                                notes=f_notes.strip(),
                                raw_content=st.session_state.get("doc_raw_input", "")
                            )
                            db.add(new_followup_doc)
                            db.commit()
                            st.session_state["doc_extracted_data"] = None
                            st.success(f"🎉 【{f_item_type}】{f_doc_num} 已成功存入列管追蹤看板！")
                            st.rerun()

        # ==========================================
        # TAB 2: 重要計畫及公文續辦追蹤看板
        # ==========================================
        with tab_list:
            st.subheader("📋 重要計畫及公文續辦動態追蹤看板")

            # 篩選工具列
            f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([1.1, 1.1, 1.1, 1.1, 1.6])
            
            all_assignees = sorted(list(set([d.assignee for d in docs if d.assignee])))
            with f_c1:
                sel_type = st.selectbox("項目類型篩選", PLAN_DOC_TYPE_OPTIONS, index=0)
            with f_c2:
                sel_status = st.selectbox("狀態篩選", ["全部", "未結案 (待續辦/辦理中)", "待續辦", "辦理中", "已辦結"], index=1)
            with f_c3:
                sel_assignee = st.selectbox("負責人篩選", ["全部人員"] + all_assignees)
            with f_c4:
                sel_category = st.selectbox("業務類別", ["全部類別"] + DOC_CATEGORY_OPTIONS)
            with f_c5:
                search_query = st.text_input("🔍 關鍵字搜尋", placeholder="搜尋字號/主旨/辦理狀況/單位...")

            # 資料過濾
            filtered_docs = docs
            if sel_type != "全部類型":
                filtered_docs = [d for d in filtered_docs if getattr(d, 'item_type', '公文續辦') == sel_type]

            if sel_status == "未結案 (待續辦/辦理中)":
                filtered_docs = [d for d in filtered_docs if d.status not in ["已辦結", "已結案"]]
            elif sel_status != "全部":
                filtered_docs = [d for d in filtered_docs if d.status == sel_status or (sel_status == "已辦結" and d.status == "已結案")]
            
            if sel_assignee != "全部人員":
                filtered_docs = [d for d in filtered_docs if d.assignee == sel_assignee]
                
            if sel_category != "全部類別":
                filtered_docs = [d for d in filtered_docs if d.category == sel_category]
                
            if search_query:
                q = search_query.lower()
                filtered_docs = [
                    d for d in filtered_docs 
                    if q in d.doc_number.lower() or q in d.subject.lower() or 
                    (getattr(d, 'current_progress', '') and q in d.current_progress.lower()) or
                    (d.notes and q in d.notes.lower()) or 
                    (d.issuing_unit and q in d.issuing_unit.lower()) or
                    (d.followup_actions and q in d.followup_actions.lower())
                ]

            # 檢視切換與匯出
            tool_col1, tool_col2 = st.columns([1, 1])
            with tool_col1:
                view_mode = st.radio("檢視模式", ["📱 完整列管卡片視圖 (含目前辦理狀況與應辦清單)", "💻 簡明管理總表"], horizontal=True)
            with tool_col2:
                csv_data = generate_documents_csv(filtered_docs)
                st.download_button(
                    label="📥 匯出計畫與公文列管清單 (Excel / CSV)",
                    data=csv_data.encode("utf-8-sig"),
                    file_name=f"民力科重要計畫及公文列管清單_{today.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            st.markdown(f"<p style='color: #64748b; font-size: 0.9rem;'>共列管 <b>{len(filtered_docs)}</b> 筆重要案件（按期限倒數自動排序）：</p>", unsafe_allow_html=True)

            if not filtered_docs:
                st.info("💡 目前無符合條件之計畫或公文。歡迎至第一分頁貼上內容或截圖快速收錄！")

            # 渲染卡片模式
            if "完整列管卡片" in view_mode:
                for d in filtered_docs:
                    days_left = (d.deadline - today).days
                    is_completed = (d.status in ["已辦結", "已結案"])
                    item_type_val = getattr(d, 'item_type', '公文續辦') or '公文續辦'
                    
                    if is_completed:
                        card_class = "completed"
                        badge_html = '<span class="badge badge-success">✅ 已辦結</span>'
                        time_text = f"期限：{d.deadline.strftime('%Y-%m-%d')}"
                    elif days_left < 0:
                        card_class = "urgent"
                        badge_html = f'<span class="badge badge-urgent">🚨 逾期 {-days_left} 天</span>'
                        time_text = f"<span style='color: #dc2626; font-weight: bold;'>期限：{d.deadline.strftime('%Y-%m-%d')} (已逾期)</span>"
                    elif days_left < 3:
                        card_class = "urgent"
                        badge_html = f'<span class="badge badge-urgent">🚨 剩餘 {days_left} 天 (急件)</span>'
                        time_text = f"<span style='color: #dc2626; font-weight: bold;'>期限：{d.deadline.strftime('%Y-%m-%d')} (剩 {days_left} 天)</span>"
                    elif days_left < 7:
                        card_class = "warning"
                        badge_html = f'<span class="badge badge-warning">⚠️ 剩餘 {days_left} 天 (提醒)</span>'
                        time_text = f"<span style='color: #d97706; font-weight: bold;'>期限：{d.deadline.strftime('%Y-%m-%d')} (剩 {days_left} 天)</span>"
                    else:
                        card_class = ""
                        badge_html = f'<span class="badge badge-info">⏳ 剩餘 {days_left} 天</span>'
                        time_text = f"期限：{d.deadline.strftime('%Y-%m-%d')} (剩 {days_left} 天)"

                    # 類型標籤顏色
                    type_tag_color = "#1e40af" if "計畫" in item_type_val else "#0f766e"
                    type_tag_bg = "#dbeafe" if "計畫" in item_type_val else "#ccfbf1"

                    with st.container(border=True):
                        c_header1, c_header2 = st.columns([3.5, 1.5])
                        with c_header1:
                            issuing_txt = getattr(d, 'issuing_unit', '') or '消防署 / 本局民力科'
                            st.markdown(
                                f"""
                                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
                                    <span style="background: {type_tag_bg}; color: {type_tag_color}; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">
                                        📌 {item_type_val}
                                    </span>
                                    <span style="font-weight: 600; color: #1e3a8a; font-size: 0.95rem;">
                                        {d.doc_number}
                                    </span>
                                    <span style="color: #64748b; font-size: 0.85rem;">
                                        🏢 {issuing_txt} ｜ 🏷️ {d.category}
                                    </span>
                                </div>
                                <div style="font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 6px;">
                                    {d.subject}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        with c_header2:
                            st.markdown(f"<div style='text-align: right;'>{badge_html}</div>", unsafe_allow_html=True)

                        # 🌟 核心高亮展示：【目前辦理狀況】橫幅
                        cur_prog = getattr(d, 'current_progress', '') or d.notes or '刻正依計畫推動中'
                        st.markdown(
                            f"""
                            <div style="background: #eff6ff; border: 1.5px solid #bfdbfe; border-left: 5px solid #2563eb; border-radius: 8px; padding: 10px 14px; margin: 6px 0 10px 0;">
                                <div style="font-size: 0.85rem; font-weight: 700; color: #1e40af; margin-bottom: 2px;">
                                    🚀 【目前辦理狀況】：
                                </div>
                                <div style="font-size: 1.05rem; font-weight: 600; color: #1e293b;">
                                    {cur_prog}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # 時限與承辦資訊
                        col_m1, col_m2 = st.columns([1.5, 2])
                        with col_m1:
                            st.markdown(f"👤 <b>主責同仁：</b> {d.assignee} ｜ 🏷️ <b>急迫等級：</b> {d.priority}", unsafe_allow_html=True)
                            st.markdown(f"📅 {time_text}", unsafe_allow_html=True)
                        with col_m2:
                            deadline_desc_txt = getattr(d, 'deadline_desc', '') or '依時限辦結'
                            st.markdown(f"⚖️ <b>時限依據/里程碑：</b> <span style='color: #b45309;'>{deadline_desc_txt}</span>", unsafe_allow_html=True)
                            st.markdown(f"📌 <b>管制狀態：</b> <b>{d.status}</b>", unsafe_allow_html=True)

                        # 應辦事項清單
                        followup_txt = getattr(d, 'followup_actions', '')
                        if followup_txt:
                            st.markdown(
                                f"""
                                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; margin-top: 6px; font-size: 0.9rem;">
                                    <div style="font-weight: 600; color: #475569; margin-bottom: 2px;">📋 續辦/實施步驟與應辦清單：</div>
                                    <div style="color: #334155; white-space: pre-line;">{followup_txt}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # 快速更新【目前辦理狀況】區塊
                        with st.expander(f"✏️ 快速更新「目前辦理狀況」與狀態 (編號: {d.doc_number})", expanded=False):
                            u_col1, u_col2 = st.columns([1, 2])
                            with u_col1:
                                current_stat = d.status if d.status in ["待續辦", "辦理中", "已辦結"] else "辦理中"
                                new_st = st.selectbox(
                                    "變更管制狀態", 
                                    ["待續辦", "辦理中", "已辦結"], 
                                    index=["待續辦", "辦理中", "已辦結"].index(current_stat),
                                    key=f"st_{d.id}"
                                )
                                quick_tag = st.selectbox(
                                    "⚡ 常用進度快捷套用",
                                    ["(手動輸入自由填寫)"] + QUICK_PROGRESS_PRESETS,
                                    key=f"qtag_{d.id}"
                                )
                            with u_col2:
                                def_prog_val = quick_tag if quick_tag != "(手動輸入自由填寫)" else (getattr(d, 'current_progress', '') or "")
                                new_prog = st.text_input(
                                    "更新【目前辦理狀況】說明 *",
                                    value=def_prog_val,
                                    key=f"prog_{d.id}",
                                    placeholder="例：簽呈陳核副局長室、名冊彙整中、規格書研擬中..."
                                )
                                new_notes = st.text_input("補充進度備註", value=d.notes or "", key=f"nt_{d.id}")

                            if st.button("💾 儲存並更新目前辦理狀況", key=f"btn_save_{d.id}", type="primary", use_container_width=True):
                                d.status = new_st
                                d.current_progress = new_prog.strip() if new_prog else "刻正辦理中"
                                d.notes = new_notes.strip()
                                d.updated_at = datetime.now()
                                db.commit()
                                st.success("✅ 辦理狀況更新成功！")
                                st.rerun()

            # 簡明表格模式
            else:
                table_rows = []
                for d in filtered_docs:
                    days_left = (d.deadline - today).days
                    if d.status in ["已辦結", "已結案"]:
                        status_display = "✅ 已辦結"
                    elif days_left < 0:
                        status_display = f"🚨 逾期 {-days_left} 天"
                    elif days_left < 3:
                        status_display = f"🚨 剩 {days_left} 天 (急)"
                    elif days_left < 7:
                        status_display = f"⚠️ 剩 {days_left} 天 (提醒)"
                    else:
                        status_display = f"⏳ 剩 {days_left} 天"

                    table_rows.append({
                        "類型": getattr(d, 'item_type', '公文續辦') or '公文續辦',
                        "時效狀態": status_display,
                        "編號/字號": d.doc_number,
                        "計畫名稱/主旨": d.subject,
                        "【目前辦理狀況】": getattr(d, 'current_progress', '') or d.notes or '刻正辦理中',
                        "執行期限": d.deadline.strftime("%Y-%m-%d"),
                        "時限依據/里程碑": getattr(d, 'deadline_desc', '') or '',
                        "負責人": d.assignee,
                        "管制狀態": d.status,
                        "來文/主辦機關": getattr(d, 'issuing_unit', '') or '',
                        "應辦步驟清單": getattr(d, 'followup_actions', '') or ''
                    })

                df = pd.DataFrame(table_rows)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "類型": st.column_config.TextColumn("類型", width="small"),
                        "時效狀態": st.column_config.TextColumn("時效狀態", width="medium"),
                        "計畫名稱/主旨": st.column_config.TextColumn("計畫名稱/主旨", width="large"),
                        "【目前辦理狀況】": st.column_config.TextColumn("【目前辦理狀況】", width="large")
                    }
                )

        # ==========================================
        # TAB 3: 傳統手動快速填報
        # ==========================================
        with tab_manual:
            st.subheader("✍️ 傳統手動快速登錄重要計畫 / 公文續辦")
            with st.form("manual_add_doc_form", clear_on_submit=True):
                m_c1, m_c2 = st.columns(2)
                with m_c1:
                    m_item_type = st.selectbox("項目類型 *", ["重要業務計畫", "公文續辦", "專案列管計畫", "演訓專案", "採購專案"])
                    m_doc_num = st.text_input("字號 / 計畫編號 *", placeholder="例：113常訓計畫-01、消署民字第113009988號")
                    m_issuing = st.text_input("來文機關 / 主辦科室", placeholder="例：內政部消防署 / 本局民力科")
                    m_assignee = st.text_input("主責承辦同仁 *", placeholder="例：陳科員、林科員")
                with m_c2:
                    m_deadline = st.date_input("執行/完成期限 *", value=today + timedelta(days=7))
                    m_deadline_desc = st.text_input("時限依據 / 里程碑說明", placeholder="例：預計9月底前開訓、文到7日內函復")
                    m_priority = st.selectbox("急迫等級", DOC_PRIORITY_OPTIONS, index=1)
                    m_category = st.selectbox("業務類別", DOC_CATEGORY_OPTIONS, index=0)
                
                m_subject = st.text_area("計畫名稱 / 公文案由主旨 *", placeholder="請輸入完整名稱或主旨...")
                
                # 目前辦理狀況
                st.markdown("##### 📌 【目前辦理狀況】")
                m_current_progress = st.text_input("目前最新辦理狀況 *", placeholder="例：簽呈陳核中、名冊彙整中、規格需求書審查中...")
                
                m_actions = st.text_area("具體續辦 / 實施步驟清單", placeholder="1. 彙整名冊\n2. 簽陳局長核定\n3. 函發各大隊配合辦理")
                m_notes = st.text_input("進度備註", placeholder="例：簽呈陳核中...")

                if st.form_submit_button("🚀 確認送出列管", type="primary", use_container_width=True):
                    if not m_doc_num or not m_subject or not m_assignee:
                        st.error("請務必填寫字號/編號、名稱主旨與承辦人！")
                    else:
                        new_m_doc = Document(
                            item_type=m_item_type,
                            doc_number=m_doc_num.strip(),
                            subject=m_subject.strip(),
                            deadline=m_deadline,
                            deadline_desc=m_deadline_desc.strip(),
                            issuing_unit=m_issuing.strip(),
                            assignee=m_assignee.strip(),
                            priority=m_priority,
                            category=m_category,
                            status="辦理中",
                            current_progress=m_current_progress.strip() if m_current_progress else "刻正辦理中",
                            followup_actions=m_actions.strip(),
                            notes=m_notes.strip()
                        )
                        db.add(new_m_doc)
                        db.commit()
                        st.success(f"🎉 【{m_item_type}】{m_doc_num} 已成功加入追蹤看板！")
                        st.rerun()

    finally:
        db.close()
