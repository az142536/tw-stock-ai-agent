"""
台股 AI 時事監控與智能選股系統 - 核心配置檔 (Configuration)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 環境變數
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    # -----------------------------
    # AI 模型配置 (LLM Settings)
    # -----------------------------
    # 支援 Google Gemini API (若未設定則自動切換為內建台股 NLP 語意推理雙引擎)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # -----------------------------
    # 新聞與時事監控配置 (News Settings)
    # -----------------------------
    # 支援: cnyes (鉅亨網), yahoo (Yahoo股市), google (Google財經)
    NEWS_SOURCES = ["cnyes", "yahoo", "google"]
    NEWS_FETCH_LIMIT = int(os.getenv("NEWS_FETCH_LIMIT", "35"))
    NEWS_MAX_AGE_HOURS = int(os.getenv("NEWS_MAX_AGE_HOURS", "48")) # 追蹤過去48小時內熱門新聞

    # -----------------------------
    # 技術面過濾與風控閥值 (Technical & Risk Parameters)
    # -----------------------------
    MA_SHORT = 5          # 週線 (5MA)
    MA_MEDIUM = 20        # 月線 (20MA) - 關鍵生命線
    MA_LONG = 60          # 季線 (60MA) - 關鍵趨勢線

    MIN_DAILY_VOLUME = 800       # 最低日成交量 (張)，過濾流動性不足的冷門殭屍股
    MIN_PRICE = 15.0             # 最低股價 (元)，過濾極度投機仙股
    MAX_PRICE = 5000.0           # 最高股價 (元)

    VOLUME_SPIKE_RATIO = 1.25    # 量能倍數閥值 (今日成交量 >= 5日均量 1.25倍視為攻擊量)
    MAX_BIAS_20 = 12.0           # 乖離率上限 (%)，超過12%視為短線過熱，禁止追高！
    MIN_RISK_REWARD_RATIO = 1.8  # 最低風報比要求 (潛在獲利 / 承受停損風險)
    DEFAULT_STOP_LOSS_PCT = 0.05 # 預設停損幅度 (5%)，若未破支撐則以跌破月線為準

    # -----------------------------
    # 監控循環配置 (Watch Mode Settings)
    # -----------------------------
    WATCH_INTERVAL_SECONDS = int(os.getenv("WATCH_INTERVAL_SECONDS", "60")) # 預設每 60 秒 (1分鐘) 即時快掃一次
    AUTO_NOTIFY_MIN_SCORE = 75.0 # 自動推播最低綜合推薦分數 (滿分100)

    # -----------------------------
    # 社群推播通知配置 (Notification Settings)
    # -----------------------------
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

    # 報表輸出目錄
    REPORT_DIR = BASE_DIR / "reports"

Config.REPORT_DIR.mkdir(parents=True, exist_ok=True)

