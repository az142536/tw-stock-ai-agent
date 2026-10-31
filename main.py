"""
台股 AI 時事智能監控與精準選股系統 - 主程式入口 (Main CLI Application)
支援指令：
  python main.py                     # 執行預設選股掃描
  python main.py --mode scan         # 執行即時全市場時事與量價綜合掃描
  python main.py --mode watch        # 盤中定時即時監控循環 (偵測時事催化飆股)
  python main.py --stock 2330        # 個股時事與技術面即時健檢
  python main.py --demo              # 快速展示示範模式
  python main.py --notify            # 啟用 Telegram / Discord 推播
"""

import argparse
import sys
import io
import time
import logging
from datetime import datetime

# Windows 終端機 UTF-8 編碼相容性設定
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from scanner import TaiwanStockAIScanner
from notifier import StockNotifier
from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TaiwanStockAI")


def run_scan_workflow(scanner: TaiwanStockAIScanner, send_notifications: bool = False, top_k: int = 10):
    """執行一次完整的掃描與輸出工作流"""
    result = scanner.run_full_scan(top_k=top_k)
    
    # 1. 終端控制台儀表板輸出
    StockNotifier.print_terminal_dashboard(result)

    # 2. 自動產出 Markdown 操盤日報
    report_path = StockNotifier.export_markdown_report(result)
    print(f"\n📄 完整操盤日報已存檔至: {report_path}")

    # 3. 社群推播 (若設定且有標的高於閥值)
    if send_notifications:
        notified_count = 0
        for p in result["top_picks"]:
            if p["total_score"] >= Config.AUTO_NOTIFY_MIN_SCORE:
                tg_ok = StockNotifier.send_telegram_alert(p)
                dc_ok = StockNotifier.send_discord_webhook(p)
                if tg_ok or dc_ok:
                    notified_count += 1
        if notified_count > 0:
            print(f"🔔 已成功發送 {notified_count} 則重點個股推播通知。")


def run_watch_loop(scanner: TaiwanStockAIScanner, interval_seconds: int = 60, send_notifications: bool = True):
    """盤中每分鐘即時監控循環 (偵測最新時事報導與 Top 3 飆股)"""
    print(f"\n🚀 啟動台股雙 AI 盤中每分鐘即時監控模式 (每 {interval_seconds} 秒掃描一次)...")
    print("即時監控: 鉅亨網、Yahoo股市、Google財經時事報導 & 台股即時量價")
    print("按 Ctrl+C 可隨時中止監控。\n")
    already_alerted_stocks = set()

    try:
        round_idx = 1
        while True:
            now_str = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{now_str}] 執行第 {round_idx} 次每分鐘即時時事與市場量價掃描...")
            result = scanner.run_full_scan(top_k=8)
            StockNotifier.print_terminal_dashboard(result)

            # 自動儲存本分鐘日報
            report_path = StockNotifier.export_markdown_report(result)

            # 檢查是否有新晉 S 級爆量時事推薦股 (前三名優先)
            for p in result.get("top_3_picks", []):
                sym = p["symbol"]
                if p["total_score"] >= Config.AUTO_NOTIFY_MIN_SCORE and sym not in already_alerted_stocks:
                    already_alerted_stocks.add(sym)
                    if send_notifications:
                        StockNotifier.send_telegram_alert(p)
                        StockNotifier.send_discord_webhook(p)
                    print(f"🔥 【最新突發題材飆股推播】: #{p['rank_grade']} {p['symbol']} {p['name']} (總分: {p['total_score']} | 勝率: {p.get('win_rate_pct')}% )")

            round_idx += 1
            print(f"\n⏳ 下次時事偵測將在 {interval_seconds} 秒後執行 (每分鐘自動刷新)...")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n👋 每分鐘即時監控已手動停止。")


def run_stock_diagnosis(scanner: TaiwanStockAIScanner, symbol: str):
    """單一股票專屬健檢"""
    diag = scanner.diagnose_single_stock(symbol)
    if not diag:
        print(f"❌ 查無代號 {symbol} 之相關資料。")
        return

    tech = diag["tech"]
    setup = diag["setup"]

    print("\n" + "=" * 64)
    print(f"🔍 【{tech['symbol']} {tech['name']}】 AI 時事與技術量價健檢報告")
    print("=" * 64)
    print(f"• 最新現價: {tech['price']} 元 (今日漲跌: {tech['change_pct']:+.2f}%)")
    print(f"• 今日成交量: {tech['volume']} 張 (5日均量: {tech['vol_ma5']} 張，量比: {tech['vol_ratio']}x)")
    print(f"• 均線結構: {tech['trend_alignment']}")
    print(f"• 關鍵均線: 5MA: {tech['ma5']} | 20MA(月線): {tech['ma20']} | 60MA(季線): {tech['ma60']}")
    print(f"• 月線乖離率 (BIAS): {tech['bias_ma20']}% {'(⚠️ 乖離過大防追高)' if tech['is_overheated'] else '(健康乖離)'}")
    print(f"• KD 動能指標: K={tech['kd_k']}, D={tech['kd_d']}")
    print("-" * 64)
    print(f"• 預估波段成功率 (勝率): {setup.get('win_rate_pct', 75.0)}% {setup.get('win_gauge', '')}")
    print(f"• 歷史統計依據: {setup.get('sample_stats', '')}")
    print(f"• 預期數學期望值 (EV): +{setup.get('expected_return_pct', 10.5)}%")
    print(f"• 操作訊號判定: {setup['action_tag']}")
    print(f"• 建議進場區間: {setup['entry_zone']} 元")
    print(f"• 防守停損價位: {setup['stop_loss']} 元 (承擔風險約 {setup['risk_pct']}%)")
    print(f"• 目標獲利價位: 第一目標 {setup['target_1']} 元 / 第二目標 {setup['target_2']} 元")
    print(f"• 試算風報比: 1:{setup['risk_reward_ratio']}")
    print("-" * 64)
    print("• 時事催化與受惠原因:")
    for r in diag["reasons"]:
        print(f"  - {r}")
    print("=" * 64 + "\n")


def main():
    parser = argparse.ArgumentParser(description="台股 AI 時事智能監控與精準選股系統 (TW Stock AI Sentinel)")
    parser.add_argument("--mode", choices=["scan", "watch", "diagnose"], default="scan", help="運行模式: scan (單次掃描), watch (盤中監控循環)")
    parser.add_argument("--stock", type=str, default="", help="單一個股即時健檢代號 (如: 2330, 3017, 3450)")
    parser.add_argument("--demo", action="store_true", help="執行示範展示模式")
    parser.add_argument("--notify", action="store_true", help="開啟 Telegram / Discord 社群推播")
    parser.add_argument("--interval", type=int, default=Config.WATCH_INTERVAL_SECONDS, help="盤中監控循環間隔秒數 (預設 300 秒)")
    parser.add_argument("--top", type=int, default=10, help="輸出推薦標的數量 (預設 10 檔)")

    args = parser.parse_args()

    scanner = TaiwanStockAIScanner()

    if args.stock:
        run_stock_diagnosis(scanner, args.stock)
    elif args.mode == "watch":
        run_watch_loop(scanner, interval_seconds=args.interval, send_notifications=args.notify)
    else:
        # scan or demo
        run_scan_workflow(scanner, send_notifications=args.notify, top_k=args.top)


if __name__ == "__main__":
    main()
