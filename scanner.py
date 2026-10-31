"""
台股時事與 AI 選股掃描引擎 (Taiwan Stock AI Scanner & Composite Ranker)
串聯 時事抓取 -> AI 產業鏈推理 -> 量價技術面確認 -> 風報比精算 -> 綜合評分排序
"""

import logging
from typing import List, Dict, Any, Optional
from news_fetcher import NewsFetcher
from ai_analyzer import AIAnalyzer
from tw_market_data import TaiwanMarketData
from technical_filter import TechnicalFilter
from learning_engine import SelfLearningEngine
from config import Config

logger = logging.getLogger(__name__)


class TaiwanStockAIScanner:
    """台股 AI 時事量價選股掃描器 (具備自我學習與覆盤反思能力)"""

    def __init__(self):
        self.news_fetcher = NewsFetcher()
        self.ai_analyzer = AIAnalyzer()
        self.market_data = TaiwanMarketData()
        self.learning_engine = SelfLearningEngine()

    def run_full_scan(self, top_k: int = 10) -> Dict[str, Any]:
        """
        執行全自動時事掃描與 AI 推薦選股：
        1. 抓取即時新聞
        2. AI 推理時事受惠股
        3. 驗證市場量價與均線型態
        4. 精算風報比與買進/停損點
        5. 產出綜合推薦清單
        """
        logger.info(">>> 步驟 1/4: 抓取最新台股重大時事與產業新聞...")
        news_items = self.news_fetcher.get_latest_news()
        logger.info(f"成功取得 {len(news_items)} 則重大財經新聞。")

        logger.info(">>> 步驟 2/4: AI 大腦推理時事催化題材與受惠個股鏈...")
        ai_candidates = self.ai_analyzer.analyze_news_batch(news_items)
        logger.info(f"AI 識別出 {len(ai_candidates)} 檔具備時事受惠潛力之台股標的。")

        logger.info(">>> 步驟 3/4: 技術面驗證、量能確認與防追高風控精算...")
        evaluated_picks = []

        for cand in ai_candidates:
            sym = cand["symbol"]
            theme = cand.get("theme", "台股熱門題材")
            consensus = cand.get("consensus_pct", 88.0)
            
            # 取得該檔股票即時行情與技術指標
            tech_snapshot = self.market_data.get_stock_technical_snapshot(sym)
            # 評估技術線型、停損停利、風報比與歷史回測勝率
            setup = TechnicalFilter.evaluate_setup(tech_snapshot, theme=theme, dual_ai_consensus=consensus)

            # 計算雙 AI 整合推薦綜合分數 (Composite AI Score, 滿分100)
            # 1. 雙 AI 時事催化與共識分 (0~45分)
            ai_score_part = (cand["catalyst_score"] * 0.35) + (consensus * 0.10)
            
            # 2. 技術面量價分 (0~35分)
            tech_score_part = setup["tech_score"]

            # 3. 風報比、位階與勝率加成 (0~20分)
            risk_reward_part = 0.0
            if setup["risk_reward_ratio"] >= 2.0:
                risk_reward_part += 8.0
            elif setup["risk_reward_ratio"] >= 1.5:
                risk_reward_part += 5.0

            # 成功率加成 (勝率越高額外加分)
            if setup["win_rate_pct"] >= 85.0:
                risk_reward_part += 6.0
            elif setup["win_rate_pct"] >= 75.0:
                risk_reward_part += 3.0

            if 2.0 <= tech_snapshot["bias_ma20"] <= 8.5:
                risk_reward_part += 6.0 # 乖離溫和甜蜜點
            elif tech_snapshot["bias_ma20"] > Config.MAX_BIAS_20:
                risk_reward_part -= 15.0 # 乖離過熱重罰

            # 4. 取得 AI 自我學習引擎之動態加成 (題材連勝加分 / 避雷庫降權)
            adaptive_boost = self.learning_engine.get_adaptive_boost(sym, theme)

            total_score = round(max(0.0, min(100.0, ai_score_part + tech_score_part + risk_reward_part + adaptive_boost)), 1)

            # 判定評級標籤
            if total_score >= 82.0 and setup["is_valid_trade"]:
                rank_grade = "S 級【首選攻擊股】"
            elif total_score >= 70.0 and setup["is_valid_trade"]:
                rank_grade = "A 級【波段潛力股】"
            elif total_score >= 55.0:
                rank_grade = "B 級【觀察名單】"
            else:
                rank_grade = "C 級【暫不建議/過熱】"

            evaluated_picks.append({
                "symbol": sym,
                "name": cand["name"],
                "theme": theme,
                "total_score": total_score,
                "rank_grade": rank_grade,
                "adaptive_boost": adaptive_boost,
                "consensus_pct": consensus,
                "ai1_view": cand.get("ai1_view", ""),
                "ai2_view": cand.get("ai2_view", ""),
                "win_rate_pct": setup["win_rate_pct"],
                "win_gauge": setup["win_gauge"],
                "expected_return_pct": setup["expected_return_pct"],
                "sample_stats": setup["sample_stats"],
                "price": tech_snapshot["price"],
                "change_pct": tech_snapshot["change_pct"],
                "volume": tech_snapshot["volume"],
                "vol_ratio": tech_snapshot["vol_ratio"],
                "ma5": tech_snapshot["ma5"],
                "ma20": tech_snapshot["ma20"],
                "bias_ma20": tech_snapshot["bias_ma20"],
                "action_tag": setup["action_tag"],
                "entry_zone": setup["entry_zone"],
                "stop_loss": setup["stop_loss"],
                "risk_pct": setup["risk_pct"],
                "target_1": setup["target_1"],
                "target_2": setup["target_2"],
                "target_gain_pct": setup["target_gain_pct"],
                "risk_reward_ratio": setup["risk_reward_ratio"],
                "reasons": cand["reasons"][:2],
                "related_news": cand["related_news_titles"][:2],
                "horizon": cand["horizon"],
                "is_valid_trade": setup["is_valid_trade"]
            })

        # 依照綜合評分由高至低排序
        evaluated_picks.sort(key=lambda x: x["total_score"], reverse=True)

        # 檢查本分鐘新偵測快訊
        breaking_news = [n for n in news_items if n.get("is_breaking_news")]

        # 將 Top 3 首選自動註冊進自我學習追蹤器
        for p in evaluated_picks[:3]:
            if p["is_valid_trade"]:
                self.learning_engine.register_new_signal(p)

        # 盤後/即時自我覆盤成敗檢查
        learning_review = self.learning_engine.update_and_review(self.market_data)

        logger.info(">>> 步驟 4/4: 選股與自我覆盤學習完成！")
        return {
            "timestamp": news_items[0]["published_at"] if news_items else "",
            "total_news_analyzed": len(news_items),
            "breaking_news_count": len(breaking_news),
            "breaking_news_list": breaking_news[:3],
            "total_stocks_evaluated": len(evaluated_picks),
            "top_3_picks": evaluated_picks[:3],
            "top_picks": evaluated_picks[:top_k],
            "raw_picks": evaluated_picks,
            "learning_review": learning_review
        }

    def diagnose_single_stock(self, symbol: str) -> Optional[Dict[str, Any]]:
        """針對特定台股進行客製化時事與量價即時健檢"""
        news_items = self.news_fetcher.get_latest_news()
        ai_candidates = self.ai_analyzer.analyze_news_batch(news_items)
        
        matched_cand = next((c for c in ai_candidates if c["symbol"] == symbol), None)
        tech_snapshot = self.market_data.get_stock_technical_snapshot(symbol)
        theme = matched_cand.get("theme", "台股熱門題材") if matched_cand else "台股熱門題材"
        consensus = matched_cand.get("consensus_pct", 80.0) if matched_cand else 75.0
        setup = TechnicalFilter.evaluate_setup(tech_snapshot, theme=theme, dual_ai_consensus=consensus)

        catalyst_score = matched_cand["catalyst_score"] if matched_cand else 40.0
        reasons = matched_cand["reasons"] if matched_cand else ["近期尚無高熱度即時新聞直接點名，需留意大盤板塊輪動"]

        return {
            "symbol": symbol,
            "name": tech_snapshot["name"],
            "tech": tech_snapshot,
            "setup": setup,
            "catalyst_score": catalyst_score,
            "reasons": reasons
        }

