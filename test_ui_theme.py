import unittest

from ui_theme import build_app_css, build_dashboard_header, build_footer


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

    def test_footer_is_quiet_and_localized(self):
        self.assertIn("Private Portfolio", build_footer("en"))
        self.assertIn("Privates Portfolio", build_footer("de"))
        self.assertIn("Yahoo Finance", build_footer("de"))


if __name__ == "__main__":
    unittest.main()
