"""Composing the strings that get written into the After Effects layers."""

from __future__ import annotations

import re
from pathlib import Path

#: The glyph plus its separating space -- the run that takes the icon font.
ICON_RUN_LENGTH = 2

_FORBIDDEN = re.compile("[<>:\"/" + chr(92) * 2 + "|?*\x00-\x1f]")
_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def compose_social(handle: str, glyph: str | None) -> str:
    """``glyph + space + handle``, or the bare handle when there is no glyph.

    The handle is never inspected or normalised: whatever prefix it carries
    (``@``, ``/``, none at all) and whatever case it uses is what gets rendered.
    """
    if glyph is None:
        return handle
    return f"{glyph} {handle}"


def trailing_blank_lines(source_text: str) -> int:
    """Blank lines a layer ends with, ignoring its paragraph terminator."""
    terminators = len(source_text) - len(source_text.rstrip("\r"))
    return max(0, terminators - 1)


def with_trailing_blanks(body: str, blanks: int) -> str:
    return body + "\r" * blanks


def to_caps(value: str) -> str:
    return value.upper()


def sanitize_filename(name: str) -> str:
    """Make *name* safe as a Windows file name, falling back to "output"."""
    cleaned = _FORBIDDEN.sub("-", name).strip().rstrip(" .")
    if not re.search(r"[^\s\-_.]", cleaned):
        return "output"
    if cleaned.upper() in _RESERVED:
        return "_" + cleaned
    return cleaned


def unique_output_path(folder: Path, stem: str, suffix: str = ".mov") -> Path:
    """A path in *folder* that does not exist yet, suffixed rather than clobbered."""
    candidate = folder / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = folder / f"{stem} ({counter}){suffix}"
        counter += 1
    return candidate
