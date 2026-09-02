"""
民力科看板 - GitHub 一鍵自動同步模組
支援網頁介面直接點擊按鈕執行 git add, commit, push 自動推送至 GitHub
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Tuple

BASE_DIR = Path(__file__).resolve().parent

def run_git_sync(commit_message: str = None) -> Tuple[bool, str]:
    """
    執行一鍵 git 同步：add, commit, push
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = commit_message.strip() if commit_message else f"Auto update from Dashboard: {now_str}"
    
    try:
        # 1. git add .
        add_res = subprocess.run(
            ["git", "add", "."],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if add_res.returncode != 0:
            return False, f"Git Add 失敗: {add_res.stderr}"

        # 2. git commit
        commit_res = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        # returncode 為 1 若無任何變更，需特別處理
        if commit_res.returncode != 0 and "nothing to commit" not in commit_res.stdout and "nothing to commit" not in commit_res.stderr:
            return False, f"Git Commit 失敗: {commit_res.stderr or commit_res.stdout}"

        # 3. git push origin main
        push_res = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if push_res.returncode != 0:
            return False, f"Git Push 失敗: {push_res.stderr or push_res.stdout}"

        return True, f"🎉 成功同步推送至 GitHub (main 分支)！Streamlit 雲端已自動開始部署更新！"

    except Exception as e:
        return False, f"執行發生例外錯誤: {str(e)}"
