"""
民力科業務執行與督勤彙整看板系統 - 全員通用身分與權限模組 (無需區分主管與同仁，全員同權限)
"""
import streamlit as st

def init_auth_state():
    """初始化驗證狀態 - 預設直接放行，全員同權限"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = True
    if "user" not in st.session_state or not st.session_state["user"]:
        st.session_state["user"] = {
            "id": 1,
            "username": "civil_force_staff",
            "display_name": "民力科同仁",
            "role": "民力科同仁",
            "email": "civil_force@fire.gov.tw"
        }
    if "current_role" not in st.session_state:
        st.session_state["current_role"] = "民力科同仁"

def get_current_user():
    """取得當前使用者資訊"""
    init_auth_state()
    return st.session_state.get("user")

def is_authenticated():
    """檢查是否已登入 (預設全員開放)"""
    init_auth_state()
    return True

def set_user_display_name(new_name: str):
    """設定同仁顯示名稱 (例如用於督勤簽名或公文承辦人)"""
    init_auth_state()
    st.session_state["user"]["display_name"] = new_name.strip() if new_name.strip() else "民力科同仁"

def login(user_info: dict):
    """設定使用者資訊"""
    st.session_state["authenticated"] = True
    st.session_state["user"] = user_info
    st.session_state["current_role"] = "民力科同仁"

def logout():
    """重設同仁名稱為預設值"""
    st.session_state["user"] = {
        "id": 1,
        "username": "civil_force_staff",
        "display_name": "民力科同仁",
        "role": "民力科同仁",
        "email": "civil_force@fire.gov.tw"
    }

def render_login_ui():
    """全員開放模式下無須登入頁，直接進入看板"""
    init_auth_state()
