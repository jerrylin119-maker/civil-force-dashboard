@echo off
chcp 65001 >nul
title 臺東縣消防局民力科看板 - 一鍵同步到 GitHub
color 0A
echo ========================================================
echo   🚒 臺東縣消防局民力科看板系統 - 一鍵同步到 GitHub
echo ========================================================
echo.
echo [1/3] 正在檢查與加入所有已修改檔案...
git add .

echo [2/3] 正在建立版本存檔標籤...
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (set mydate=%%a-%%b-%%c)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set mytime=%%a:%%b)
git commit -m "Auto update: %mydate% %mytime%"

echo [3/3] 正在推送至 GitHub 雲端倉庫...
git push origin main
if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   🎉 成功！所有最新程式碼與設定已同步推送至 GitHub！
    echo   Streamlit 雲端將在 15 秒內自動完成部署與更新！
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo   ⚠️ 推送若需要認證，請依畫面提示登入 GitHub 即可完成。
    echo ========================================================
)
echo.
pause
