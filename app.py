"""
台股 AI 雙引擎時事戰情室 - Web App 伺服器 (Aiohttp Web Backend)
提供 REST API 與手機/電腦自適應 PWA 網頁介面：
- GET /                    : 戰情室單頁應用 (PWA)
- GET /api/scan            : 全市場時事與 Top 3 推薦即時數據
- GET /api/diagnose?symbol : 單一股票入場價、停損價、停利點健檢
"""

import sys
import io
import json
import logging
import socket
import webbrowser
from pathlib import Path
from aiohttp import web
from scanner import TaiwanStockAIScanner
from config import Config

# Windows UTF-8 編碼相容
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("StockAppServer")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# 初始化共用掃描器與快取
scanner = TaiwanStockAIScanner()
cached_scan_data = None
last_scan_time = 0


def get_local_ip() -> str:
    """取得本機區域網路 IP，方便手機瀏覽"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


async def handle_index(request: web.Request) -> web.Response:
    """首頁 HTML"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return web.FileResponse(index_file)
    return web.Response(text="<h1>找不到 static/index.html</h1>", content_type="text/html")


async def handle_scan_api(request: web.Request) -> web.Response:
    """全市場掃描 API (含快取機制)"""
    global cached_scan_data, last_scan_time
    import time
    now = time.time()

    # 15 秒內請求直接返回快取，避免重複高頻運算
    if cached_scan_data and (now - last_scan_time < 15):
        return web.json_response(cached_scan_data)

    try:
        result = scanner.run_full_scan(top_k=10)
        cached_scan_data = result
        last_scan_time = now
        return web.json_response(result)
    except Exception as e:
        logger.error(f"掃描 API 發生異常: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_diagnose_api(request: web.Request) -> web.Response:
    """個股專屬診斷 API"""
    symbol = request.query.get("symbol", "").strip()
    if not symbol:
        return web.json_response({"error": "請提供台股代號 (如: 2330)"}, status=400)

    try:
        diag = scanner.diagnose_single_stock(symbol)
        if not diag:
            return web.json_response({"error": f"找不到股票代號 {symbol}"}, status=404)
        return web.json_response(diag)
    except Exception as e:
        logger.error(f"診斷 API 發生異常: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


async def handle_learning_stats(request: web.Request) -> web.Response:
    """AI 自我學習與歷史勝率覆盤看板 API"""
    try:
        data = scanner.learning_engine.get_learning_dashboard_data()
        return web.json_response(data)
    except Exception as e:
        logger.error(f"取得學習數據異常: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/scan", handle_scan_api)
    app.router.add_get("/api/diagnose", handle_diagnose_api)
    app.router.add_get("/api/learning_stats", handle_learning_stats)
    app.router.add_static("/static/", STATIC_DIR)
    return app


def main():
    import os
    port = int(os.getenv("PORT", 8000))
    local_ip = get_local_ip()

    print("\n" + "=" * 70)
    print("🚀 台股 AI 雙引擎時事戰情室 APP 已成功就緒！")
    print("=" * 70)
    print(f"📱 電腦本機存取網址: http://localhost:{port}")
    print(f"📲 同 Wi-Fi 手機存取網址: http://{local_ip}:{port}")
    print("提示：在手機 Safari 或 Chrome 開啟後，點擊「加入主畫面」即可像原生 App 一樣使用！")
    print("按 Ctrl+C 可停止伺服器。\n" + "=" * 70 + "\n")

    app = create_app()
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

