"""Cover the orchestration in cli.main() with everything external stubbed."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autozocalos import aepx, cli, config, icons, picker, prompts, render

ROTULO_TEXTS = {
    ("BLOQUE NOMBRE", "Rodrigo Lo Cicero"): "Rodrigo Lo Cicero\r",
    ("rotulin", "desc 4"): "\ue61b @@zarkoarg\r\r",
    ("rotulin", "desc 5"): "\uf16d @rodri.locicero\r",
    ("rotulin", "desc 6"): "\uf26b 501stargentina.com.ar\r",
}
MUSICA_TEXTS = {
    ("Zocalo Edit", "NOMBRE DEL TEMA"): "NOMBRE DEL TEMA\r",
    ("Zocalo Edit", "NOMBRE DEL JUEGO"): "NOMBRE DEL JUEGO\r",
}
SIZES = {
    ("BLOQUE NOMBRE", "Rodrigo Lo Cicero"): 46.0,
    ("Zocalo Edit", "NOMBRE DEL TEMA"): 59.0,
}

# What After Effects reports back for each template's render comp.
REPORTS = {
    "rotulo": "OK\nfps=60\nduration=184.2667\nworkAreaStart=0\nworkAreaDuration=5.5333",
    "musica": "OK\nfps=60\nduration=60.0\nworkAreaStart=0\nworkAreaDuration=7.0167",
}


class MainTests(unittest.TestCase):
    def run_main(self, template):
        calls = []

        def fake_run(argv, echo=None):
            calls.append(argv)
            if "-noui" in argv:
                workdir = Path(argv[argv.index("-r") + 1]).parent
                (workdir / "status.txt").write_text(REPORTS[template], encoding="utf-8")
            else:
                Path(argv[argv.index("-output") + 1]).write_bytes(b"x" * 32)
            return 0

        def fake_choose(label, options):
            wanted = config.TEMPLATES[template]["label"]
            return wanted if wanted in options else "Instagram"

        def fake_required(label):
            return {"Nombre": "Ricardo Bochini",
                    "Nombre del tema": "thunderstruck",
                    "Nombre del juego": "rock band"}.get(label, "@r")

        texts = ROTULO_TEXTS if template == "rotulo" else MUSICA_TEXTS

        with tempfile.TemporaryDirectory() as dest, tempfile.TemporaryDirectory() as ae:
            support = Path(ae)
            (support / "aerender.exe").write_bytes(b"")
            (support / "AfterFX.exe").write_bytes(b"")
            with (
                mock.patch.object(render, "run_streaming", fake_run),
                mock.patch.object(render, "after_effects_running", lambda: False),
                mock.patch.object(config, "support_dir", lambda: support),
                mock.patch.object(icons, "load_available_codepoints", lambda: {0xF16D}),
                mock.patch.object(aepx, "read_layer_texts", lambda p: texts),
                mock.patch.object(aepx, "read_layer_font_sizes", lambda p: SIZES),
                mock.patch.object(picker, "ask_folder", lambda: Path(dest)),
                mock.patch.object(prompts, "choose", fake_choose),
                mock.patch.object(prompts, "ask_required", fake_required),
                mock.patch.object(prompts, "ask_optional", lambda label: ""),
                mock.patch.object(prompts, "ask_optional_number", lambda label, size=None: None),
            ):
                code = cli.main()
        aerender = next(a for a in calls if "-output" in a)
        return code, aerender, calls

    def test_rotulo_run_succeeds(self):
        code, _, _ = self.run_main("rotulo")
        self.assertEqual(code, 0)

    def test_rotulo_renders_only_its_work_area(self):
        _, argv, _ = self.run_main("rotulo")
        self.assertEqual(argv[argv.index("-s") + 1], "0")
        self.assertEqual(argv[argv.index("-e") + 1], "331")

    def test_rotulo_does_not_render_the_whole_comp(self):
        _, argv, _ = self.run_main("rotulo")
        self.assertNotIn("11055", argv)

    def test_musica_is_pinned_to_seven_seconds(self):
        _, argv, _ = self.run_main("musica")
        self.assertEqual(argv[argv.index("-e") + 1], "419")

    def test_applies_the_text_before_rendering(self):
        _, _, calls = self.run_main("rotulo")
        self.assertIn("-noui", calls[0])
        self.assertIn("-output", calls[1])

    def test_writes_into_the_chosen_folder(self):
        _, argv, _ = self.run_main("rotulo")
        self.assertTrue(argv[argv.index("-output") + 1].endswith("Ricardo Bochini.mov"))

    def test_cleans_up_the_work_directory_on_success(self):
        _, _, calls = self.run_main("rotulo")
        workdir = Path(calls[0][calls[0].index("-r") + 1]).parent
        self.assertFalse(workdir.exists())


if __name__ == "__main__":
    unittest.main()
