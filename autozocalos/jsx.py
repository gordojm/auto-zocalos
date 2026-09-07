r"""Generate the ExtendScript that rewrites the text inside a temp project.

Text is written through After Effects' own DOM rather than by patching the
.aepx: a text layer's btdk blob caches per-character glyph IDs and advances and
records style-run lengths, all of which must agree with the string.  Letting AE
set the text keeps them in sync.

The generated script is pure ASCII -- ExtendScript does not reliably read UTF-8
without a BOM, so every accent and icon travels as a \uXXXX escape.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LayerEdit:
    """One layer to touch.  ``text=None`` leaves the text alone."""

    comp: str
    layer: str
    text: str | None
    icon_run: bool = False
    font_size: float | None = None
    enabled: bool = True


def _js(value: object) -> str:
    """A JavaScript literal for *value*, escaped and ASCII-only."""
    return json.dumps(value, ensure_ascii=True)


_BODY = r"""
function writeStatus(ok, message, extra) {
    var file = new File(STATUS);
    file.encoding = "UTF-8";
    if (file.open("w")) {
        file.write(ok ? ("OK" + (extra || "")) : ("ERROR\n" + message));
        file.close();
    }
}

// Python needs the comp's real work area to decide the render range; the
// render-settings template would otherwise fall back to the whole comp length.
function reportComp(name) {
    if (!name) { return ""; }
    var comp = findComp(name);
    if (comp === null) { return ""; }
    return "\nfps=" + comp.frameRate +
           "\nduration=" + comp.duration +
           "\nworkAreaStart=" + comp.workAreaStart +
           "\nworkAreaDuration=" + comp.workAreaDuration;
}

function findComp(name) {
    for (var i = 1; i <= app.project.numItems; i++) {
        var item = app.project.item(i);
        if (item instanceof CompItem && item.name === name) { return item; }
    }
    return null;
}

function findLayer(comp, name) {
    for (var i = 1; i <= comp.numLayers; i++) {
        if (comp.layer(i).name === name) { return comp.layer(i); }
    }
    return null;
}

function textProperty(layer) {
    return layer.property("ADBE Text Properties").property("ADBE Text Document");
}

// The last character is always body text, whatever the leading run looks like,
// so it is the safe place to sample a layer's existing style from.
function sampleLast(prop, what) {
    var current = prop.value.text;
    if (current.length > 0) {
        try {
            var range = prop.value.characterRange(current.length - 1, current.length);
            return (what === "font") ? range.font : range.fontSize;
        } catch (err) {}
    }
    return (what === "font") ? DEFAULT_BODY_FONT : prop.value.fontSize;
}

function applyEdit(edit) {
    var comp = findComp(edit.comp);
    if (comp === null) { throw new Error("Comp not found: " + edit.comp); }
    var layer = findLayer(comp, edit.layer);
    if (layer === null) {
        throw new Error("Layer not found: " + edit.layer + " in " + edit.comp);
    }

    // The template ships with desc 6 hidden, so this has to switch layers
    // on as well as off -- not just hide the blank ones.
    layer.enabled = edit.enabled;
    if (!edit.enabled) { return; }
    if (edit.text === null) { return; }

    var prop = textProperty(layer);
    var bodyFont = sampleLast(prop, "font");
    var size = (edit.fontSize === null) ? sampleLast(prop, "size") : edit.fontSize;

    // Style the document and write it back ONCE.  Ranges written afterwards,
    // off prop.value, land on a detached copy and are silently discarded --
    // that left every social line rendered in the icon font.
    var length = edit.text.length;
    var doc = prop.value;
    doc.text = edit.text;
    doc.characterRange(0, length).font = bodyFont;
    doc.characterRange(0, length).fontSize = size;

    // The glyph and its separating space take the icon font.
    if (edit.iconRun && length >= 2) {
        doc.characterRange(0, 2).font = ICON_FONT;
    }
    prop.setValue(doc);
}

try {
    app.beginSuppressDialogs();
    app.open(new File(PROJECT));

    // Both templates ship with a queued H.264 item; aerender would render it too.
    var queue = app.project.renderQueue;
    while (queue.numItems > 0) { queue.item(1).remove(); }

    for (var i = 0; i < EDITS.length; i++) { applyEdit(EDITS[i]); }

    app.project.save(new File(PROJECT));
    writeStatus(true, "", reportComp(REPORT_COMP));
} catch (err) {
    writeStatus(false, err.toString() + (err.line ? (" (line " + err.line + ")") : ""), "");
}

try { app.endSuppressDialogs(false); } catch (err) {}
app.quit();
"""


def build_jsx(
    project_path: Path,
    edits: list[LayerEdit],
    status_path: Path,
    icon_font: str,
    default_body_font: str,
    report_comp: str | None = None,
) -> str:
    payload = [
        {
            "comp": edit.comp,
            "layer": edit.layer,
            "text": edit.text,
            "iconRun": edit.icon_run,
            "fontSize": edit.font_size,
            "enabled": edit.enabled,
        }
        for edit in edits
    ]
    header = "\n".join(
        [
            "var PROJECT = " + _js(str(project_path)) + ";",
            "var STATUS = " + _js(str(status_path)) + ";",
            "var ICON_FONT = " + _js(icon_font) + ";",
            "var DEFAULT_BODY_FONT = " + _js(default_body_font) + ";",
            "var REPORT_COMP = " + _js(report_comp) + ";",
            "var EDITS = " + _js(payload) + ";",
        ]
    )
    return header + "\n" + _BODY
