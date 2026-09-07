import unittest
from pathlib import Path

from autozocalos import aepx, build, config

FA = {0xF16D, 0xF09A, 0xE07B, 0xF167, 0xE61B, 0xF1BC, 0xF1E8, 0xF26B}

ORIGINALS = {
    ("BLOQUE NOMBRE", "Rodrigo Lo Cicero"): "Rodrigo Lo Cicero\r",
    ("rotulin", "desc 4"): "\ue61b @@zarkoarg\r\r",
    ("rotulin", "desc 5"): "\uf16d @rodri.locicero\r",
    ("rotulin", "desc 6"): "\uf26b 501stargentina.com.ar\r",
    ("Zocalo Edit", "NOMBRE DEL TEMA"): "NOMBRE DEL TEMA\r",
    ("Zocalo Edit", "NOMBRE DEL JUEGO"): "NOMBRE DEL JUEGO\r",
}


def rotulo(name="Juan Perez", size=None, socials=(("Instagram", "@rodri"), None, None)):
    return build.rotulo_edits(name, size, list(socials), ORIGINALS, FA)


def by_layer(edits, layer):
    return next(e for e in edits if e.layer == layer)


class RotuloNameTests(unittest.TestCase):
    def test_writes_the_name_to_its_own_comp(self):
        edit = by_layer(rotulo(), "Rodrigo Lo Cicero")
        self.assertEqual(edit.comp, "BLOQUE NOMBRE")
        self.assertEqual(edit.text, "Juan Perez")

    def test_does_not_uppercase_the_name(self):
        self.assertEqual(by_layer(rotulo(name="Juan Perez"), "Rodrigo Lo Cicero").text, "Juan Perez")

    def test_the_name_never_takes_an_icon_run(self):
        self.assertFalse(by_layer(rotulo(), "Rodrigo Lo Cicero").icon_run)

    def test_applies_the_name_font_size_override(self):
        self.assertEqual(by_layer(rotulo(size=64.0), "Rodrigo Lo Cicero").font_size, 64.0)

    def test_leaves_the_font_size_alone_when_not_given(self):
        self.assertIsNone(by_layer(rotulo(), "Rodrigo Lo Cicero").font_size)

    def test_the_size_override_does_not_leak_to_social_layers(self):
        self.assertIsNone(by_layer(rotulo(size=64.0), "desc 4").font_size)


class RotuloSocialTests(unittest.TestCase):
    def test_prepends_the_glyph_and_marks_the_icon_run(self):
        edit = by_layer(rotulo(socials=(("Instagram", "@rodri"), None, None)), "desc 4")
        self.assertTrue(edit.text.startswith("\uf16d @rodri"))
        self.assertTrue(edit.icon_run)

    def test_preserves_the_layers_existing_blank_line(self):
        edit = by_layer(rotulo(socials=(("Instagram", "@rodri"), None, None)), "desc 4")
        self.assertEqual(edit.text, "\uf16d @rodri\r")

    def test_a_layer_without_a_blank_line_gets_no_extra_carriage_return(self):
        edit = by_layer(rotulo(socials=(None, ("Twitch", "/zarko"), None)), "desc 5")
        self.assertEqual(edit.text, "\uf1e8 /zarko")

    def test_shows_a_slot_that_was_filled_in(self):
        """The template ships with desc 6 hidden, so filling it must unhide it."""
        edit = by_layer(rotulo(socials=(("Instagram", "@r"), ("Twitch", "/t"), ("Spotify", "s"))), "desc 6")
        self.assertTrue(edit.enabled)

    def test_shows_every_filled_slot(self):
        edits = rotulo(socials=(("Instagram", "@r"), ("Twitch", "/t"), ("Spotify", "s")))
        for layer in ("desc 4", "desc 5", "desc 6"):
            self.assertTrue(by_layer(edits, layer).enabled, layer)

    def test_hides_a_slot_that_was_left_blank(self):
        edit = by_layer(rotulo(socials=(("Instagram", "@r"), None, None)), "desc 5")
        self.assertFalse(edit.enabled)
        self.assertIsNone(edit.text)

    def test_omits_the_icon_when_the_font_lacks_the_glyph(self):
        edit = by_layer(build.rotulo_edits("N", None, [("Instagram", "@r"), None, None], ORIGINALS, set()), "desc 4")
        self.assertEqual(edit.text, "@r\r")
        self.assertFalse(edit.icon_run)

    def test_passes_an_unusual_handle_through_verbatim(self):
        edit = by_layer(rotulo(socials=((("No icon"), "@@zarkoarg"), None, None)), "desc 4")
        self.assertEqual(edit.text, "@@zarkoarg\r")

    def test_produces_one_edit_per_configured_layer(self):
        self.assertEqual(len(rotulo()), 4)


class MusicaTests(unittest.TestCase):
    def edits(self, song="thunderstruck", size=None, game="rock band"):
        return build.musica_edits(song, size, game, ORIGINALS)

    def test_uppercases_the_song(self):
        self.assertEqual(by_layer(self.edits(), "NOMBRE DEL TEMA").text, "THUNDERSTRUCK")

    def test_uppercases_the_game(self):
        self.assertEqual(by_layer(self.edits(), "NOMBRE DEL JUEGO").text, "ROCK BAND")

    def test_applies_the_song_font_size_override(self):
        self.assertEqual(by_layer(self.edits(size=72.0), "NOMBRE DEL TEMA").font_size, 72.0)

    def test_the_size_override_does_not_leak_to_the_game_layer(self):
        self.assertIsNone(by_layer(self.edits(size=72.0), "NOMBRE DEL JUEGO").font_size)

    def test_never_marks_an_icon_run(self):
        self.assertFalse(any(e.icon_run for e in self.edits()))


class RealTemplateTests(unittest.TestCase):
    def test_the_real_desc_4_blank_line_is_preserved(self):
        originals = aepx.read_layer_texts(config.template_path("rotulo"))
        edits = build.rotulo_edits("N", None, [("Instagram", "@r"), None, None], originals, FA)
        self.assertEqual(by_layer(edits, "desc 4").text, "\uf16d @r\r")


class OutputStemTests(unittest.TestCase):
    def test_names_a_rotulo_after_the_person(self):
        self.assertEqual(build.output_stem("rotulo", {"name": "Juan Perez"}), "Juan Perez")

    def test_names_a_musica_after_song_and_game(self):
        stem = build.output_stem("musica", {"song": "THUNDERSTRUCK", "game": "ROCK BAND"})
        self.assertEqual(stem, "THUNDERSTRUCK - ROCK BAND")

    def test_sanitises_an_illegal_character(self):
        self.assertEqual(build.output_stem("rotulo", {"name": "AC/DC"}), "AC-DC")


if __name__ == "__main__":
    unittest.main()
