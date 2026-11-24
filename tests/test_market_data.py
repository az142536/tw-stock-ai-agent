import unittest
from unittest.mock import patch

from config import Config
from tw_market_data import TaiwanMarketData


class TaiwanMarketDataTests(unittest.TestCase):
    def setUp(self):
        Config.ENABLE_DEMO_FALLBACK = False

    @patch.object(TaiwanMarketData, "_fetch_yahoo_history", return_value=None)
    @patch.object(TaiwanMarketData, "_fetch_yahoo_finance_quote", return_value=None)
    @patch.object(TaiwanMarketData, "_refresh_openapi_quotes")
    def test_unavailable_data_is_explicit(self, _refresh, _quote, _history):
        market = TaiwanMarketData()
        snapshot = market.get_stock_technical_snapshot("9999")

        self.assertEqual(snapshot["data_source"], "UNAVAILABLE")
        self.assertEqual(snapshot["price"], 0.0)
        self.assertFalse(snapshot["is_bullish"])

    @patch.object(TaiwanMarketData, "_refresh_openapi_quotes")
    def test_ma_and_bias_use_real_history(self, _refresh):
        closes = [100 + i for i in range(30)]
        points = [
            {
                "close": close,
                "volume": 1000000,
                "high": close + 2,
                "low": close - 2,
                "open": close - 1,
            }
            for close in closes
        ]
        market = TaiwanMarketData()
        market.openapi_market_quotes = {
            "2330": {
                "symbol": "2330",
                "name": "台積電",
                "price": 129.0,
                "change_pct": 1.0,
                "volume": 1000,
                "market": "TWSE",
            }
        }

        with patch.object(
            market,
            "_fetch_yahoo_history",
            return_value={"points": points, "source": "Yahoo_.TW"},
        ):
            snapshot = market.get_stock_technical_snapshot("2330")

        self.assertTrue(snapshot["ma20"] > 0)
        self.assertTrue(snapshot["ma60"] > 0)
        self.assertTrue(snapshot["data_source"].startswith("Historical_"))
        self.assertGreater(snapshot["bias_ma20"], 0)
        self.assertEqual(snapshot["vol_ma5"], 1000)


if __name__ == "__main__":
    unittest.main()
