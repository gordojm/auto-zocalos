import unittest
from pathlib import Path

from autozocalos import aepx

ROOT = Path(__file__).resolve().parent.parent
MUSICA = ROOT / "Zocalo Musica.aepx"
ROTULO = ROOT / "rotulo.aepx"


class ReadLayerFontSizesTests(unittest.TestCase):
    def test_reads_the_song_layer_size(self):
        sizes = aepx.read_layer_font_sizes(MUSICA)
        self.assertAlmostEqual(sizes[("Zocalo Edit", "NOMBRE DEL TEMA")], 59.0)

    def test_reads_the_game_layer_size(self):
        sizes = aepx.read_layer_font_sizes(MUSICA)
        self.assertAlmostEqual(sizes[("Zocalo Edit", "NOMBRE DEL JUEGO")], 26.9)

    def test_reads_the_name_layer_size(self):
        sizes = aepx.read_layer_font_sizes(ROTULO)
        self.assertAlmostEqual(sizes[("BLOQUE NOMBRE", "Rodrigo Lo Cicero")], 46.0)

    def test_reads_a_social_layer_size(self):
        sizes = aepx.read_layer_font_sizes(ROTULO)
        self.assertAlmostEqual(sizes[("rotulin", "desc 5")], 30.0)

    def test_does_not_report_the_document_default_of_twelve(self):
        sizes = aepx.read_layer_font_sizes(ROTULO)
        self.assertNotIn(12.0, sizes.values())


class ReadLayerTextsTests(unittest.TestCase):
    def test_reads_the_musica_song_layer_text(self):
        texts = aepx.read_layer_texts(MUSICA)
        self.assertEqual(texts[("Zocalo Edit", "NOMBRE DEL TEMA")], "NOMBRE DEL TEMA\r")

    def test_reads_the_musica_game_layer_text(self):
        texts = aepx.read_layer_texts(MUSICA)
        self.assertEqual(texts[("Zocalo Edit", "NOMBRE DEL JUEGO")], "NOMBRE DEL JUEGO\r")

    def test_reads_a_social_layer_including_its_icon(self):
        texts = aepx.read_layer_texts(ROTULO)
        self.assertEqual(texts[("rotulin", "desc 5")], "\uf16d @rodri.locicero\r")

    def test_preserves_a_layers_extra_trailing_carriage_return(self):
        texts = aepx.read_layer_texts(ROTULO)
        self.assertEqual(texts[("rotulin", "desc 4")], "\ue61b @@zarkoarg\r\r")

    def test_finds_the_name_layer_in_its_own_comp(self):
        texts = aepx.read_layer_texts(ROTULO)
        self.assertEqual(texts[("BLOQUE NOMBRE", "Rodrigo Lo Cicero")], "Rodrigo Lo Cicero\r")

    def test_ignores_layers_that_carry_no_text(self):
        layers = [layer for _comp, layer in aepx.read_layer_texts(ROTULO)]
        self.assertNotIn("Capa de formas 3", layers)
        self.assertIn("desc 4", layers)


if __name__ == "__main__":
    unittest.main()
