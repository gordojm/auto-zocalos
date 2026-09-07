import unittest
from pathlib import Path

from autozocalos import config


class TemplateMapTests(unittest.TestCase):
    def test_offers_both_templates(self):
        self.assertEqual(sorted(config.TEMPLATES), ["musica", "rotulo"])

    def test_rotulo_renders_its_master_comp(self):
        self.assertEqual(config.TEMPLATES["rotulo"]["comp"], "Comp 1")

    def test_rotulo_renders_its_full_length(self):
        self.assertIsNone(config.TEMPLATES["rotulo"]["render_seconds"])

    def test_musica_is_clamped_to_seven_seconds(self):
        self.assertEqual(config.TEMPLATES["musica"]["render_seconds"], 7.0)

    def test_social_slots_map_in_the_confirmed_order(self):
        fields = config.TEMPLATES["rotulo"]["fields"]
        self.assertEqual(fields["social1"]["layer"], "desc 4")
        self.assertEqual(fields["social2"]["layer"], "desc 5")
        self.assertEqual(fields["social3"]["layer"], "desc 6")

    def test_only_social_fields_take_an_icon(self):
        fields = config.TEMPLATES["rotulo"]["fields"]
        self.assertFalse(fields["name"]["icon"])
        self.assertTrue(fields["social1"]["icon"])

    def test_every_configured_layer_exists_in_its_template(self):
        from autozocalos import aepx
        for name, spec in config.TEMPLATES.items():
            texts = aepx.read_layer_texts(config.PROJECT_ROOT / spec["file"])
            for field, layer in spec["fields"].items():
                key = (layer["comp"], layer["layer"])
                self.assertIn(key, texts, f"{name}.{field} -> {key}")


class NewestInstallTests(unittest.TestCase):
    def test_prefers_the_highest_version(self):
        found = [
            Path(r"C:\Adobe\Adobe After Effects 2024\Support Files\aerender.exe"),
            Path(r"C:\Adobe\Adobe After Effects 2026\Support Files\aerender.exe"),
            Path(r"C:\Adobe\Adobe After Effects 2025\Support Files\aerender.exe"),
        ]
        self.assertIn("2026", str(config.newest_install(found)))

    def test_returns_none_when_nothing_is_installed(self):
        self.assertIsNone(config.newest_install([]))


if __name__ == "__main__":
    unittest.main()
