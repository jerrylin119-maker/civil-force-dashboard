"""
模組五：系統設定與資料庫管理
"""
import os
import streamlit as st
import pandas as pd
from datetime import datetime

from database import get_db, FireUnit, InspectionFocusItem, User, init_db
from ai_helper import test_gemini_connection, get_gemini_api_key
from config import DB_PATH
from git_sync_helper import run_git_sync

def render_settings_module():
    st.markdown(
        """
        <div class="main-header">
            <h1>⚙️ 模組五：系統設定與資料庫管理</h1>
            <p>Gemini API 金鑰設定、轄內單位主檔管理、督勤重點項目庫維護、GitHub 一鍵雲端同步</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_api, tab_units, tab_items, tab_db, tab_git = st.tabs([
        "🔑 Gemini API 金鑰與模型設定",
        "🏢 轄內消防/義消單位主檔管理",
        "📋 督勤重點項目庫維護",
        "💾 資料庫備份與重設",
        "🚀 一鍵同步至 GitHub 雲端"
    ])

    db = get_db()
    try:
        # ==========================================
        # TAB 1: Gemini API 金鑰與模型設定
        # ==========================================
        with tab_api:
            st.subheader("🔑 Google Gemini API 設定與金鑰配置")
            
            st.markdown(
                """
                <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 6px; font-size: 0.9rem; color: #1e293b; margin-bottom: 1rem;">
                    <b>💡 Google Gemini API Key 免費申請 3 步驟</b>：<br>
                    1. 點擊開啟 👉 <a href="https://aistudio.google.com/" target="_blank" style="color: #2563eb; font-weight: bold; text-decoration: underline;">Google AI Studio 官網 ↗</a>，以您的 Google 帳號登入。<br>
                    2. 點擊畫面左上角或右上角的 <b>「Get API key」</b> 按鈕 ➔ 選擇 <b>「Create API key」</b>。<br>
                    3. 複製產生的金鑰代碼（開頭通常為 <code>AIzaSy...</code>），貼入下方輸入框，點擊 <b>「💾 儲存並套用金鑰」</b> 即可！<br>
                    <i>（※ 系統已升級自動相容機制，會自動選取您帳號支援的最佳模型，如 Gemini 2.0 Flash / 1.5 Flash / 1.5 Pro）</i>
                </div>
                """,
                unsafe_allow_html=True
            )

            current_key = get_gemini_api_key() or ""
            masked_key = f"{current_key[:6]}...{current_key[-4:]}" if len(current_key) > 10 else current_key

            if current_key:
                st.success(f"✅ 目前已成功配置並永久儲存 API Key：`{masked_key}`")
            else:
                st.warning("⚠️ 目前尚未配置 API Key，系統正以內建智慧範本備用引擎運作。")

            with st.form("api_key_form"):
                new_key = st.text_input("輸入您的 Gemini API Key", value=current_key if current_key else "", type="password", placeholder="請貼上以 AIzaSy 開頭的金鑰代碼")
                test_conn = st.checkbox("儲存前先進行連線驗證測試", value=True)
                btn_save_key = st.form_submit_button("💾 儲存並套用金鑰", type="primary")

                if btn_save_key:
                    if not new_key.strip():
                        st.error("請輸入有效的 API Key")
                    else:
                        target_key = new_key.strip()
                        if test_conn:
                            with st.spinner("正在向 Google Gemini 伺服器進行自動相容性連線驗證中..."):
                                from ai_helper import save_gemini_api_key
                                success, resp_msg = test_gemini_connection(target_key)
                                if success:
                                    save_gemini_api_key(target_key)
                                    st.success(f"🎉 {resp_msg}，金鑰已永久儲存！")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {resp_msg}")
                        else:
                            from ai_helper import save_gemini_api_key
                            save_gemini_api_key(target_key)
                            st.success("✅ API Key 已直接儲存套用！")
                            st.rerun()

        # ==========================================
        # TAB 2: 轄內消防/義消單位主檔管理
        # ==========================================
        with tab_units:
            st.subheader("🏢 轄內消防大隊、分隊與義消單位清單")
            
            all_units = db.query(FireUnit).order_by(FireUnit.unit_type.asc(), FireUnit.district.asc()).all()
            
            u_col1, u_col2 = st.columns([1.5, 1])
            with u_col1:
                st.write(f"目前共建置 **{len(all_units)}** 個受考評單位：")
                u_data = [{"ID": u.id, "單位名稱": u.unit_name, "單位類別": u.unit_type, "轄區分區": u.district or "無", "啟用狀態": "啟用" if u.is_active else "停用"} for u in all_units]
                st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)

            with u_col2:
                with st.container(border=True):
                    st.write("##### ➕ 新增轄內單位")
                    with st.form("add_unit_form", clear_on_submit=True):
                        nu_name = st.text_input("單位名稱 *", placeholder="例：三重義消中隊、救護義消分隊")
                        nu_type = st.selectbox("單位類別", ["消防大隊", "消防分隊", "義消大隊", "義消中隊", "義消分隊", "救難團體", "志工隊伍"])
                        nu_dist = st.text_input("轄區分區", placeholder="例：東區、西區、特種")
                        if st.form_submit_button("新增單位", type="primary", use_container_width=True):
                            if not nu_name:
                                st.error("請填寫單位名稱！")
                            else:
                                exist = db.query(FireUnit).filter(FireUnit.unit_name == nu_name.strip()).first()
                                if exist:
                                    st.error("該單位名稱已存在！")
                                else:
                                    new_u = FireUnit(unit_name=nu_name.strip(), unit_type=nu_type, district=nu_dist.strip())
                                    db.add(new_u)
                                    db.commit()
                                    st.success(f"✅ 單位【{nu_name}】已成功新增！")
                                    st.rerun()

        # ==========================================
        # TAB 3: 督勤重點項目庫維護
        # ==========================================
        with tab_items:
            st.subheader("📋 督勤重點項目定義庫")
            st.caption("局端與科內各期宣導重點、防救災安全查核指標設定")

            items = db.query(InspectionFocusItem).order_by(InspectionFocusItem.category.asc()).all()
            
            i_c1, i_c2 = st.columns([1.5, 1])
            with i_c1:
                st.write(f"目前共定義 **{len(items)}** 項督勤重點：")
                i_data = [{"ID": it.id, "重點類別": it.category, "查核項目名稱": it.item_name, "查核重點說明": it.description or ""} for it in items]
                st.dataframe(pd.DataFrame(i_data), use_container_width=True, hide_index=True)

            with i_c2:
                with st.container(border=True):
                    st.write("##### ➕ 新增督勤查核重點")
                    with st.form("add_item_form", clear_on_submit=True):
                        ni_cat = st.selectbox("重點類別", ["局端重點政策", "義消簽到與時數", "救災安全防護", "裝備保養管理", "福利慰問宣導", "組織運作與招募", "民力關懷互動", "其他專案"])
                        ni_name = st.text_input("查核項目名稱 *", placeholder="例：常年訓練出席簽退與安全裝備抽檢")
                        ni_desc = st.text_area("查核指引與重點說明", placeholder="例：查核現場簽到簿、抽查個人防護裝備是否依規範保養穿戴。")
                        if st.form_submit_button("新增重點項目", type="primary", use_container_width=True):
                            if not ni_name:
                                st.error("請填寫項目名稱！")
                            else:
                                new_it = InspectionFocusItem(category=ni_cat, item_name=ni_name.strip(), description=ni_desc.strip() if ni_desc else "")
                                db.add(new_it)
                                db.commit()
                                st.success("✅ 督勤重點項目已成功新增！")
                                st.rerun()

        # ==========================================
        # TAB 4: 資料庫備份與重設
        # ==========================================
        with tab_db:
            st.subheader("💾 本地 SQLite 資料庫維護與下載")
            st.markdown(f"**資料庫實體檔案位置：** `{DB_PATH}`")

            if os.path.exists(DB_PATH):
                with open(DB_PATH, "rb") as f:
                    db_bytes = f.read()
                st.download_button(
                    label="📥 下載資料庫完整備份檔 (civil_force.db)",
                    data=db_bytes,
                    file_name=f"civil_force_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                    mime="application/x-sqlite3",
                    type="primary"
                )

            st.markdown("---")
            st.markdown("##### ⚠️ 重設系統資料庫為預設示範資料")
            st.caption("此操作將重設公文、行事曆、督勤報告與範本至開箱預設資料，便於示範與測試。")
            if st.button("🔄 重設種子資料庫", type="secondary"):
                init_db(force_reseed=True)
                st.success("✅ 資料庫已成功檢查並補齊種子資料！")
                st.rerun()

        # ==========================================
        # TAB 5: 一鍵同步至 GitHub 雲端
        # ==========================================
        with tab_git:
            st.subheader("🚀 一鍵自動同步更新至 GitHub 雲端倉庫")
            
            st.markdown(
                """
                <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px 16px; border-radius: 6px; font-size: 0.9rem; color: #166534; margin-bottom: 1.2rem;">
                    <b>💡 為什麼需要一鍵同步？</b><br>
                    • 當您在本地電腦修改了代碼、自訂了督導狀況詞庫或完成更新後，<b>只要點擊下方按鈕，系統會自動將所有變更推送到 GitHub</b>！<br>
                    • <b>完全自動化</b>：GitHub 收到推送後，<b>Streamlit 雲端伺服器會在 15~30 秒內自動拉取並重啟生效</b>，手機與全體同仁立即看到最新版本！
                </div>
                """,
                unsafe_allow_html=True
            )

            col_g1, col_g2 = st.columns([1.3, 1])
            with col_g1:
                with st.container(border=True):
                    st.markdown("##### 📦 方式一：網頁介面直接一鍵推送")
                    st.caption("自動執行 `git add .` ➔ `git commit` ➔ `git push origin main`")
                    
                    commit_msg_input = st.text_input(
                        "更新版本說明 (Commit Message)",
                        value=f"更新看板與督勤詞庫: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        placeholder="輸入本次更新的說明"
                    )
                    
                    if st.button("🚀 立即一鍵自動同步至 GitHub", type="primary", use_container_width=True):
                        with st.spinner("正在自動加入變更、打包版本並推送至 GitHub 倉庫中..."):
                            success, msg = run_git_sync(commit_msg_input)
                            if success:
                                st.success(msg)
                                st.balloons()
                            else:
                                st.error(msg)
                                st.info("💡 提示：若出現權限錯誤，可直接使用右側的 Windows 批次檔進行推送。")

            with col_g2:
                with st.container(border=True):
                    st.markdown("##### 💻 方式二：Windows 桌面一鍵批次檔")
                    st.markdown(
                        """
                        專案目錄內已建立專用批次檔：<br>
                        👉 <code>一鍵上傳到GitHub.bat</code><br><br>
                        <b>使用方式</b>：<br>
                        1. 打開專案資料夾。<br>
                        2. <b>滑鼠雙擊 <code>一鍵上傳到GitHub.bat</code></b>。<br>
                        3. 視窗會全自動完成所有推送作業並顯示綠色成功訊息！
                        """,
                        unsafe_allow_html=True
                    )

    finally:
        db.close()
