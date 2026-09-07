# -*- coding: utf-8 -*-
"""What the CLI asks, in what order, and what it does with blank answers."""
import unittest
from unittest import mock

from autozocalos import cli, prompts

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
SIZES = {("BLOQUE NOMBRE", "Rodrigo Lo Cicero"): 46.0,
         ("Zocalo Edit", "NOMBRE DEL TEMA"): 59.0}
GLYPHS = {0xF16D, 0xF1E8, 0xF1BC}


def by_layer(edits, layer):
    return next(e for e in edits if e.layer == layer)


class Harness:
    """Records every prompt in order and feeds canned answers."""

    def __init__(self, optional_answers):
        self.order = []
        self.optional = list(optional_answers)

    def required(self, label):
        self.order.append(label)
        return {"Nombre": "Ricardo Bochini",
                "Nombre del tema": "thunderstruck",
                "Nombre del juego": "rock band"}[label]

    def optional_text(self, label):
        self.order.append(label)
        return self.optional.pop(0) if self.optional else ""

    def number(self, label, template_size=None):
        self.order.append(label)
        return None

    def choose(self, label, options):
        self.order.append(label)
        return "Instagram"


def run_rotulo(socials):
    h = Harness(socials)
    with (
        mock.patch.object(prompts, "ask_required", h.required),
        mock.patch.object(prompts, "ask_optional", h.optional_text),
        mock.patch.object(prompts, "ask_optional_number", h.number),
        mock.patch.object(prompts, "choose", h.choose),
    ):
        values, edits = cli.collect_rotulo(ROTULO_TEXTS, SIZES, GLYPHS)
    return h.order, values, edits


def run_musica():
    h = Harness([])
    with (
        mock.patch.object(prompts, "ask_required", h.required),
        mock.patch.object(prompts, "ask_optional", h.optional_text),
        mock.patch.object(prompts, "ask_optional_number", h.number),
        mock.patch.object(prompts, "choose", h.choose),
    ):
        values, edits = cli.collect_musica(MUSICA_TEXTS, SIZES)
    return h.order, values, edits


class PromptOrderTests(unittest.TestCase):
    def test_musica_asks_the_font_size_last(self):
        order, _, _ = run_musica()
        self.assertIn("Tama\u00f1o", order[-1])

    def test_musica_asks_both_titles_before_the_size(self):
        order, _, _ = run_musica()
        self.assertEqual(order[:2], ["Nombre del tema", "Nombre del juego"])

    def test_rotulo_asks_the_font_size_last(self):
        order, _, _ = run_rotulo(["@uno", "", ""])
        self.assertIn("Tama\u00f1o", order[-1])

    def test_rotulo_asks_the_name_first(self):
        order, _, _ = run_rotulo(["@uno", "", ""])
        self.assertEqual(order[0], "Nombre")


class SocialSkippingTests(unittest.TestCase):
    def test_a_blank_first_slot_hides_all_three(self):
        _, _, edits = run_rotulo([""])
        for layer in ("desc 4", "desc 5", "desc 6"):
            self.assertFalse(by_layer(edits, layer).enabled, layer)

    def test_a_blank_first_slot_stops_the_questions(self):
        order, _, _ = run_rotulo([""])
        self.assertEqual(len([p for p in order if "Red social" in p]), 1)

    def test_a_blank_second_slot_hides_the_second_and_third(self):
        _, _, edits = run_rotulo(["@uno", ""])
        self.assertTrue(by_layer(edits, "desc 4").enabled)
        self.assertFalse(by_layer(edits, "desc 5").enabled)
        self.assertFalse(by_layer(edits, "desc 6").enabled)

    def test_a_blank_second_slot_stops_the_questions(self):
        order, _, _ = run_rotulo(["@uno", ""])
        self.assertEqual(len([p for p in order if "Red social" in p]), 2)

    def test_three_answers_show_all_three_layers(self):
        _, _, edits = run_rotulo(["@uno", "@dos", "@tres"])
        for layer in ("desc 4", "desc 5", "desc 6"):
            self.assertTrue(by_layer(edits, layer).enabled, layer)

    def test_the_first_slot_is_not_mandatory(self):
        order, _, _ = run_rotulo([""])
        self.assertNotIn("Nombre", [p for p in order if "Red social" in p])
        self.assertTrue(any("Red social 1" in p for p in order))


if __name__ == "__main__":
    unittest.main()
