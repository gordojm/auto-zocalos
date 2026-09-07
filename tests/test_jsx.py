import unittest
from pathlib import Path

from autozocalos.jsx import LayerEdit, build_jsx

BS = chr(92)


def script(edits, **kw):
    return build_jsx(
        project_path=Path(r"C:\temp\x\rotulo.aepx"),
        edits=edits,
        status_path=Path(r"C:\temp\x\status.txt"),
        icon_font="FontAwesome7Brands-Regular",
        default_body_font="ZeroesTwo",
        **kw,
    )


class EscapingTests(unittest.TestCase):
    def test_generated_script_is_pure_ascii(self):
        script([LayerEdit("rotulin", "desc 4", "\uf16d @rodri")]).encode("ascii")

    def test_non_ascii_becomes_a_unicode_escape(self):
        s = script([LayerEdit("rotulin", "desc 4", "\uf16d @rodri")])
        self.assertIn(BS + "uf16d", s.lower())

    def test_a_quote_in_a_handle_cannot_break_the_string_literal(self):
        s = script([LayerEdit("rotulin", "desc 4", 'say "hi"')])
        self.assertIn(r"\"hi\"", s)

    def test_a_backslash_in_a_handle_is_escaped(self):
        s = script([LayerEdit("rotulin", "desc 4", "a" + BS + "b")])
        self.assertIn("a" + BS * 2 + "b", s)

    def test_windows_paths_survive_escaping(self):
        expected = "C:" + BS * 2 + "temp" + BS * 2 + "x" + BS * 2 + "rotulo.aepx"
        self.assertIn(expected, script([]))


class EditDataTests(unittest.TestCase):
    def test_marks_the_icon_run_in_the_edit_data(self):
        s = script([LayerEdit("rotulin", "desc 4", "\uf16d @r", icon_run=True)])
        self.assertIn('"iconRun": true', s)

    def test_does_not_mark_an_icon_run_without_a_glyph(self):
        s = script([LayerEdit("rotulin", "desc 4", "@r", icon_run=False)])
        self.assertIn('"iconRun": false', s)

    def test_carries_a_font_size_override_when_given(self):
        s = script([LayerEdit("BLOQUE NOMBRE", "N", "x", font_size=64.0)])
        self.assertIn('"fontSize": 64.0', s)

    def test_carries_a_null_font_size_when_not_overridden(self):
        s = script([LayerEdit("BLOQUE NOMBRE", "N", "x", font_size=None)])
        self.assertIn('"fontSize": null', s)

    def test_hides_a_layer_that_was_left_blank(self):
        s = script([LayerEdit("rotulin", "desc 5", None, enabled=False)])
        self.assertIn('"enabled": false', s)

    def test_carries_the_comp_and_layer_names(self):
        s = script([LayerEdit("rotulin", "desc 5", "x")])
        self.assertIn('"comp": "rotulin"', s)
        self.assertIn('"layer": "desc 5"', s)


class ScriptBodyTests(unittest.TestCase):
    def test_clears_the_leftover_render_queue(self):
        s = script([])
        self.assertIn("renderQueue", s)
        self.assertIn("remove()", s)

    def test_styles_the_icon_run_with_the_icon_font(self):
        s = script([LayerEdit("rotulin", "desc 4", "\uf16d @r", icon_run=True)])
        self.assertIn("characterRange(0, 2)", s)
        self.assertIn("FontAwesome7Brands-Regular", s)

    def test_falls_back_to_the_default_body_font(self):
        self.assertIn("ZeroesTwo", script([]))

    def test_writes_a_status_file_for_python_to_read(self):
        self.assertIn("status.txt", script([]))

    def test_saves_the_temporary_project(self):
        self.assertIn("app.project.save", script([]))

    def test_reports_the_render_comps_numbers(self):
        s = build_jsx(
            project_path=Path(r"C:	\p.aepx"), edits=[],
            status_path=Path(r"C:	\status.txt"),
            icon_font="F", default_body_font="B", report_comp="Comp 1")
        self.assertIn("workAreaDuration", s)
        self.assertIn('"Comp 1"', s)

    def test_styles_the_document_before_writing_it_back(self):
        """AE keeps characterRange edits only when they precede setValue.

        Writing them afterwards, off prop.value, mutates a detached copy and is
        silently discarded -- which left every social line in the icon font.
        """
        whole = script([LayerEdit("rotulin", "desc 4", "x", icon_run=True)])
        body = whole[whole.index("function applyEdit"):]
        self.assertLess(body.index("characterRange"), body.index("prop.setValue"))

    def test_never_styles_through_the_detached_live_view(self):
        """Reading via prop.value is fine; writing style through it is not."""
        whole = script([LayerEdit("rotulin", "desc 4", "x", icon_run=True)])
        body = whole[whole.index("function applyEdit"):]
        self.assertNotIn("prop.value.characterRange", body)

    def test_writes_the_document_back_exactly_once(self):
        body = script([LayerEdit("rotulin", "desc 4", "x", icon_run=True)])
        self.assertEqual(body.count("prop.setValue"), 1)

    def test_applies_the_body_font_and_size_to_the_document(self):
        body = script([LayerEdit("rotulin", "desc 4", "x", icon_run=True)])
        self.assertIn("doc.characterRange(0, length).font = bodyFont", body)
        self.assertIn("doc.characterRange(0, length).fontSize = size", body)

    def test_applies_the_icon_font_to_the_document(self):
        body = script([LayerEdit("rotulin", "desc 4", "x", icon_run=True)])
        self.assertIn("doc.characterRange(0, 2).font = ICON_FONT", body)

    def test_sets_visibility_from_the_edit(self):
        """Not just hiding: a layer the template left hidden must be turned on."""
        body = script([LayerEdit("rotulin", "desc 6", "x")])
        self.assertIn("layer.enabled = edit.enabled", body)

    def test_marks_a_filled_layer_as_visible(self):
        s = script([LayerEdit("rotulin", "desc 6", "x")])
        self.assertIn('"enabled": true', s)

    def test_quits_after_running(self):
        self.assertIn("app.quit()", script([]))


if __name__ == "__main__":
    unittest.main()
