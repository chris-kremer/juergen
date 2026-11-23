"""Visible disclosures for mixed return bases and unknown-date history scope."""
from contextlib import nullcontext
from unittest.mock import MagicMock

import pandas as pd
import pytest

import config
import portfolio_dashboard as dashboard
import report_generator
from price_fetcher import PriceFetcher


@pytest.mark.parametrize("mode, eur_basis, usd_basis, expected", [
    ("since_purchase", None, 100, True),
    ("daily", None, 100, False),
    ("since_purchase", 90, 100, False),
    ("since_purchase", None, None, False),
])
def test_heatmap_visibly_discloses_mixed_return_bases(
    monkeypatch, mode, eur_basis, usd_basis, expected
):
    ui = MagicMock()
    ui.columns.return_value = [nullcontext(), nullcontext()]
    ui.radio.return_value = mode
    ui.checkbox.return_value = True
    monkeypatch.setattr(dashboard, "st", ui)
    position = next(s.copy() for s in config.STOCKS if s["symbol"] == "ANT")
    position.update(cost_basis_eur=eur_basis, cost_basis_usd=usd_basis)
    # The no-cost case has no valid return calculation; keep this test about rendering.
    if eur_basis is None and not usd_basis:
        monkeypatch.setattr(dashboard, "build_portfolio_heatmap_rows", lambda *a, **kw: [])
    view = dashboard.PortfolioDashboard(PriceFetcher())
    monkeypatch.setattr(view, "_plotly_chart", lambda *a, **kw: None)
    view.show_portfolio_heatmap([position], {"username": "user"}, "en")
    captions = [call.args[0] for call in ui.caption.call_args_list]
    disclosures = [text for text in captions if "USD-cost returns" in text]
    assert bool(disclosures) is expected
    if expected:
        assert all(term in disclosures[0] for term in (
            "ANT/SKHY", "valuation FX", "EUR-basis holdings", "aggregate mixes bases"
        ))
        assert ui.caption.call_count >= 2


@pytest.mark.parametrize("excluded", [True, False])
def test_dashboard_visibly_explains_historical_scope(monkeypatch, excluded):
    ui = MagicMock()
    ui.session_state = {}
    monkeypatch.setattr(dashboard, "st", ui)
    fetcher = MagicMock()
    fetcher.get_portfolio_value.return_value = 100
    fetcher.get_user_daily_change_value.return_value = 0
    view = dashboard.PortfolioDashboard(fetcher)
    monkeypatch.setattr(view, "_calculate_tranche_returns", lambda *a: (100, 0, 0))
    monkeypatch.setattr(view, "_get_user_historical_portfolio_peak", lambda *a: None)
    monkeypatch.setattr(view, "_show_metric_grid", lambda *a: None)
    for name in (
        "show_portfolio_heatmap", "show_investment_tranches", "show_all_users_overview",
        "show_admin_aum_chart", "show_tax_overview", "show_login_statistics",
        "show_historical_performance_chart", "show_individual_stock_performance_chart",
        "show_returns_chart", "show_portfolio_breakdown", "show_holdings_table",
    ):
        monkeypatch.setattr(view, name, lambda *a, **kw: None)
    position = {"symbol": "ANT", "price": 100}
    if excluded:
        position["history_policy"] = "exclude_unknown_execution_date"
    view.show_dashboard({"username": "user"}, [position], [])
    notices = [call.args[0] for call in ui.info.call_args_list]
    assert bool(notices) is excluded
    if excluded:
        assert all(term in notices[0] for term in (
            "Historical charts exclude ANT/SKHY", "associated cash correction",
            "until execution dates", "current values include them",
        ))


@pytest.mark.parametrize("note", [
    "Legacy historical composition only; ANT/SKHY and their USD cash correction excluded due to unknown execution dates.",
    None,
])
def test_pdf_renders_history_scope_next_to_highlights(monkeypatch, note):
    calls = []

    class RecordingPDF(report_generator.FPDF):
        def cell(self, w, h=0, text="", *args, **kwargs):
            calls.append(("cell", text))
            return super().cell(w, h, text, *args, **kwargs)

        def multi_cell(self, w, h, text="", *args, **kwargs):
            calls.append(("multi_cell", text, w, self.get_x(), self.l_margin))
            return super().multi_cell(w, h, text, *args, **kwargs)

    monkeypatch.setattr(report_generator, "FPDF", RecordingPDF)
    generator = report_generator.AnnualReportGenerator(PriceFetcher())
    monkeypatch.setattr(generator, "_build_performance_chart", lambda *a: None)
    monkeypatch.setattr(generator, "_build_inflation_chart", lambda *a: None)
    monkeypatch.setattr(generator, "_embed_chart", lambda pdf, *a, **kw: pdf)
    context = {
        "summary": dict.fromkeys(("portfolio_return_pct", "real_return_pct", "index_return_pct", "dax_return_pct"), 0),
        "index_symbol": "EUNL.DE", "dax_symbol": "LYY7.DE", "payments": [],
        "breakdown": pd.DataFrame(), "monthly_returns": pd.DataFrame(),
    }
    if note is not None:
        context["history_scope_note"] = note
    result = generator._render_pdf({"username": "user"}, context, 2025)
    assert result.startswith(b"%PDF-")
    rendered = [call for call in calls if call[0] == "multi_cell"]
    if note is None:
        assert not rendered
    else:
        assert rendered and rendered[0][1] == note
        assert rendered[0][2] == 0
        assert rendered[0][3] == pytest.approx(rendered[0][4])
        heading = calls.index(("cell", "Performance Highlights"))
        assert calls.index(rendered[0]) == heading + 1
        rendered[0][1].encode("ascii")
