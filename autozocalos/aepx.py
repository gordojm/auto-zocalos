"""Read text layer content and styling out of an .aepx project.

After Effects stores a text layer in a ``<btdk>`` element whose ``bdata``
attribute is hex for a CoolType document -- a PostScript-style dictionary whose
strings are UTF-16BE, BOM first, wrapped in parentheses.

This module only reads.  Nothing here writes to a project file.
"""

from __future__ import annotations

import binascii
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections.abc import Iterator

NS = "{http://www.adobe.com/products/aftereffects}"

# Decoded UTF-16 strings are fenced with these markers so they can be told
# apart from the surrounding dictionary syntax.
_OPEN, _CLOSE = "\x01", "\x02"

# The document body: /1 [ << /0 << /0 (<text>) ...
_SOURCE_TEXT = re.compile(r"/1 \[ << /0 << /0 " + _OPEN + "([^" + _CLOSE + "]*)" + _CLOSE)

# A character style run: /6 << /0 <font index> /1 <size> /2 false /3 false /4 true
_FONT_SIZE = re.compile(
    r"/6 << /0 \d+ /1 ([0-9.]+) /2 (?:false|true) /3 (?:false|true) /4 (?:false|true)"
)

_ESCAPES = {
    ord("n"): 0x0A, ord("r"): 0x0D, ord("t"): 0x09,
    ord("b"): 0x08, ord("f"): 0x0C,
}


def _read_ps_string(blob: bytes, start: int) -> tuple[bytes, int]:
    """Read one parenthesised PostScript string starting at ``blob[start]``."""
    i = start + 1
    depth = 1
    out = bytearray()
    while i < len(blob):
        ch = blob[i]
        if ch == 0x5C:  # backslash
            nxt = blob[i + 1]
            if 0x30 <= nxt <= 0x37:  # octal escape, up to three digits
                digits = ""
                i += 1
                while i < len(blob) and len(digits) < 3 and 0x30 <= blob[i] <= 0x37:
                    digits += chr(blob[i])
                    i += 1
                out.append(int(digits, 8) & 0xFF)
                continue
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if ch == 0x28:
            depth += 1
        elif ch == 0x29:
            depth -= 1
            if depth == 0:
                return bytes(out), i + 1
        out.append(ch)
        i += 1
    return bytes(out), i


def decode_btdk(hex_data: str) -> str:
    """Decode a btdk blob, fencing its UTF-16 strings with the marker bytes."""
    blob = binascii.unhexlify(hex_data)
    out = bytearray()
    i = 0
    while i < len(blob):
        if blob[i] == 0x28:
            raw, i = _read_ps_string(blob, i)
            if raw.startswith(b"\xfe\xff"):
                decoded = raw[2:].decode("utf-16-be", "replace")
                out += _OPEN.encode() + decoded.encode("utf-8") + _CLOSE.encode()
            else:
                out += b"(" + raw + b")"
            continue
        out.append(blob[i])
        i += 1
    return out.decode("utf-8", "replace")


def _first_string(element: ET.Element) -> str | None:
    for child in element:
        if child.tag == NS + "string":
            return child.text
    return None


def _text_layers(path: Path) -> Iterator[tuple[str, str, str]]:
    """Yield (comp name, layer name, decoded document) for every text layer."""
    root = ET.parse(path).getroot()
    for item in root.iter(NS + "Item"):
        comp = _first_string(item)
        if comp is None:
            continue
        for layer in item.findall(f".//{NS}Layr"):
            btdk = layer.find(f".//{NS}btdk")
            if btdk is None:
                continue
            name = _first_string(layer)
            if name is None:
                continue
            yield comp, name, decode_btdk(btdk.get("bdata", ""))


def read_layer_texts(path: Path) -> dict[tuple[str, str], str]:
    """Map (comp name, layer name) -> raw source text, for text layers only.

    The text is returned exactly as stored, including its trailing carriage
    returns, so callers can preserve a layer's blank lines.
    """
    texts: dict[tuple[str, str], str] = {}
    for comp, name, document in _text_layers(path):
        match = _SOURCE_TEXT.search(document)
        if match:
            texts[(comp, name)] = match.group(1)
    return texts


def read_layer_font_sizes(path: Path) -> dict[tuple[str, str], float]:
    """Map (comp name, layer name) -> the size the layer's text is set in.

    The search starts after the source text: the style runs that precede it are
    document defaults (always 12.0), not what is on screen.
    """
    sizes: dict[tuple[str, str], float] = {}
    for comp, name, document in _text_layers(path):
        text_at = _SOURCE_TEXT.search(document)
        if text_at is None:
            continue
        style = _FONT_SIZE.search(document, text_at.end())
        if style:
            sizes[(comp, name)] = float(style.group(1))
    return sizes
