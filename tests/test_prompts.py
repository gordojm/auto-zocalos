import unittest

from autozocalos import prompts


class OptionalNumberTests(unittest.TestCase):
    def test_blank_means_keep_the_template_default(self):
        self.assertIsNone(prompts.parse_optional_number(""))

    def test_whitespace_only_means_keep_the_default(self):
        self.assertIsNone(prompts.parse_optional_number("   "))

    def test_reads_a_whole_number(self):
        self.assertEqual(prompts.parse_optional_number("64"), 64.0)

    def test_reads_a_decimal(self):
        self.assertEqual(prompts.parse_optional_number("26.9"), 26.9)

    def test_accepts_a_comma_as_the_decimal_separator(self):
        self.assertEqual(prompts.parse_optional_number("26,9"), 26.9)

    def test_rejects_text(self):
        with self.assertRaises(ValueError):
            prompts.parse_optional_number("grande")

    def test_rejects_zero(self):
        with self.assertRaises(ValueError):
            prompts.parse_optional_number("0")

    def test_rejects_a_negative_size(self):
        with self.assertRaises(ValueError):
            prompts.parse_optional_number("-10")


class SizePromptTests(unittest.TestCase):
    def test_shows_the_template_size(self):
        self.assertIn("46", prompts.size_prompt("Tamano de fuente", 46.0))

    def test_drops_a_pointless_trailing_zero(self):
        self.assertNotIn("46.0", prompts.size_prompt("Tamano de fuente", 46.0))

    def test_keeps_a_real_decimal(self):
        self.assertIn("26.9", prompts.size_prompt("Tamano de fuente", 26.9))

    def test_keeps_the_label(self):
        self.assertTrue(prompts.size_prompt("Tamano de fuente", 59.0).startswith("Tamano de fuente"))

    def test_says_enter_keeps_it(self):
        self.assertIn("Enter", prompts.size_prompt("Tamano de fuente", 59.0))

    def test_falls_back_when_the_size_is_unknown(self):
        self.assertIn("template", prompts.size_prompt("Tamano de fuente", None))


if __name__ == "__main__":
    unittest.main()
