import unittest

from translations import get_text
from ui_theme import build_app_css, build_dashboard_header, build_footer, build_login_intro


class UIThemeTests(unittest.TestCase):
    def test_theme_removes_streamlit_branding_without_hiding_sidebar_controls(self):
        css = build_app_css()
        self.assertIn("#MainMenu", css)
        self.assertIn('[data-testid="stStatusWidget"]', css)
        self.assertIn("footer", css)
        self.assertNotIn('[data-testid="stHeader"] { display: none', css)

    def test_dashboard_header_is_branded_and_escapes_user_content(self):
        html = build_dashboard_header('<Kremer & Co>')
        self.assertIn("PRIVATE PORTFOLIO", html)
        self.assertIn("Kremer &amp; Co", html)
        self.assertNotIn("<Kremer", html)
        self.assertIn("portfolio-hero", html)
        self.assertIn("PRIVAT PORTFOLIO", build_dashboard_header("kremer", "de"))

    def test_footer_is_quiet_and_localized(self):
        self.assertIn("Private Portfolio", build_footer("en"))
        self.assertIn("Privates Portfolio", build_footer("de"))
        self.assertIn("Yahoo Finance", build_footer("de"))

    def test_metric_cards_use_one_consistent_surface(self):
        css = build_app_css()
        self.assertNotIn(".metric-card:first-child", css)
        self.assertNotIn(".metric-card:nth-child(2)", css)

    def test_native_metric_cards_reserve_equal_height_for_optional_deltas(self):
        css = build_app_css()
        self.assertIn('[data-testid="stMetric"] {\n    min-height: 141px;', css)

    def test_login_is_minimal_and_has_empty_placeholders(self):
        intro = build_login_intro()
        self.assertIn("Portfolio Login", intro)
        self.assertNotIn("↗", intro)
        self.assertNotIn("Sign in", intro)
        self.assertEqual(get_text("username"), "User")
        self.assertEqual(get_text("enter_username"), "")
        self.assertEqual(get_text("enter_password"), "")


if __name__ == "__main__":
    unittest.main()
