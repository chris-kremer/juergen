"""Contract test for the temporary display-only Kremer annotation."""
import ast
from pathlib import Path
import unittest


class TemporaryValueLabelTest(unittest.TestCase):
    def test_headline_annotation_is_kremer_only_and_display_only(self):
        tree = ast.parse(Path(__file__).with_name('portfolio_dashboard.py').read_text())
        dashboard = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'show_dashboard')
        call = next(n for n in ast.walk(dashboard) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == '_show_metric_grid')
        metric = call.args[0].elts[0]
        value = next(v for k, v in zip(metric.keys, metric.values) if isinstance(k, ast.Constant) and k.value == 'value')
        expr = compile(ast.Expression(value), '<headline>', 'eval')
        for username in ('kremer', 'annika', 'christian', 'juergen'):
            context = {'user': {'username': username}, 'user_portfolio_value': 123456.78, 'lang': 'de', 'format_currency': lambda amount, lang: f'{amount:.2f} EUR'}
            result = eval(expr, context)
            self.assertEqual(result, '123456.78 EUR' + (' (+ 10.000)' if username == 'kremer' else ''))
            self.assertEqual(context['user_portfolio_value'], 123456.78)


if __name__ == '__main__':
    unittest.main()
