"""FontAwesome brand icons for the social-media lines.

Codepoints were taken from the glyph table of the installed
"Font Awesome 7 Brands" OTF, not from documentation.  Kick is deliberately
absent: the family ships no ``kick`` glyph, only the unrelated ``kickstarter``.
"""

from __future__ import annotations

import os
import struct
from pathlib import Path

PLATFORMS: list[tuple[str, str | None]] = [
    ("Instagram", "\uf16d"),
    ("Facebook", "\uf09a"),
    ("Internet Explorer", "\uf26b"),
    ("TikTok", "\ue07b"),
    ("YouTube", "\uf167"),
    ("X (Twitter)", "\ue61b"),
    ("Spotify", "\uf1bc"),
    ("Twitch", "\uf1e8"),
    ("No icon", None),
]

FONT_GLOB = "Font Awesome*Brands*.otf"


def font_path() -> Path | None:
    """Locate the installed FontAwesome Brands OTF, per-user install first."""
    roots = [
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")),
        Path(os.path.expandvars(r"%WINDIR%\Fonts")),
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for match in sorted(root.glob(FONT_GLOB), reverse=True):
            return match
    return None


def parse_codepoints(data: bytes) -> set[int]:
    """Return every codepoint mapped by an sfnt font's cmap table."""
    if len(data) < 12:
        return set()
    num_tables = struct.unpack(">H", data[4:6])[0]
    cmap_off = None
    for i in range(num_tables):
        rec = 12 + i * 16
        tag, _checksum, off, _len = struct.unpack(">4sIII", data[rec:rec + 16])
        if tag == b"cmap":
            cmap_off = off
            break
    if cmap_off is None:
        return set()

    codepoints: set[int] = set()
    subtable_count = struct.unpack(">H", data[cmap_off + 2:cmap_off + 4])[0]
    for i in range(subtable_count):
        rec = cmap_off + 4 + i * 8
        _pid, _eid, rel = struct.unpack(">HHI", data[rec:rec + 8])
        sub = cmap_off + rel
        fmt = struct.unpack(">H", data[sub:sub + 2])[0]
        if fmt == 4:
            codepoints |= _format4(data, sub)
        elif fmt == 12:
            codepoints |= _format12(data, sub)
    return codepoints


def _format4(data: bytes, sub: int) -> set[int]:
    seg_x2 = struct.unpack(">H", data[sub + 6:sub + 8])[0]
    segs = seg_x2 // 2
    ends = struct.unpack(f">{segs}H", data[sub + 14:sub + 14 + seg_x2])
    starts_at = sub + 16 + seg_x2
    starts = struct.unpack(f">{segs}H", data[starts_at:starts_at + seg_x2])
    deltas_at = starts_at + seg_x2
    deltas = struct.unpack(f">{segs}h", data[deltas_at:deltas_at + seg_x2])
    ranges_at = deltas_at + seg_x2
    ranges = struct.unpack(f">{segs}H", data[ranges_at:ranges_at + seg_x2])

    found: set[int] = set()
    for i in range(segs):
        for cp in range(starts[i], min(ends[i], 0xFFFF) + 1):
            if cp == 0xFFFF:
                continue
            if ranges[i] == 0:
                gid = (cp + deltas[i]) & 0xFFFF
            else:
                at = ranges_at + i * 2 + ranges[i] + (cp - starts[i]) * 2
                if at + 2 > len(data):
                    continue
                gid = struct.unpack(">H", data[at:at + 2])[0]
                if gid:
                    gid = (gid + deltas[i]) & 0xFFFF
            if gid:
                found.add(cp)
    return found


def _format12(data: bytes, sub: int) -> set[int]:
    groups = struct.unpack(">I", data[sub + 12:sub + 16])[0]
    found: set[int] = set()
    for i in range(groups):
        at = sub + 16 + i * 12
        start, end, _gid = struct.unpack(">III", data[at:at + 12])
        found.update(range(start, end + 1))
    return found


def load_available_codepoints(path: Path | None = None) -> set[int]:
    """Codepoints the installed FontAwesome Brands font can actually render."""
    path = path or font_path()
    if path is None or not path.is_file():
        return set()
    return parse_codepoints(path.read_bytes())


def resolve_glyph(platform: str, available: set[int] | frozenset[int]) -> str | None:
    """The glyph for *platform*, or None when unknown or unsupported by the font.

    Returning None is what makes the caller emit the handle with no icon and no
    leading space, per the "unsupported characters are not appended" rule.
    """
    glyph = dict(PLATFORMS).get(platform)
    if glyph is None:
        return None
    return glyph if ord(glyph) in available else None
