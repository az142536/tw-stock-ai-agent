"""
技術面與量價風控過濾模組 (Technical & Risk Control Filter)
專業台股操盤三大防護機制：
1. 均線與多頭型態驗證：確認站上月線(20MA)，排除空頭反彈或主力誘多出貨
2. 量能爆發確認：確認當日成交量突破5日均量(1.25倍以上)，有真實買盤推動
3. 月線乖離率(BIAS)防追高：乖離率超過12%亮起紅燈警示，嚴禁追高
4. 風報比精算：自動計算進場區間、防守停損點、第一波段目標與第二目標，確保風報比 >= 1.8:1
"""

from typing import Dict, Any, Tuple
from config import Config
from knowledge_graph import get_theme_backtest_stats

class TechnicalFilter:
    """技術面與交易風險過濾器 (含歷史回測成功率精算)"""

    @staticmethod
    def evaluate_setup(tech_data: Dict[str, Any], theme: str = "台股綜合題材", dual_ai_consensus: float = 85.0) -> Dict[str, Any]:
        """
        評估個股技術線型並生成具體交易計畫（進場價、停損價、目標價、風報比、勝率成功率試算）
        """
        price = tech_data["price"]
        ma5 = tech_data["ma5"]
        ma20 = tech_data["ma20"]
        bias_ma20 = tech_data["bias_ma20"]
        vol_ratio = tech_data["vol_ratio"]
        change_pct = tech_data["change_pct"]
        is_bullish = tech_data["is_bullish"]

        # 1. 判斷防守停損價 (以月線 MA20 或跌破 4.5% 為基準防守線)
        stop_loss_candidate = round(ma20 * 0.985, 1)
        risk_pct = round(((price - stop_loss_candidate) / price) * 100.0, 2)
        
        if risk_pct > 7.0:
            stop_loss = round(price * (1.0 - Config.DEFAULT_STOP_LOSS_PCT), 1)
            risk_pct = 5.0
        else:
            stop_loss = stop_loss_candidate

        risk_amount = max(0.1, price - stop_loss)

        # 2. 推算波段獲利目標價與獲利空間
        target_1 = round(price + (risk_amount * 2.1), 1)
        target_2 = round(price * 1.15, 1)
        reward_amount = target_1 - price
        risk_reward_ratio = round(reward_amount / risk_amount, 2)
        target_gain_pct = round(((target_1 - price) / price) * 100.0, 2)

        # 3. 建議進場點位區間
        entry_low = round(min(price, max(ma5, price * 0.985)), 1)
        entry_high = round(price * 1.005, 1)

        # 4. 技術面量價綜合評分 (0 ~ 35 分)
        tech_score = 0.0

        if is_bullish:
            tech_score += 15.0
        elif price >= ma20:
            tech_score += 8.0

        if vol_ratio >= 1.5:
            tech_score += 12.0
        elif vol_ratio >= Config.VOLUME_SPIKE_RATIO:
            tech_score += 9.0
        elif vol_ratio >= 1.0:
            tech_score += 5.0

        if 50.0 <= tech_data["kd_k"] <= 85.0:
            tech_score += 8.0
        elif tech_data["kd_k"] > 85.0:
            tech_score += 4.0

        # 5. 精算預估成功率 (Win Rate %) 與數學期望值 (EV)
        # 讀取該題材歷史同型態波段真實回測統計
        theme_stats = get_theme_backtest_stats(theme)
        base_win_rate = theme_stats["base_win_rate"]
        sample_count = theme_stats["sample_count"]
        win_count = theme_stats["win_count"]
        avg_profit = theme_stats["avg_profit_pct"]

        # 動態校準勝率
        calibrated_win_rate = base_win_rate
        if is_bullish:
            calibrated_win_rate += 2.5
        else:
            calibrated_win_rate -= 6.0

        if vol_ratio >= 1.5:
            calibrated_win_rate += 3.0
        elif vol_ratio >= Config.VOLUME_SPIKE_RATIO:
            calibrated_win_rate += 1.5
        elif vol_ratio < 1.0:
            calibrated_win_rate -= 4.5

        if 2.0 <= bias_ma20 <= 8.0:
            calibrated_win_rate += 2.0  # 甜蜜剛起漲區
        elif bias_ma20 > Config.MAX_BIAS_20:
            calibrated_win_rate -= 16.0 # 乖離嚴重過熱，勝率大幅重挫

        if dual_ai_consensus >= 88.0:
            calibrated_win_rate += 2.5

        calibrated_win_rate = round(max(35.0, min(94.8, calibrated_win_rate)), 1)

        # 期望值 EV % = (勝率 * 目標獲利%) - ((1 - 勝率) * 承擔風險%)
        expected_return_pct = round(
            ((calibrated_win_rate / 100.0) * target_gain_pct) - (((100.0 - calibrated_win_rate) / 100.0) * risk_pct), 2
        )

        # 勝率進度條圖形 (10格)
        filled_bars = int(round(calibrated_win_rate / 10.0))
        win_gauge = "█" * filled_bars + "░" * (10 - filled_bars)

        # 6. 綜合策略行動標籤
        if bias_ma20 > Config.MAX_BIAS_20:
            action_tag = "⚠️ 過熱警戒 (乖離過大勿追高，靜待回測月線)"
            signal_color = "YELLOW"
            is_valid_trade = False
        elif is_bullish and vol_ratio >= Config.VOLUME_SPIKE_RATIO and change_pct >= 2.0:
            action_tag = "🔥 爆量攻擊買點 (時事利多與多頭量價共振)"
            signal_color = "GREEN"
            is_valid_trade = True
        elif price >= ma20 and vol_ratio >= 1.0:
            action_tag = "📈 拉回月線支撐布局 (低接風報比優)"
            signal_color = "CYAN"
            is_valid_trade = True
        else:
            action_tag = "⏳ 區間震盪觀察 (等待放量表態突破)"
            signal_color = "WHITE"
            is_valid_trade = False

        return {
            "tech_score": round(tech_score, 1),
            "action_tag": action_tag,
            "signal_color": signal_color,
            "is_valid_trade": is_valid_trade,
            "entry_zone": f"{entry_low} ~ {entry_high}",
            "stop_loss": stop_loss,
            "risk_pct": risk_pct,
            "target_1": target_1,
            "target_2": target_2,
            "target_gain_pct": target_gain_pct,
            "risk_reward_ratio": risk_reward_ratio,
            "win_rate_pct": calibrated_win_rate,
            "win_gauge": win_gauge,
            "expected_return_pct": expected_return_pct,
            "sample_stats": f"歷史同型態 {sample_count} 次觸發，{win_count} 次成功獲利 (平均獲利 +{avg_profit}%)"
        }

