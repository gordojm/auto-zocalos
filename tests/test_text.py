import unittest
from pathlib import Path
import tempfile

from autozocalos import text


class ComposeSocialTests(unittest.TestCase):
    def test_joins_glyph_and_handle_with_a_single_space(self):
        self.assertEqual(text.compose_social("@rodri", "\uf16d"), "\uf16d @rodri")

    def test_icon_run_covers_exactly_the_glyph_and_its_space(self):
        line = text.compose_social("@rodri", "\uf16d")
        self.assertEqual(line[: text.ICON_RUN_LENGTH], "\uf16d ")

    def test_omits_the_leading_space_when_there_is_no_glyph(self):
        self.assertEqual(text.compose_social("@rodri", None), "@rodri")

    def test_passes_a_doubled_at_sign_through_untouched(self):
        self.assertEqual(text.compose_social("@@zarkoarg", None), "@@zarkoarg")

    def test_passes_a_slash_prefix_through_untouched(self):
        self.assertEqual(text.compose_social("/MiCanal", "\uf167"), "\uf167 /MiCanal")

    def test_preserves_case_exactly(self):
        self.assertEqual(text.compose_social("RoDrI.LoCiCeRo", None), "RoDrI.LoCiCeRo")

    def test_does_not_add_a_prefix_to_a_bare_domain(self):
        self.assertEqual(text.compose_social("501stargentina.com.ar", None), "501stargentina.com.ar")


class TrailingBlankTests(unittest.TestCase):
    def test_a_single_paragraph_terminator_is_not_a_blank_line(self):
        self.assertEqual(text.trailing_blank_lines("NOMBRE DEL TEMA\r"), 0)

    def test_an_extra_carriage_return_counts_as_one_blank_line(self):
        self.assertEqual(text.trailing_blank_lines("\ue61b @@zarkoarg\r\r"), 1)

    def test_text_with_no_terminator_has_no_blank_lines(self):
        self.assertEqual(text.trailing_blank_lines("plain"), 0)

    def test_reapplies_the_recorded_blank_lines(self):
        self.assertEqual(text.with_trailing_blanks("nuevo", 1), "nuevo\r")

    def test_reapplies_nothing_when_there_were_no_blank_lines(self):
        self.assertEqual(text.with_trailing_blanks("nuevo", 0), "nuevo")


class CapsTests(unittest.TestCase):
    def test_uppercases_the_song_title(self):
        self.assertEqual(text.to_caps("thunderstruck"), "THUNDERSTRUCK")

    def test_uppercases_accented_spanish_characters(self):
        self.assertEqual(text.to_caps("canción"), "CANCIÓN")


class FilenameTests(unittest.TestCase):
    def test_replaces_characters_windows_forbids(self):
        self.assertEqual(text.sanitize_filename('AC/DC: Back*Black?'), "AC-DC- Back-Black-")

    def test_replaces_a_backslash(self):
        self.assertEqual(text.sanitize_filename("AC" + chr(92) + "DC"), "AC-DC")

    def test_strips_trailing_dots_and_spaces(self):
        self.assertEqual(text.sanitize_filename("nombre. "), "nombre")

    def test_falls_back_when_nothing_usable_remains(self):
        self.assertEqual(text.sanitize_filename("///"), "output")

    def test_escapes_a_reserved_device_name(self):
        self.assertEqual(text.sanitize_filename("CON"), "_CON")

    def test_uses_the_plain_name_when_the_folder_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(text.unique_output_path(Path(d), "clip").name, "clip.mov")

    def test_suffixes_rather_than_overwriting_an_existing_file(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "clip.mov").write_bytes(b"")
            self.assertEqual(text.unique_output_path(Path(d), "clip").name, "clip (2).mov")


if __name__ == "__main__":
    unittest.main()
