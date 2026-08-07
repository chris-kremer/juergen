import unittest

from celebration import build_doubling_message, should_show_doubling_celebration


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


if __name__ == "__main__":
    unittest.main()
