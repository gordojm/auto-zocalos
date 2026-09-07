import unittest

from autozocalos import render


class ConsoleEncodingTests(unittest.TestCase):
    def test_uses_the_console_output_codepage(self):
        self.assertEqual(render.console_encoding(lambda: 850), "cp850")

    def test_maps_the_utf8_codepage(self):
        self.assertEqual(render.console_encoding(lambda: 65001), "utf-8")

    def test_maps_a_windows_ansi_codepage(self):
        self.assertEqual(render.console_encoding(lambda: 1252), "cp1252")

    def test_falls_back_when_the_codepage_cannot_be_read(self):
        def boom():
            raise OSError("no console")
        self.assertTrue(render.console_encoding(boom))

    def test_cp850_decodes_aerenders_accented_output(self):
        raw = b"par\xa0metro"
        self.assertEqual(raw.decode(render.console_encoding(lambda: 850)), "par\u00e1metro")


class ProgressReporterTests(unittest.TestCase):
    def frames(self, total):
        out = []
        report = render.progress_reporter(total, out.append)
        for i in range(1, total + 1):
            report(f"PROGRESS:  0:00:00:00 ({i}): 0 segundos")
        return out

    def test_reports_ten_times_not_once_per_frame(self):
        self.assertEqual(len(self.frames(100)), 10)

    def test_reports_ten_times_for_an_awkward_total(self):
        self.assertEqual(len(self.frames(332)), 10)

    def test_finishes_at_one_hundred_percent(self):
        self.assertIn("100%", self.frames(332)[-1])

    def test_starts_at_ten_percent_not_zero(self):
        self.assertIn("10%", self.frames(100)[0])

    def test_shows_the_frame_count(self):
        self.assertIn("332", self.frames(332)[-1])

    def test_swallows_the_noisy_settings_dump(self):
        out = []
        report = render.progress_reporter(332, out.append)
        report("PROGRESS:  Formato: QuickTime")
        report("PROGRESS:  Canales: RGB + Alfa")
        self.assertEqual(out, [])

    def test_lets_errors_through(self):
        out = []
        report = render.progress_reporter(332, out.append)
        report("aerender Error: no se puede abrir el proyecto")
        self.assertEqual(len(out), 1)

    def test_ignores_blank_lines(self):
        out = []
        report = render.progress_reporter(332, out.append)
        report("")
        report("   ")
        self.assertEqual(out, [])

    def test_survives_an_unknown_total(self):
        out = []
        report = render.progress_reporter(0, out.append)
        report("PROGRESS:  0:00:00:00 (5): 0 segundos")
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
