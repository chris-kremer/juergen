import unittest
from unittest.mock import patch

import plotly.graph_objects as go

from portfolio_dashboard import (
    PortfolioDashboard,
    build_confirmed_capital_series,
    build_portfolio_heatmap_rows,
    calculate_tax_simulation,
    get_confirmed_portfolio_capital_events,
)


class ChartInteractionTests(unittest.TestCase):
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

        simulation = calculate_tax_simulation(stocks, tax_rate=0.25)

        self.assertEqual(simulation["gross_value_eur"], 250)
        self.assertEqual(simulation["cost_basis_eur"], 150)
        self.assertEqual(simulation["unrealized_gain_eur"], 100)
        self.assertEqual(simulation["estimated_tax_eur"], 25)
        self.assertEqual(simulation["net_liquidation_value_eur"], 225)
        self.assertAlmostEqual(simulation["gross_up_reference_eur"], 250 / 0.75)

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
        )

        self.assertEqual(simulation["gross_value_eur"], 40)
        self.assertEqual(simulation["cost_basis_eur"], 20)
        self.assertEqual(simulation["estimated_tax_eur"], 5)
        self.assertEqual(simulation["net_liquidation_value_eur"], 35)

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
