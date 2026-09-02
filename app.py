"""
民力科業務執行與督勤彙整看板系統 - 系統主程式 (Main App)
"""
import os
import streamlit as st
from pathlib import Path

# 設定頁面配置 (必須是第一個 Streamlit 指令)
st.set_page_config(
    page_title="民力科業務執行與督勤彙整看板系統",
    page_icon="🚒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 匯入自訂模組
from config import APP_TITLE, APP_SUBTITLE, APP_ICON, APP_VERSION, STATIC_DIR
from database import init_db
from auth import init_auth_state, is_authenticated, get_current_user, logout, render_login_ui
from ai_helper import get_gemini_api_key
from pages_modules.mod1_documents import render_documents_module
from pages_modules.mod2_calendar import render_calendar_module
from pages_modules.mod3_inspection import render_inspection_module
from pages_modules.mod4_speech_press import render_speech_press_module
from pages_modules.mod5_settings import render_settings_module

def load_custom_css():
    """載入自訂主題樣式表"""
    css_path = STATIC_DIR / "custom.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    # 載入樣式
    load_custom_css()
    
    # 初始化資料庫種子
    init_db()
    
    # 初始化身分認證狀態
    init_auth_state()

    # 全員開放模式：直接渲染側邊欄與主要功能看板
    user = get_current_user()

    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 0.5rem 0 0.8rem 0;">
                <div style="font-size: 2.6rem;">{APP_ICON}</div>
                <h3 style="color: #1e3a8a; margin: 0; font-size: 1.2rem;">民力科業務看板系統</h3>
                <span style="font-size: 0.75rem; color: #64748b;">臺東縣消防局 ｜ 全員通用版</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 操作同仁身分卡片 (可自由輸入姓名，全員同等權限)
        with st.container(border=True):
            curr_name = user.get('display_name', '民力科同仁') if user else '民力科同仁'
            new_operator_name = st.text_input(
                "👤 目前操作同仁姓名",
                value=curr_name,
                placeholder="例：陳科員、林科員",
                help="輸入您的稱呼，系統將在督勤填報與公文承辦時自動帶入您的姓名。"
            )
            if new_operator_name != curr_name:
                set_user_display_name(new_operator_name)
                st.rerun()

        # AI 引擎狀態標記
        api_key = get_gemini_api_key()
        if api_key:
            st.markdown(
                """
                <div style="background: #dcfce7; color: #166534; padding: 6px 10px; border-radius: 6px; font-size: 0.8rem; text-align: center; margin: 8px 0; border: 1px solid #86efac;">
                    🟢 Gemini AI 視覺與生成已連線
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="background: #fef3c7; color: #92400e; padding: 6px 10px; border-radius: 6px; font-size: 0.8rem; text-align: center; margin: 8px 0; border: 1px solid #fcd34d;">
                    🟡 智慧範本模式 (未設定 API Key)
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")

        # 模組導航選單
        nav_selection = st.radio(
            "📌 核心功能模組導航",
            [
                "📑 模組一：重要計畫及公文續辦管理",
                "📅 模組二：圖文辨識與公務行事曆",
                "🛡️ 模組三：督勤管理與報告產出機",
                "✍️ 模組四：新聞稿與致詞稿智慧生成",
                "⚙️ 模組五：系統設定與資料庫管理"
            ],
            index=0
        )

        st.markdown("---")
        with st.expander("🚀 一鍵同步更新到 GitHub", expanded=False):
            st.caption("在本地修改代碼或自訂詞庫後，點擊立即自動推送到 GitHub 雲端：")
            if st.button("🚀 立即推送更新", use_container_width=True, key="sidebar_git_sync_btn"):
                from git_sync_helper import run_git_sync
                with st.spinner("同步推送中..."):
                    ok_git, git_msg = run_git_sync()
                    if ok_git:
                        st.success("✅ 已成功同步至 GitHub！Streamlit 雲端已開始自動部署！")
                        st.balloons()
                    else:
                        st.error(git_msg)

        st.markdown(
            """
            <div style="font-size: 0.75rem; color: #94a3b8; text-align: center;">
                民力科業務執行與督勤彙整看板系統<br>
                支援電腦大螢幕與手機跨端操作
            </div>
            """,
            unsafe_allow_html=True
        )

    # 路由至各模組頁面
    if "模組一" in nav_selection:
        render_documents_module()
    elif "模組二" in nav_selection:
        render_calendar_module()
    elif "模組三" in nav_selection:
        render_inspection_module()
    elif "模組四" in nav_selection:
        render_speech_press_module()
    elif "模組五" in nav_selection:
        render_settings_module()

if __name__ == "__main__":
    main()
