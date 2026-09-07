"""Native Windows folder picker."""

from __future__ import annotations

import tkinter
from pathlib import Path
from tkinter import filedialog


def ask_folder(title: str = "Elegi la carpeta de destino") -> Path | None:
    """Show the system folder dialog.  None when the user cancels."""
    root = tkinter.Tk()
    root.withdraw()
    # Without this the dialog opens behind the terminal window.
    root.attributes("-topmost", True)
    root.update()
    try:
        chosen = filedialog.askdirectory(title=title, mustexist=True, parent=root)
    finally:
        root.destroy()
    return Path(chosen) if chosen else None
