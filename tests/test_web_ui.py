import unittest
from pathlib import Path

from web.app import app


REPO_ROOT = Path(__file__).resolve().parents[1]


class HomePageUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True
        cls.client = app.test_client()

    def test_homepage_contains_guided_flow_shell(self):
        response = self.client.get("/")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        for snippet in (
            'data-theme="light"',
            'id="themeToggle"',
            'id="stepUpload"',
            'id="stepReview"',
            'id="stepResults"',
            'id="reviewPanel"',
            'id="resultsPanel"',
            'id="trustSection"',
            'id="classesGrid"',
        ):
            self.assertIn(snippet, html)

    def test_stylesheet_defines_theme_and_accessibility_hooks(self):
        css = (REPO_ROOT / "web" / "static" / "css" / "style.css").read_text(encoding="utf-8")

        for snippet in (
            '[data-theme="dark"]',
            ".theme-toggle",
            ".flow-step.is-active",
            ".inline-error",
            ":focus-visible",
            "@media (prefers-reduced-motion: reduce)",
        ):
            self.assertIn(snippet, css)

    def test_script_defines_theme_and_flow_helpers(self):
        js = (REPO_ROOT / "web" / "static" / "js" / "main.js").read_text(encoding="utf-8")

        for snippet in (
            "const THEME_KEY = 'dermai-theme';",
            "function applyTheme(theme)",
            "function setFlowState(state)",
            "function showInlineError(message)",
            "themeToggle.addEventListener('click'",
            "localStorage.setItem(THEME_KEY, theme);",
        ):
            self.assertIn(snippet, js)


if __name__ == "__main__":
    unittest.main()
