"""Interactive entry point: ask, build, render, clean up."""

from __future__ import annotations

import shutil
import tempfile
import time
from collections.abc import Collection
from pathlib import Path

from autozocalos import aepx, build, config, icons, jsx, picker, prompts, render, text

SOCIAL_HINT = "se escribe tal cual, con @ o / si corresponde"


def preflight(
    support_dir: Path | None,
    ae_running: bool,
    glyphs: Collection[int],
    root: Path,
) -> list[str]:
    """Everything that would make a run fail, reported before any work starts."""
    problems: list[str] = []

    if support_dir is None:
        problems.append(
            "No encontré After Effects. Instalalo, o definí AE_HOME apuntando a su carpeta "
            "'Support Files'."
        )
    else:
        for exe in ("aerender.exe", "AfterFX.exe"):
            if not (support_dir / exe).is_file():
                problems.append(f"Falta {exe} en {support_dir}.")

    if ae_running:
        problems.append(
            "After Effects está abierto. Cerralo antes de seguir: el script termina con "
            "app.quit() y cerraría tu sesión."
        )

    for spec in config.TEMPLATES.values():
        if not (root / spec["file"]).is_file():
            problems.append(f"Falta el template {spec['file']} en {root}.")

    if not glyphs:
        problems.append(
            "No encontré la fuente Font Awesome Brands instalada; los íconos no se podrían agregar."
        )
    return problems


def read_status(path: Path) -> str | None:
    """None when the ExtendScript succeeded, otherwise its error message."""
    if not path.is_file():
        return "El script de After Effects no escribió ningún estado."
    content = path.read_text(encoding="utf-8", errors="replace").strip()
    if content.startswith("OK"):
        return None
    return content[len("ERROR"):].strip() or "Error desconocido."


def read_comp_info(path: Path) -> dict[str, float]:
    """The numeric key=value lines the ExtendScript appended after "OK"."""
    if not path.is_file():
        return {}
    info: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        key, _, value = line.partition("=")
        try:
            info[key.strip()] = float(value)
        except ValueError:
            continue
    return info


def wait_for(path: Path, timeout: float = 600.0) -> None:
    """Give AfterFX.exe time to finish when it returns before the script does."""
    deadline = time.monotonic() + timeout
    while not path.is_file() and time.monotonic() < deadline:
        time.sleep(1.0)


def _ask_socials(glyphs: Collection[int]) -> list[tuple[str, str] | None]:
    """Ask for handles until one is left blank; the rest stay hidden.

    Every slot is optional, including the first, so the block can render with no
    social lines at all.
    """
    labels = [label for label, _ in icons.PLATFORMS]
    socials: list[tuple[str, str] | None] = []
    stopped = False

    for slot in (1, 2, 3):
        if stopped:
            socials.append(None)
            continue
        handle = prompts.ask_optional(f"Red social {slot} ({SOCIAL_HINT})")
        if not handle:
            stopped = True
            socials.append(None)
            continue
        platform = prompts.choose(f"Plataforma para {handle}", labels)
        if platform != "No icon" and icons.resolve_glyph(platform, set(glyphs)) is None:
            print(f"  Aviso: la fuente instalada no tiene el ícono de {platform}; va sin ícono.")
        socials.append((platform, handle))

    return socials


def collect_rotulo(originals: dict, sizes: dict, glyphs: Collection[int]):
    fields = config.TEMPLATES["rotulo"]["fields"]
    name_layer = (fields["name"]["comp"], fields["name"]["layer"])

    name = prompts.ask_required("Nombre")
    socials = _ask_socials(glyphs)
    # Optional sizes are always asked last.
    size = prompts.ask_optional_number("Tamaño de fuente del nombre", sizes.get(name_layer))

    return {"name": name}, build.rotulo_edits(name, size, socials, originals, glyphs)


def collect_musica(originals: dict, sizes: dict):
    song_field = config.TEMPLATES["musica"]["fields"]["song"]
    song_layer = (song_field["comp"], song_field["layer"])

    song = prompts.ask_required("Nombre del tema")
    game = prompts.ask_required("Nombre del juego")
    # Optional sizes are always asked last.
    size = prompts.ask_optional_number("Tamaño de fuente del tema", sizes.get(song_layer))

    values = {"song": text.to_caps(song), "game": text.to_caps(game)}
    return values, build.musica_edits(song, size, game, originals)


def main() -> int:
    print("=== auto-zócalos ===")

    glyphs = icons.load_available_codepoints()
    support = config.support_dir()
    problems = preflight(support, render.after_effects_running(), glyphs, config.PROJECT_ROOT)
    if problems:
        print("\nNo puedo continuar:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    assert support is not None

    by_label = {spec["label"]: key for key, spec in config.TEMPLATES.items()}
    template = by_label[prompts.choose("¿Qué zócalo querés generar?", list(by_label))]
    spec = config.TEMPLATES[template]
    source = config.template_path(template)
    originals = aepx.read_layer_texts(source)
    sizes = aepx.read_layer_font_sizes(source)

    if template == "rotulo":
        values, edits = collect_rotulo(originals, sizes, glyphs)
    else:
        values, edits = collect_musica(originals, sizes)

    print("\nElegí la carpeta de destino en la ventana que se abrió...")
    folder = picker.ask_folder()
    if folder is None:
        print("Cancelado: no elegiste carpeta.")
        return 1

    output = text.unique_output_path(folder, build.output_stem(template, values))

    workdir = Path(tempfile.mkdtemp(prefix="autozocalos-"))
    temp_project = workdir / source.name
    status_path = workdir / "status.txt"
    script_path = workdir / "apply.jsx"

    # The original template is only ever read; all edits happen on this copy.
    shutil.copy2(source, temp_project)
    script_path.write_text(
        jsx.build_jsx(
            project_path=temp_project,
            edits=edits,
            status_path=status_path,
            icon_font=config.ICON_FONT,
            default_body_font=config.DEFAULT_BODY_FONT,
            report_comp=spec["comp"],
        ),
        encoding="ascii",
    )

    print("\nAplicando textos en After Effects (puede tardar)...")
    render.run_streaming(render.afterfx_argv(support / "AfterFX.exe", script_path))
    wait_for(status_path)

    failure = read_status(status_path)
    if failure is not None:
        print(f"\nNo pude modificar el proyecto: {failure}")
        print(f"Archivos de trabajo (para revisar): {workdir}")
        return 1

    info = read_comp_info(status_path)
    window = render.render_range(info, spec["render_seconds"])
    if window is None:
        start_frame, end_frame, total = 0, None, 0
        print("\nAviso: no pude leer el área de trabajo; se renderiza la composición entera.")
    else:
        start_frame, end_frame = window
        total = end_frame - start_frame + 1
        fps = info.get("fps") or spec["fps"]
        print(f"\nRango: fotogramas {start_frame}-{end_frame} ({total} = {total / fps:.3f}s)")

    print(f"Renderizando: {output}")
    echo = render.progress_reporter(total) if total else None
    code = render.run_streaming(
        render.aerender_argv(
            exe=support / "aerender.exe",
            project=temp_project,
            comp=spec["comp"],
            output=output,
            om_template=config.OM_TEMPLATE,
            rs_template=config.RS_TEMPLATE,
            start_frame=start_frame,
            end_frame=end_frame,
        ),
        echo=echo,
    )

    if code != 0 or not output.is_file() or output.stat().st_size == 0:
        print(f"\nEl render falló (código {code}).")
        print(
            f"Revisá que existan las plantillas '{config.OM_TEMPLATE}' y "
            f"'{config.RS_TEMPLATE}' en After Effects."
        )
        print(f"Archivos de trabajo (para revisar): {workdir}")
        return 1

    shutil.rmtree(workdir, ignore_errors=True)
    print(f"\n¡Listo! {output}")
    return 0
