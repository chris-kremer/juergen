import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from portfolio_dashboard import (
    PortfolioDashboard,
    calculate_historical_portfolio_peak,
    is_portfolio_all_time_high,
)


class PortfolioAllTimeHighTests(unittest.TestCase):
    def test_calculates_peak_from_synchronized_holdings_and_cash(self):
        dates = pd.to_datetime(["2026-08-06", "2026-08-07"])
        histories = {
            "AAA": pd.DataFrame({"Close": [10.0, 12.0]}, index=dates),
            "BBB": pd.DataFrame({"Close": [20.0, 19.0]}, index=dates),
        }
        stocks = [
            {"symbol": "AAA", "quantity": 2.0},
            {"symbol": "BBB", "quantity": 1.0},
            {"symbol": "CASH", "quantity": 5.0},
        ]

        # Daily totals are 45 and 48.
        self.assertEqual(calculate_historical_portfolio_peak(histories, stocks), 48.0)

    def test_requires_complete_history_to_avoid_false_highs(self):
        histories = {"AAA": pd.DataFrame({"Close": [10.0]})}
        stocks = [
            {"symbol": "AAA", "quantity": 1.0},
            {"symbol": "BBB", "quantity": 1.0},
        ]
        self.assertIsNone(calculate_historical_portfolio_peak(histories, stocks))

    def test_all_time_high_requires_current_value_to_reach_peak(self):
        self.assertTrue(is_portfolio_all_time_high(100.0, 100.0))
        self.assertTrue(is_portfolio_all_time_high(101.0, 100.0))
        self.assertFalse(is_portfolio_all_time_high(99.99, 100.0))
        self.assertFalse(is_portfolio_all_time_high(100.0, None))

    def test_all_time_high_metric_renders_clickable_full_screen_confetti_trigger(self):
        dashboard = PortfolioDashboard(price_fetcher=MagicMock())
        with patch("portfolio_dashboard.st.markdown") as markdown:
            dashboard._show_metric_grid([
                {
                    "label": "Ihr Portfolio-Wert",
                    "value": "€260,000.00",
                    "delta": "Allzeithoch",
                    "all_time_high": True,
                }
            ])

        html = markdown.call_args.args[0]
        self.assertIn("metric-card--all-time-high", html)
        self.assertIn('tabindex="0"', html)
        self.assertIn("ath-confetti-layer", html)


if __name__ == "__main__":
    unittest.main()
