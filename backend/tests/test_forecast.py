import unittest
from unittest.mock import patch

from model.forecast import _fh_stock_candles


class StockCandleTests(unittest.TestCase):
    @patch("model.forecast._fh_get")
    def test_candles_preserve_prices_and_utc_dates(self, get):
        get.return_value = {
            "s": "ok",
            "c": [120.0, 125.5],
            "t": [1704067200, 1704153600],
        }
        result = _fh_stock_candles("TEST", 0, 1704153600)
        self.assertEqual(result.tolist(), [120.0, 125.5])
        self.assertEqual(
            result.index.strftime("%Y-%m-%d").tolist(),
            ["2024-01-01", "2024-01-02"],
        )
        self.assertIsNone(result.index.tz)

    @patch("model.forecast._fh_get")
    def test_mismatched_candles_are_rejected(self, get):
        get.return_value = {"s": "ok", "c": [120.0], "t": [1, 2]}
        self.assertTrue(_fh_stock_candles("TEST", 0, 2).empty)

    @patch("model.forecast._fh_get")
    def test_no_data_returns_empty_series(self, get):
        get.return_value = {"s": "no_data"}
        self.assertTrue(_fh_stock_candles("TEST", 0, 2).empty)


if __name__ == "__main__":
    unittest.main()
