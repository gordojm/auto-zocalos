import unittest

from autozocalos import icons


class PlatformTableTests(unittest.TestCase):
    def test_kick_is_not_offered(self):
        labels = [label for label, _ in icons.PLATFORMS]
        self.assertNotIn("Kick", labels)
        self.assertFalse(any("kick" in l.lower() for l in labels))

    def test_offers_a_no_icon_choice_with_no_glyph(self):
        self.assertIn(("No icon", None), icons.PLATFORMS)

    def test_instagram_maps_to_its_font_awesome_codepoint(self):
        self.assertEqual(dict(icons.PLATFORMS)["Instagram"], "\uf16d")


class ResolveGlyphTests(unittest.TestCase):
    def test_returns_the_glyph_when_the_font_provides_it(self):
        self.assertEqual(icons.resolve_glyph("Instagram", {0xF16D}), "\uf16d")

    def test_returns_none_when_the_font_lacks_the_glyph(self):
        self.assertIsNone(icons.resolve_glyph("Instagram", set()))

    def test_returns_none_for_the_no_icon_choice(self):
        self.assertIsNone(icons.resolve_glyph("No icon", {0xF16D}))

    def test_returns_none_for_an_unknown_platform(self):
        self.assertIsNone(icons.resolve_glyph("Kick", {0xF16D}))


class CmapParsingTests(unittest.TestCase):
    def test_every_offered_platform_glyph_exists_in_the_installed_font(self):
        available = icons.load_available_codepoints()
        missing = [
            label
            for label, glyph in icons.PLATFORMS
            if glyph is not None and ord(glyph) not in available
        ]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
