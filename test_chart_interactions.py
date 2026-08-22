import unittest
from unittest.mock import MagicMock, patch

import plotly.graph_objects as go
import pandas as pd

from portfolio_dashboard import (
    BENCHMARK_LABEL,
    PortfolioDashboard,
    _is_benchmark,
    allocate_tax_by_earnings,
    build_confirmed_capital_series,
    build_portfolio_heatmap_rows,
    calculate_tax_simulation,
    get_confirmed_portfolio_capital_events,
    get_confirmed_user_investment,
)
from config import STOCKS
from translations import get_text


class ChartInteractionTests(unittest.TestCase):
    def test_historical_chart_uses_dax_as_its_benchmark(self):
        benchmark_stocks = [stock for stock in STOCKS if _is_benchmark(stock)]

        self.assertEqual(BENCHMARK_LABEL, "DAX")
        self.assertEqual([stock["symbol"] for stock in benchmark_stocks], ["LYY7.DE"])
        self.assertEqual(get_text("portfolio_vs_benchmark", "en"), "Portfolio vs DAX Benchmark")
        self.assertEqual(get_text("portfolio_vs_benchmark", "de"), "Portfolio vs DAX Benchmark")

    def test_history_window_uses_latest_finite_close(self):
        dashboard = PortfolioDashboard(price_fetcher=MagicMock())
        history = pd.DataFrame(
            {"Close": [100.0, 104.0, float("nan")]},
            index=pd.to_datetime(["2026-08-20", "2026-08-21", "2026-08-22"]),
        )

        price = dashboard._get_price_from_history_window(
            history,
            pd.Timestamp("2026-08-18"),
            pd.Timestamp("2026-08-24"),
        )

        self.assertEqual(price, 104.0)

    def test_tax_simulation_taxes_gains_not_the_entire_asset_value(self):
        stocks = [
            {
                "quantity": 10,
                "price": 15,
                "current_price": 20,
                "cost_basis_eur": 100,
            },
            {
                "quantity": 50,
                "price": 1,
                "current_price": 1,
                "cost_basis_eur": 50,
            },
        ]

        simulation = calculate_tax_simulation(
            stocks,
            tax_rate=0.25,
            invested_capital_eur=150,
        )

        self.assertEqual(simulation["gross_value_eur"], 250)
        self.assertEqual(simulation["cost_basis_eur"], 150)
        self.assertEqual(simulation["taxable_gain_eur"], 100)
        self.assertEqual(simulation["economic_gain_eur"], 100)
        self.assertEqual(simulation["estimated_tax_eur"], 25)
        self.assertEqual(simulation["net_liquidation_value_eur"], 225)
        self.assertEqual(simulation["tax_equivalent_value_eur"], 250)

    def test_tax_equivalent_grosses_up_only_gain_above_investment(self):
        stocks = [{
            "quantity": 10,
            "price": 20,
            "cost_basis_eur": 160,
        }]

        simulation = calculate_tax_simulation(
            stocks,
            tax_rate=0.25,
            invested_capital_eur=100,
        )

        self.assertEqual(simulation["gross_value_eur"], 200)
        self.assertEqual(simulation["economic_gain_eur"], 100)
        self.assertEqual(simulation["estimated_tax_eur"], 10)
        self.assertEqual(simulation["net_liquidation_value_eur"], 190)
        self.assertEqual(simulation["tax_equivalent_value_eur"], 220)
        equivalent_net = 220 - 0.25 * (220 - 100)
        self.assertEqual(equivalent_net, 190)

    def test_tax_simulation_allocates_the_pool_pro_rata(self):
        stocks = [{
            "quantity": 10,
            "price": 20,
            "cost_basis_eur": 100,
        }]

        simulation = calculate_tax_simulation(
            stocks,
            user_percentage=0.2,
            tax_rate=0.25,
            invested_capital_eur=30,
        )

        self.assertEqual(simulation["gross_value_eur"], 40)
        self.assertEqual(simulation["cost_basis_eur"], 20)
        self.assertEqual(simulation["pooled_tax_share_eur"], 5)
        self.assertEqual(simulation["estimated_tax_eur"], 5)
        self.assertEqual(simulation["net_liquidation_value_eur"], 35)
        self.assertAlmostEqual(simulation["tax_equivalent_value_eur"], 30 + 5 / 0.75)

    def test_tax_liability_is_allocated_proportionally_to_earnings(self):
        allocations = allocate_tax_by_earnings(
            30,
            {"one": 20, "two": 80, "loss": -10},
        )

        self.assertEqual(allocations["one"], 6)
        self.assertEqual(allocations["two"], 24)
        self.assertEqual(allocations["loss"], 0)
        self.assertEqual(sum(allocations.values()), 30)

    def test_asset_basis_tax_is_split_by_user_earnings(self):
        stocks = [{
            "quantity": 1,
            "price": 100000,
            "cost_basis_eur": 50000,
        }]
        pooled = calculate_tax_simulation(
            stocks,
            tax_rate=0.25,
            invested_capital_eur=40000,
        )
        allocations = allocate_tax_by_earnings(
            pooled["estimated_tax_eur"],
            {"user_1": 40000, "user_2": 20000},
        )
        user_1 = calculate_tax_simulation(
            stocks,
            user_percentage=0.5,
            tax_rate=0.25,
            invested_capital_eur=10000,
            allocated_tax_eur=allocations["user_1"],
        )

        self.assertEqual(pooled["estimated_tax_eur"], 12500)
        self.assertAlmostEqual(allocations["user_1"], 12500 * 2 / 3)
        self.assertAlmostEqual(allocations["user_2"], 12500 * 1 / 3)
        self.assertAlmostEqual(user_1["net_liquidation_value_eur"], 41666.6667, places=3)
        self.assertAlmostEqual(user_1["tax_equivalent_value_eur"], 52222.2222, places=3)

    def test_confirmed_user_investment_supports_owner_and_admin_totals(self):
        users = [
            {"username": "user"},
            {"username": "one", "payments": [{"date": "2026-01-01", "amount": 80}]},
            {"username": "two", "initial_investment": 20, "paid_date": "2025-01-01"},
        ]

        self.assertEqual(get_confirmed_user_investment("one", users), 80)
        self.assertEqual(get_confirmed_user_investment("two", users), 20)
        self.assertEqual(get_confirmed_user_investment("user", users), 100)

    def test_admin_capital_ledger_uses_payments_or_initial_but_not_both(self):
        users = [
            {"username": "user", "initial_investment": 999},
            {
                "username": "one",
                "initial_investment": 100,
                "payments": [
                    {"date": "2026-01-01", "amount": 100},
                    {"date": "2026-02-01", "amount": 20},
                ],
            },
            {
                "username": "two",
                "initial_investment": 50,
                "paid_date": "2025-01-01",
            },
        ]

        events = get_confirmed_portfolio_capital_events(users)

        self.assertEqual(sum(event["amount_eur"] for event in events), 170)
        self.assertEqual(len(events), 3)

    def test_admin_capital_series_nets_internal_transfers_by_month(self):
        users = [
            {
                "username": "one",
                "payments": [
                    {"date": "2026-02-01", "amount": 500},
                ],
            },
            {
                "username": "two",
                "payments": [
                    {"date": "2026-02-02", "amount": -500},
                ],
            },
        ]

        series = build_confirmed_capital_series(users, "2026-03-15")

        self.assertEqual(series.iloc[0]["Net Pay-ins"], 0)
        self.assertEqual(series.iloc[-1]["Cumulative Pay-ins"], 0)

    def test_heatmap_sizes_positions_by_user_value_and_colors_by_daily_return(self):
        stocks = [
            {
                "isin": "ONE",
                "symbol": "ONE",
                "name": "One",
                "industry": "Software",
                "quantity": 10,
                "price": 9,
                "current_price": 10,
                "previous_close": 8,
                "cost_basis_eur": 50,
            },
            {
                "isin": "CASH-EUR",
                "symbol": "CASH",
                "name": "Cash",
                "quantity": 40,
                "price": 1,
                "current_price": 1,
                "previous_close": 1,
                "cost_basis_eur": 40,
            },
        ]

        rows = build_portfolio_heatmap_rows(stocks, user_percentage=0.25)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["value_eur"], 25)
        self.assertEqual(rows[0]["performance_pct"], 25)
        self.assertEqual(rows[1]["industry"], "Cash")

    def test_heatmap_can_exclude_cash_and_use_cost_basis_return(self):
        stocks = [
            {
                "isin": "ONE",
                "symbol": "ONE",
                "name": "One",
                "industry": "Software",
                "quantity": 10,
                "price": 9,
                "current_price": 10,
                "previous_close": 8,
                "cost_basis_eur": 50,
            },
            {
                "isin": "CASH-EUR",
                "symbol": "CASH",
                "name": "Cash",
                "quantity": 40,
                "price": 1,
                "cost_basis_eur": 40,
            },
        ]

        rows = build_portfolio_heatmap_rows(
            stocks,
            include_cash=False,
            color_mode="since_purchase",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "ONE")
        self.assertEqual(rows[0]["performance_pct"], 100)

    def test_charts_keep_hover_but_disable_accidental_zoom_and_pan(self):
        dashboard = PortfolioDashboard.__new__(PortfolioDashboard)
        figure = go.Figure(go.Scatter(x=[1, 2], y=[3, 4]))

        with patch("portfolio_dashboard.st.plotly_chart") as render:
            dashboard._plotly_chart(figure)

        self.assertFalse(figure.layout.dragmode)
        self.assertTrue(figure.layout.xaxis.fixedrange)
        self.assertTrue(figure.layout.yaxis.fixedrange)

        config = render.call_args.kwargs["config"]
        self.assertFalse(config["displayModeBar"])
        self.assertFalse(config["scrollZoom"])
        self.assertFalse(config["doubleClick"])
        self.assertFalse(config["showAxisDragHandles"])
        self.assertFalse(config["showAxisRangeEntryBoxes"])
        self.assertFalse(config["editable"])
        self.assertFalse(config["staticPlot"])


if __name__ == "__main__":
    unittest.main()
