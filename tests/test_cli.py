import tempfile
import unittest
from pathlib import Path

from autozocalos import cli, config

GLYPHS = {0xF16D}


def fake_install(root: Path) -> Path:
    support = root / "Support Files"
    support.mkdir(parents=True)
    (support / "aerender.exe").write_bytes(b"")
    (support / "AfterFX.exe").write_bytes(b"")
    return support


def fake_templates(root: Path) -> Path:
    for spec in config.TEMPLATES.values():
        (root / spec["file"]).write_bytes(b"")
    return root


class PreflightTests(unittest.TestCase):
    def test_is_silent_when_everything_is_in_place(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            problems = cli.preflight(fake_install(root / "ae"), False, GLYPHS, fake_templates(root))
            self.assertEqual(problems, [])

    def test_reports_when_after_effects_is_not_installed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            problems = cli.preflight(None, False, GLYPHS, fake_templates(root))
            self.assertTrue(any("After Effects" in p for p in problems))

    def test_reports_a_missing_executable(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            support = fake_install(root / "ae")
            (support / "aerender.exe").unlink()
            problems = cli.preflight(support, False, GLYPHS, fake_templates(root))
            self.assertTrue(any("aerender.exe" in p for p in problems))

    def test_reports_when_after_effects_is_already_running(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            problems = cli.preflight(fake_install(root / "ae"), True, GLYPHS, fake_templates(root))
            self.assertTrue(any("abierto" in p.lower() for p in problems))

    def test_reports_a_missing_template_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            problems = cli.preflight(fake_install(root / "ae"), False, GLYPHS, root)
            self.assertTrue(any("rotulo.aepx" in p for p in problems))

    def test_reports_a_missing_font_awesome(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            problems = cli.preflight(fake_install(root / "ae"), False, set(), fake_templates(root))
            self.assertTrue(any("Awesome" in p for p in problems))


class StatusTests(unittest.TestCase):
    def write(self, folder, content):
        path = Path(folder) / "status.txt"
        path.write_text(content, encoding="utf-8")
        return path

    def test_accepts_the_ok_marker(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(cli.read_status(self.write(d, "OK")))

    def test_returns_the_message_after_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write(d, "ERROR\nLayer not found: desc 9")
            self.assertIn("desc 9", cli.read_status(path))

    def test_a_status_carrying_comp_numbers_is_still_success(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(cli.read_status(self.write(d, "OK\nfps=60")))

    def test_reports_when_the_script_never_wrote_a_status(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNotNone(cli.read_status(Path(d) / "missing.txt"))


class CompInfoTests(unittest.TestCase):
    def write(self, folder, content):
        path = Path(folder) / "status.txt"
        path.write_text(content, encoding="utf-8")
        return path

    def test_reads_the_comp_numbers_the_script_reported(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write(
                d, "OK\nfps=60\nduration=184.2667\nworkAreaStart=0\nworkAreaDuration=5.5333")
            info = cli.read_comp_info(path)
            self.assertEqual(info["fps"], 60.0)
            self.assertAlmostEqual(info["workAreaDuration"], 5.5333)
            self.assertAlmostEqual(info["duration"], 184.2667)

    def test_reports_nothing_when_no_numbers_were_written(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli.read_comp_info(self.write(d, "OK")), {})

    def test_reports_nothing_for_a_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli.read_comp_info(Path(d) / "missing.txt"), {})

    def test_ignores_a_line_that_is_not_a_number(self):
        with tempfile.TemporaryDirectory() as d:
            info = cli.read_comp_info(self.write(d, "OK\nfps=60\nname=Comp 1"))
            self.assertEqual(info, {"fps": 60.0})


if __name__ == "__main__":
    unittest.main()
