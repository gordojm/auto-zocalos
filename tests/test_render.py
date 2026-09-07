import io
import unittest
from pathlib import Path

from autozocalos import render


class FrameMathTests(unittest.TestCase):
    def test_seven_seconds_at_sixty_fps_ends_on_frame_419(self):
        self.assertEqual(render.last_frame(7.0, 60), 419)

    def test_one_second_at_sixty_fps_ends_on_frame_59(self):
        self.assertEqual(render.last_frame(1.0, 60), 59)


class RenderRangeTests(unittest.TestCase):
    ROTULO = {"fps": 60.0, "duration": 184.2667, "workAreaStart": 0.0, "workAreaDuration": 5.5333}
    MUSICA = {"fps": 60.0, "duration": 60.0, "workAreaStart": 0.0, "workAreaDuration": 7.0167}

    def test_uses_the_work_area_not_the_comp_length(self):
        self.assertEqual(render.render_range(self.ROTULO, None), (0, 331))

    def test_a_work_area_that_does_not_start_at_zero(self):
        info = dict(self.ROTULO, workAreaStart=1.0, workAreaDuration=2.0)
        self.assertEqual(render.render_range(info, None), (60, 179))

    def test_an_explicit_override_wins_over_the_work_area(self):
        self.assertEqual(render.render_range(self.MUSICA, 7.0), (0, 419))

    def test_falls_back_to_the_whole_comp_without_information(self):
        self.assertIsNone(render.render_range({}, None))

    def test_an_override_still_applies_without_work_area_information(self):
        self.assertEqual(render.render_range({"fps": 60.0}, 7.0), (0, 419))

    def test_never_runs_past_the_end_of_the_comp(self):
        info = dict(self.ROTULO, workAreaDuration=999.0)
        start, end = render.render_range(info, None)
        self.assertEqual(end, round(184.2667 * 60) - 1)


class AerenderArgvTests(unittest.TestCase):
    def argv(self, **kw):
        return render.aerender_argv(
            exe=Path(r"C:\AE\aerender.exe"),
            project=Path(r"C:\temp\p.aepx"),
            comp="Comp 1",
            output=Path(r"D:\out\clip.mov"),
            om_template="ProRes4444_Alpha",
            rs_template="AutoZocalos_RS",
            **kw,
        )

    def test_passes_the_comp_and_templates(self):
        argv = self.argv()
        self.assertIn("-comp", argv)
        self.assertIn("Comp 1", argv)
        self.assertIn("ProRes4444_Alpha", argv)
        self.assertIn("AutoZocalos_RS", argv)

    def test_renders_the_whole_comp_when_no_limit_is_given(self):
        self.assertNotIn("-e", self.argv())

    def test_limits_the_range_when_an_end_frame_is_given(self):
        argv = self.argv(end_frame=419)
        self.assertEqual(argv[argv.index("-s") + 1], "0")
        self.assertEqual(argv[argv.index("-e") + 1], "419")

    def test_uses_a_non_zero_start_frame(self):
        argv = self.argv(start_frame=60, end_frame=179)
        self.assertEqual(argv[argv.index("-s") + 1], "60")
        self.assertEqual(argv[argv.index("-e") + 1], "179")

    def test_does_not_save_changes_back_to_the_project(self):
        self.assertIn("DO_NOT_SAVE_CHANGES", self.argv())

    def test_every_argument_is_a_string(self):
        self.assertTrue(all(isinstance(a, str) for a in self.argv(end_frame=419)))


class SafeWriteTests(unittest.TestCase):
    def console(self, encoding):
        buffer = io.BytesIO()
        return buffer, io.TextIOWrapper(buffer, encoding=encoding, errors="strict", newline="")

    def test_writes_a_plain_line(self):
        buffer, stream = self.console("cp1252")
        render.safe_write("PROGRESS: rendering", stream)
        stream.flush()
        self.assertIn(b"PROGRESS: rendering", buffer.getvalue())

    def test_survives_a_character_the_console_cannot_encode(self):
        buffer, stream = self.console("cp1252")
        render.safe_write("aerender: � sigue", stream)
        stream.flush()
        self.assertIn(b"sigue", buffer.getvalue())

    def test_survives_an_accent_on_an_ascii_only_console(self):
        buffer, stream = self.console("ascii")
        render.safe_write("Duracion: 7 segundos, canción", stream)
        stream.flush()
        self.assertIn(b"segundos", buffer.getvalue())


class AfterFxArgvTests(unittest.TestCase):
    def test_runs_the_script_without_a_ui(self):
        argv = render.afterfx_argv(Path(r"C:\AE\AfterFX.exe"), Path(r"C:\t\a.jsx"))
        self.assertIn("-noui", argv)
        self.assertEqual(argv[argv.index("-r") + 1], r"C:\t\a.jsx")


if __name__ == "__main__":
    unittest.main()
