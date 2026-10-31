@echo off
chcp 65001 >nul
title 台股 AI 雙引擎時事戰情室 APP
cd /d "%~dp0"
echo ===============================================================
echo 🚀 正在啟動 台股 AI 雙引擎時事戰情室 APP...
echo ===============================================================
echo.
echo 電腦瀏覽器開啟: http://localhost:8000
echo 手機同 Wi-Fi 亦可直接輸入畫面顯示的區網 IP 使用！
echo.
start http://localhost:8000
python app.py
pause

