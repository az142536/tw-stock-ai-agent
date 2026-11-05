"""
推播通知與報表輸出模組 (Taiwan Stock Alerts & Report Generator)
1. 終端控制台多色彩美觀儀表板 (支援 Tabulate 與 ANSI 色彩)
2. Telegram Bot 即時推播 (Markdown 格式)
3. Discord Webhook 卡片推播
4. 自動產出 Markdown / HTML 操盤日報
"""

import json
import logging
import urllib.request
from datetime import datetime
from typing import Dict, Any, List
from tabulate import tabulate
from config import Config

logger = logging.getLogger(__name__)

# ANSI 顏色常數
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class StockNotifier:
    """台股時事推薦通知與報表產生器"""

    @staticmethod
    def print_terminal_dashboard(scan_result: Dict[str, Any]):
        """在終端機印出精美台股 AI 雙引擎推薦與每分鐘時事監控看板"""
        top_picks = scan_result.get("top_picks", [])
        top_3 = scan_result.get("top_3_picks", top_picks[:3])
        total_news = scan_result.get("total_news_analyzed", 0)
        breaking_count = scan_result.get("breaking_news_count", 0)
        breaking_list = scan_result.get("breaking_news_list", [])
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("\n" + "=" * 98)
        print(f"{BOLD}{CYAN}🚀 台股 AI 雙引擎時事每分鐘智能監控系統 (TW Stock Dual-AI Sentinel){RESET}")
        print(f"⏱️ 監控時間: {now_str} | 已解析最新重大時事: {total_news} 則 | 監控頻率: 每 60 秒即時快掃")
        
        # 若本分鐘有新抵達的快訊，顯示高亮警示
        if breaking_count > 0:
            print(f"{BOLD}{YELLOW}🚨 【即時突發快訊】本分鐘偵測到 {breaking_count} 則最新重大財經時事！{RESET}")
            for b in breaking_list:
                print(f"   📰 [{b.get('source', '即時快訊')}] {b.get('title', '')[:50]}...")

        print("=" * 98)

        # ----------------------------------------------------
        # 1. 前三名首選 (Top 3 Picks) - 雙 AI 整合與成功率深度解析
        # ----------------------------------------------------
        print(f"\n{BOLD}{RED}👑 【雙 AI 整合精選推薦前三名個股 (Top 3) - 成功率與實戰操盤計畫】{RESET}")

        for idx, p in enumerate(top_3, 1):
            rank_medal = "🥇 首選第一名" if idx == 1 else ("🥈 首選第二名" if idx == 2 else "🥉 首選第三名")
            
            # 勝率色彩
            wr = p.get("win_rate_pct", 75.0)
            if wr >= 85.0:
                wr_str = f"{BOLD}{RED}{p.get('win_gauge', '')} {wr}% (極高勝率){RESET}"
            elif wr >= 75.0:
                wr_str = f"{BOLD}{YELLOW}{p.get('win_gauge', '')} {wr}% (優良勝率){RESET}"
            else:
                wr_str = f"{p.get('win_gauge', '')} {wr}%"

            print(f"\n{BOLD}#{idx} {rank_medal}：【{p['symbol']} {p['name']}】 - {p['rank_grade']}{RESET}")
            print(f"  ┌── 🎯 核心題材: {CYAN}{p['theme']}{RESET} | 建議週期: {p['horizon']}")
            print(f"  ├── 📈 預估波段成功率: {wr_str}")
            print(f"  │    └─ 統計依據: {p.get('sample_stats', '')}")
            print(f"  ├── 🤖 雙 AI 整合共識度: {BOLD}{CYAN}{p.get('consensus_pct', 88.0)}%{RESET} (綜合評分: {BOLD}{RED}{p['total_score']} 分{RESET})")
            print(f"  │    ├─ 【AI-1 宏觀時事大腦】: {p.get('ai1_view', '題材受惠顯著')}")
            print(f"  │    └─ 【AI-2 量化圖譜大腦】: {p.get('ai2_view', '供應鏈地位關鍵')}")
            print(f"  ├── 💰 現價: {p['price']} ({RED}+{p['change_pct']}%{RESET}) | 量能: {p['vol_ratio']}x 5日均量 | 20MA乖離: {p['bias_ma20']}%")
            print(f"  ├── 🛒 建議買進區間: {BOLD}{p['entry_zone']} 元{RESET}")
            print(f"  ├── 🛑 防守停損價位: {BOLD}{RED}{p['stop_loss']} 元{RESET} (嚴守風控，跌破不戀戰，最大風險僅 {p['risk_pct']}%)")
            print(f"  ├── 🚀 第一波段目標: {BOLD}{GREEN}{p['target_1']} 元{RESET} (預估獲利 +{p.get('target_gain_pct', 14.5)}%)")
            print(f"  └── ⚖️ 數學期望值 (EV): {BOLD}{GREEN}+{p.get('expected_return_pct', 10.5)}%{RESET} | 風報比: {BOLD}1:{p['risk_reward_ratio']}{RESET}")

        print("\n" + "-" * 98)

        # ----------------------------------------------------
        # 2. 全市場候選池總覽表格
        # ----------------------------------------------------
        print(f"{BOLD}{YELLOW}📊 【全市場 AI 時事量價推薦排行榜 (Top 10 Overview)】{RESET}")
        table_rows = []
        for idx, p in enumerate(top_picks, 1):
            chg = p["change_pct"]
            chg_str = f"{RED}+{chg:.2f}%{RESET}" if chg > 0 else (f"{GREEN}{chg:.2f}%{RESET}" if chg < 0 else "0.00%")

            score = p["total_score"]
            score_str = f"{BOLD}{RED}{score}{RESET}" if score >= 85 else (f"{BOLD}{YELLOW}{score}{RESET}" if score >= 75 else f"{score}")

            wr = p.get("win_rate_pct", 75.0)
            wr_str = f"{BOLD}{RED}{wr}%{RESET}" if wr >= 85 else f"{wr}%"

            table_rows.append([
                idx,
                f"{p['symbol']} {p['name']}",
                p["theme"][:7],
                score_str,
                f"{p.get('consensus_pct', 88.0):.0f}%",
                wr_str,
                f"{p['price']:.1f}",
                chg_str,
                f"{p['vol_ratio']:.2f}x",
                p["action_tag"][:10],
                f"{p['stop_loss']:.1f}",
                f"{p['target_1']:.1f}",
                f"1:{p['risk_reward_ratio']:.1f}"
            ])

        headers = [
            "名次", "個股", "核心題材", "AI總分", "雙AI共識", "預估成功率",
            "現價", "漲跌幅", "量比", "操作訊號", "停損點", "目標價", "風報比"
        ]

        print(tabulate(table_rows, headers=headers, tablefmt="grid", stralign="center"))
        print("=" * 98)

    @staticmethod
    def export_markdown_report(scan_result: Dict[str, Any]) -> str:
        """產出專業 Markdown 操盤日報"""
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M")
        file_path = Config.REPORT_DIR / f"tw_stock_ai_report_{date_str}.md"

        top_picks = scan_result.get("top_picks", [])
        total_news = scan_result.get("total_news_analyzed", 0)

        lines = [
            f"# 🚀 台股 AI 雙引擎時事智能監控與推薦日報",
            f"- **產出時間**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **追蹤時事新聞數**: {total_news} 則重大財經頭條",
            f"- **核心策略哲學**: 雙 AI 引擎共識 + 時事催化 + 均線多頭 + 爆量突破 + 風報比 >= 1.8:1 + 成功率精算",
            "",
            "## 📊 推薦評分排行榜 (Top Picks Overview)",
            "",
            "| 名次 | 代號 | 名稱 | 核心題材 | AI總分 | 雙AI共識 | 預估成功率 | 現價 | 漲跌幅 | 量比 | 建議買進區間 | 防守停損 | 目標價 | 預估風報比 |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for idx, p in enumerate(top_picks, 1):
            lines.append(
                f"| {idx} | `{p['symbol']}` | **{p['name']}** | {p['theme']} | **{p['total_score']}** | "
                f"{p.get('consensus_pct', 88.0):.0f}% | **{p.get('win_rate_pct', 75.0)}%** | "
                f"{p['price']} | {p['change_pct']:+.2f}% | {p['vol_ratio']}x | "
                f"{p['entry_zone']} | `{p['stop_loss']}` | `{p['target_1']}` | 1:{p['risk_reward_ratio']} |"
            )

        lines.extend([
            "",
            "---",
            "## 👑 Top 3 首選個股深度剖析與實戰操盤計畫",
            ""
        ])

        for idx, p in enumerate(scan_result.get("top_3_picks", top_picks[:3]), 1):
            rank_title = "🥇 首選第一名" if idx == 1 else ("🥈 首選第二名" if idx == 2 else "🥉 首選第三名")
            lines.extend([
                f"### #{idx} {rank_title}：{p['symbol']} {p['name']} ({p['rank_grade']})",
                f"- **題材族群**: {p['theme']} (建議操作週期: {p['horizon']})",
                f"- **📈 預估波段成功率**: **{p.get('win_rate_pct', 75.0)}%** (統計依據: {p.get('sample_stats', '')})",
                f"- **🤖 雙 AI 共識度**: **{p.get('consensus_pct', 88.0)}%** (AI 總分: **{p['total_score']}**)",
                f"  - *AI-1 宏觀時事大腦*: {p.get('ai1_view', '')}",
                f"  - *AI-2 量化圖譜大腦*: {p.get('ai2_view', '')}",
                f"- **操作訊號**: `{p['action_tag']}`",
                f"- **建議進場區間**: `{p['entry_zone']}` 元",
                f"- **關鍵停損防守**: `{p['stop_loss']}` 元 (最大承受跌幅: {p['risk_pct']}%)",
                f"- **波段目標價位**: 第一目標 `{p['target_1']}` 元 (預估獲利 +{p.get('target_gain_pct', 14.5)}%) / 第二目標 `{p['target_2']}` 元",
                f"- **⚖️ 數學期望值 (EV)**: `+{p.get('expected_return_pct', 10.5)}%` (風報比: `1:{p['risk_reward_ratio']}`)",
                f"- **關聯新聞**: {p['related_news'][0] if p['related_news'] else '產業大單湧入'}",
                ""
            ])

        lines.extend([
            "---",
            "> ⚠️ **免責聲明**: 本報告由 AI 演算法與市場量價模型自動運算產出，僅供投資研究與學習參考，不構成任何實體投資要約或保證獲利承諾。交易股票請務必嚴格執行停損防守紀律。"
        ])

        content = "\n".join(lines)
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"成功輸出台股 AI 操盤日報: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.warning(f"輸出報告至硬碟略過或無權限: {e}")
            return ""

    @staticmethod
    def send_telegram_alert(pick: Dict[str, Any]) -> bool:
        """發送 Telegram 即時推播"""
        token = Config.TELEGRAM_BOT_TOKEN
        chat_id = Config.TELEGRAM_CHAT_ID
        if not token or not chat_id:
            return False

        text = (
            f"🔥 *【台股 AI 時事強烈推薦】*\n"
            f"📌 標的：`{pick['symbol']} {pick['name']}` ({pick['theme']})\n"
            f"🌟 AI綜合評分：*{pick['total_score']} 分* ({pick['rank_grade']})\n"
            f"💰 現價：{pick['price']} ({pick['change_pct']:+.2f}%)\n"
            f"⚡ 量比：{pick['vol_ratio']}x 均量 | 20MA乖離：{pick['bias_ma20']}%\n"
            f"🎯 建議買進：`{pick['entry_zone']}`\n"
            f"🛑 防守停損：`{pick['stop_loss']}` (風險 {pick['risk_pct']}%)\n"
            f"🚀 目標價：`{pick['target_1']}` (風報比 1:{pick['risk_reward_ratio']})\n"
            f"💡 催化理由：{pick['reasons'][0] if pick['reasons'] else ''}\n"
        )

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception as e:
            logger.debug(f"Telegram 推播失敗: {e}")
            return False

    @staticmethod
    def send_discord_webhook(pick: Dict[str, Any]) -> bool:
        """發送 Discord Webhook 卡片推播"""
        webhook_url = Config.DISCORD_WEBHOOK_URL
        if not webhook_url:
            return False

        color = 0x00FF00 if pick["total_score"] >= 80 else 0xFFD700
        payload = {
            "embeds": [{
                "title": f"🚀 台股 AI 時事推薦: {pick['symbol']} {pick['name']} (評分: {pick['total_score']})",
                "description": f"**受惠族群**: {pick['theme']}\n**訊號**: {pick['action_tag']}\n**催化理由**: {pick['reasons'][0] if pick['reasons'] else ''}",
                "color": color,
                "fields": [
                    {"name": "現價 / 漲跌", "value": f"{pick['price']} ({pick['change_pct']:+.2f}%)", "inline": True},
                    {"name": "量能倍數", "value": f"{pick['vol_ratio']}x", "inline": True},
                    {"name": "買進區間", "value": f"{pick['entry_zone']}", "inline": True},
                    {"name": "防守停損", "value": f"{pick['stop_loss']} 元", "inline": True},
                    {"name": "第一目標價", "value": f"{pick['target_1']} 元", "inline": True},
                    {"name": "預期風報比", "value": f"1:{pick['risk_reward_ratio']}", "inline": True},
                ],
                "footer": {"text": "台股 AI 智能時事監控系統 • 嚴格防守停損"}
            }]
        }
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status in (200, 204)
        except Exception as e:
            logger.debug(f"Discord 推播失敗: {e}")
            return False
