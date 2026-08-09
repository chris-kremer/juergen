import unittest
from unittest.mock import patch

import plotly.graph_objects as go

from portfolio_dashboard import PortfolioDashboard


class ChartInteractionTests(unittest.TestCase):
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
