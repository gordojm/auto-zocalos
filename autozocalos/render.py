"""Driving AfterFX.exe and aerender.exe."""

from __future__ import annotations

import ctypes
import locale
import re
import subprocess
import sys
from pathlib import Path
from typing import TextIO


def last_frame(seconds: float, fps: float) -> int:
    """Final frame index for an exact duration, e.g. 7s @ 60fps -> 419."""
    return int(round(seconds * fps)) - 1


def render_range(
    info: dict[str, float],
    override_seconds: float | None = None,
) -> tuple[int, int] | None:
    """The (start, end) frames to render, or None to leave it to aerender.

    Defaults to the comp's work area, which is what you set on the timeline.
    Without this, aerender falls back to the render-settings template's time
    span -- "Length of Comp" -- and happily renders all 184 seconds of a comp
    whose work area is 5.5.
    """
    fps = info.get("fps")
    if not fps:
        return None

    if override_seconds is not None:
        return 0, last_frame(override_seconds, fps)

    if "workAreaDuration" not in info:
        return None

    start = int(round(info.get("workAreaStart", 0.0) * fps))
    end = start + int(round(info["workAreaDuration"] * fps)) - 1

    duration = info.get("duration")
    if duration:
        end = min(end, last_frame(duration, fps))
    return start, end


FRAME_LINE = re.compile(r"\((\d+)\):")


def console_encoding(get_codepage=None) -> str:
    """The codepage aerender actually writes in.

    On a Spanish Windows the console is cp850, where 0xA0 is "a-acute".  The
    ANSI locale (cp1252) reads that same byte as a non-breaking space, which is
    what mangled every accent in the render log.
    """
    if get_codepage is None:
        def get_codepage():
            return ctypes.windll.kernel32.GetConsoleOutputCP()
    try:
        codepage = int(get_codepage())
    except Exception:
        return locale.getpreferredencoding(False)
    if codepage == 65001:
        return "utf-8"
    if codepage <= 0:
        return locale.getpreferredencoding(False)
    return f"cp{codepage}"


def progress_reporter(total_frames: int, echo=None):
    """Collapse aerender's per-frame chatter into one line per 10%.

    aerender prints a line for every single frame; at 332 frames that is 332
    lines of noise for a 10 second render.
    """
    echo = safe_write if echo is None else echo
    state = {"bucket": 0}

    def report(line: str) -> None:
        stripped = line.strip()
        if not stripped:
            return
        if not stripped.startswith("PROGRESS:"):
            echo(line)
            return
        match = FRAME_LINE.search(stripped)
        if match is None or total_frames <= 0:
            return
        done = int(match.group(1))
        bucket = min(10, done * 10 // total_frames)
        if bucket > state["bucket"]:
            state["bucket"] = bucket
            echo(f"   {bucket * 10:3d}%   ({done}/{total_frames} fotogramas)")

    return report


def safe_write(line: str, stream: TextIO | None = None) -> None:
    """Print a line that the console may not be able to encode.

    aerender is localised, so its output carries accents and, when a byte does
    not decode, replacement characters.  A plain print() raises
    UnicodeEncodeError on a cp1252 console and would abort the render mid-way.
    """
    stream = sys.stdout if stream is None else stream
    encoding = getattr(stream, "encoding", None) or "utf-8"
    stream.write(line.encode(encoding, "replace").decode(encoding, "replace") + "\n")


def afterfx_argv(exe: Path, jsx: Path) -> list[str]:
    return [str(exe), "-noui", "-r", str(jsx)]


def aerender_argv(
    exe: Path,
    project: Path,
    comp: str,
    output: Path,
    om_template: str,
    rs_template: str,
    start_frame: int = 0,
    end_frame: int | None = None,
) -> list[str]:
    argv = [
        str(exe),
        "-project", str(project),
        "-comp", comp,
        "-RStemplate", rs_template,
        "-OMtemplate", om_template,
        "-output", str(output),
    ]
    if end_frame is not None:
        argv += ["-s", str(start_frame), "-e", str(end_frame)]
    argv += ["-close", "DO_NOT_SAVE_CHANGES"]
    return argv


def after_effects_running() -> bool:
    """True when AfterFX.exe already has a session open.

    It matters because ``AfterFX.exe -r`` attaches to a running instance and our
    script ends with app.quit(), which would close the user's own project.
    """
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq AfterFX.exe", "/NH"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return "AfterFX.exe" in result.stdout


def run_streaming(argv: list[str], echo=None) -> int:
    """Run a command, streaming its output live, and return the exit code."""
    echo = safe_write if echo is None else echo
    process = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding=console_encoding(),
        errors="replace",
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        echo(line.rstrip())
    return process.wait()
