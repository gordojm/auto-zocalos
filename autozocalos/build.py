"""Turn the answers from the CLI into the list of layer edits to apply."""

from __future__ import annotations

from collections.abc import Collection

from autozocalos import config, icons, text
from autozocalos.jsx import LayerEdit

#: One social slot: (platform label, handle) -- or None when left blank.
SocialAnswer = tuple[str, str] | None


def _layer_text(body: str, original: str) -> str:
    """Body text plus whatever blank lines the layer already ended with."""
    return text.with_trailing_blanks(body, text.trailing_blank_lines(original))


def _edit(spec: dict, body: str | None, originals: dict, **kw) -> LayerEdit:
    key = (spec["comp"], spec["layer"])
    rendered = None if body is None else _layer_text(body, originals.get(key, ""))
    return LayerEdit(spec["comp"], spec["layer"], rendered, **kw)


def rotulo_edits(
    name: str,
    name_font_size: float | None,
    socials: list[SocialAnswer],
    originals: dict[tuple[str, str], str],
    available: Collection[int],
) -> list[LayerEdit]:
    fields = config.TEMPLATES["rotulo"]["fields"]
    edits = [_edit(fields["name"], name, originals, font_size=name_font_size)]

    for index, answer in enumerate(socials, start=1):
        spec = fields[f"social{index}"]
        if answer is None:
            edits.append(_edit(spec, None, originals, enabled=False))
            continue
        platform, handle = answer
        glyph = icons.resolve_glyph(platform, set(available))
        line = text.compose_social(handle, glyph)
        edits.append(_edit(spec, line, originals, icon_run=glyph is not None))
    return edits


def musica_edits(
    song: str,
    song_font_size: float | None,
    game: str,
    originals: dict[tuple[str, str], str],
) -> list[LayerEdit]:
    fields = config.TEMPLATES["musica"]["fields"]
    return [
        _edit(fields["song"], text.to_caps(song), originals, font_size=song_font_size),
        _edit(fields["game"], text.to_caps(game), originals),
    ]


def output_stem(template: str, values: dict[str, str]) -> str:
    """File name (without extension) for the rendered clip."""
    if template == "musica":
        raw = f"{values['song']} - {values['game']}"
    else:
        raw = values["name"]
    return text.sanitize_filename(raw)
