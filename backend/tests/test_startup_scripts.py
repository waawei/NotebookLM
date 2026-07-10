from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class StartupScriptTests(unittest.TestCase):
    def test_windows_start_scripts_wait_for_backend_health_before_frontend(self):
        scripts = [
            ROOT / "start.bat",
            ROOT / "frontend" / "start_frontend.bat",
            ROOT / "start-frontend-clean.bat",
        ]

        for script in scripts:
            with self.subTest(script=script):
                content = script.read_text(encoding="utf-8").lower()
                self.assertIn("127.0.0.1:8000/health", content)
                self.assertIn("backend is ready", content)

    def test_service_scripts_use_their_own_directory(self):
        scripts = [
            ROOT / "backend" / "start_backend.bat",
            ROOT / "frontend" / "start_frontend.bat",
        ]

        for script in scripts:
            with self.subTest(script=script):
                content = script.read_text(encoding="utf-8").lower()
                self.assertIn('cd /d "%~dp0"', content)


if __name__ == "__main__":
    unittest.main()
