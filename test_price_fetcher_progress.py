import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from price_fetcher import PriceFetcher


class PriceFetcherProgressTests(unittest.TestCase):
    def test_progress_ui_is_removed_after_prices_finish_loading(self):
        progress_container = MagicMock()
        progress_bar = MagicMock()
        status_text = MagicMock()
        history = pd.DataFrame({"Close": [42.0], "Open": [41.0]})
        stocks = [
            {"symbol": "TEST", "price": 40.0, "quantity": 1.0},
            {"symbol": "CASH", "price": 1.0, "quantity": 10.0},
        ]

        with (
            patch("price_fetcher.st.container", return_value=progress_container),
            patch("price_fetcher.st.progress", return_value=progress_bar),
            patch("price_fetcher.st.empty", return_value=status_text),
            patch("price_fetcher._fetch_yfinance_history_uncached", return_value=history),
        ):
            PriceFetcher().fetch_stock_prices(
                stocks,
                show_progress=True,
                use_cached_history=False,
            )

        progress_bar.empty.assert_called_once_with()
        status_text.empty.assert_called_once_with()
        progress_container.empty.assert_called_once_with()
        rendered_statuses = [str(call.args[0]) for call in status_text.text.call_args_list]
        self.assertFalse(any("Completed" in status for status in rendered_statuses))


if __name__ == "__main__":
    unittest.main()
