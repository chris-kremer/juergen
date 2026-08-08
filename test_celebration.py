import unittest

from celebration import (
    build_annika_2500_celebration_html,
    build_doubling_celebration_html,
    build_doubling_message,
    resolve_doubling_celebration_return,
    should_show_annika_2500_celebration,
    should_show_doubling_celebration,
)


class DoublingCelebrationTests(unittest.TestCase):
    def test_shows_for_kremer_at_lower_boundary(self):
        self.assertTrue(should_show_doubling_celebration("kremer", 100.0))

    def test_shows_for_kremer_at_upper_boundary(self):
        self.assertTrue(should_show_doubling_celebration("kremer", 105.0))

    def test_hides_below_the_window(self):
        self.assertFalse(should_show_doubling_celebration("kremer", 99.99))

    def test_hides_above_the_window(self):
        self.assertFalse(should_show_doubling_celebration("kremer", 105.01))

    def test_hides_for_other_accounts(self):
        self.assertFalse(should_show_doubling_celebration("juergen", 102.0))

    def test_message_is_german_and_includes_the_live_return(self):
        message = build_doubling_message(102.4)
        self.assertIn("verdoppelt", message)
        self.assertIn("102,4 %", message)

    def test_html_is_an_all_out_celebration(self):
        html = build_doubling_celebration_html(102.4)
        self.assertIn("100 % GEKNACKT", html)
        self.assertIn("DOPPELT HÄLT BESSER", html)
        self.assertIn("102,4 %", html)
        self.assertIn("celebration-confetti", html)
        self.assertIn("prefers-reduced-motion", html)

    def test_kremer_can_replay_a_safe_preview_below_the_real_threshold(self):
        self.assertEqual(
            resolve_doubling_celebration_return("kremer", 98.9, preview_requested=True),
            102.4,
        )

    def test_real_milestone_uses_the_live_return(self):
        self.assertEqual(
            resolve_doubling_celebration_return("kremer", 101.2, preview_requested=False),
            101.2,
        )

    def test_preview_is_not_available_to_other_accounts(self):
        self.assertIsNone(
            resolve_doubling_celebration_return("juergen", 98.9, preview_requested=True)
        )

    def test_annika_2500_milestone_has_a_bounded_window(self):
        self.assertFalse(should_show_annika_2500_celebration("annika", 2499.99))
        self.assertTrue(should_show_annika_2500_celebration("annika", 2500.0))
        self.assertTrue(should_show_annika_2500_celebration("annika", 2550.0))
        self.assertTrue(should_show_annika_2500_celebration("annika", 2600.0))
        self.assertFalse(should_show_annika_2500_celebration("annika", 2600.01))
        self.assertFalse(should_show_annika_2500_celebration("kremer", 2550.0))

    def test_annika_html_names_her_and_formats_the_live_value(self):
        html = build_annika_2500_celebration_html(2550.0)
        self.assertIn("2.500 € GEKNACKT", html)
        self.assertIn("ANNIKA", html)
        self.assertIn("2.550,00 €", html)
        self.assertIn("celebration-confetti", html)


if __name__ == "__main__":
    unittest.main()
