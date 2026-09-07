"""Where the templates live, what is inside them, and where After Effects is.

Every comp, layer and font name here was read out of the .aepx files rather
than assumed.  If you rename layers in After Effects, update this file.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ICON_FONT = "FontAwesome7Brands-Regular"
#: Fallback only -- the real body font is read off the layer at run time.
DEFAULT_BODY_FONT = "ZeroesTwo"
OM_TEMPLATE = "ProRes4444_Alpha"
RS_TEMPLATE = "AutoZocalos_RS"

TEMPLATES: dict[str, dict] = {
    "rotulo": {
        "label": "Rótulo (nombre + redes sociales)",
        "file": "rotulo.aepx",
        "comp": "Comp 1",
        "fps": 60,
        "render_seconds": None,
        "fields": {
            "name": {"comp": "BLOQUE NOMBRE", "layer": "Rodrigo Lo Cicero", "icon": False},
            "social1": {"comp": "rotulin", "layer": "desc 4", "icon": True},
            "social2": {"comp": "rotulin", "layer": "desc 5", "icon": True},
            "social3": {"comp": "rotulin", "layer": "desc 6", "icon": True},
        },
    },
    "musica": {
        "label": "Música (tema + juego)",
        "file": "Zocalo Musica.aepx",
        "comp": "Zocalo Export",
        "fps": 60,
        "render_seconds": 7.0,
        "fields": {
            "song": {"comp": "Zocalo Edit", "layer": "NOMBRE DEL TEMA", "icon": False},
            "game": {"comp": "Zocalo Edit", "layer": "NOMBRE DEL JUEGO", "icon": False},
        },
    },
}

_ADOBE = Path(r"C:\Program Files\Adobe")
_VERSION = re.compile(r"After Effects (\d+)")


def newest_install(candidates: list[Path]) -> Path | None:
    """Pick the highest-numbered After Effects from discovered aerender paths."""
    if not candidates:
        return None

    def version(path: Path) -> int:
        match = _VERSION.search(str(path))
        return int(match.group(1)) if match else 0

    return max(candidates, key=version)


def support_dir() -> Path | None:
    """The AE "Support Files" directory, overridable with the AE_HOME env var."""
    override = os.environ.get("AE_HOME")
    if override:
        candidate = Path(override)
        return candidate if candidate.is_dir() else None
    found = list(_ADOBE.glob("Adobe After Effects */Support Files/aerender.exe"))
    newest = newest_install(found)
    return newest.parent if newest else None


def template_path(name: str) -> Path:
    return PROJECT_ROOT / TEMPLATES[name]["file"]
