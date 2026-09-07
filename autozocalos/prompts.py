"""Interactive console prompts."""

from __future__ import annotations


def parse_optional_number(raw: str) -> float | None:
    """A positive font size, or None when the field was left blank.

    A comma is accepted as the decimal separator.
    """
    value = raw.strip()
    if not value:
        return None
    try:
        number = float(value.replace(",", "."))
    except ValueError:
        raise ValueError(f"'{raw}' no es un número válido.") from None
    if number <= 0:
        raise ValueError("El tamaño de fuente debe ser mayor que cero.")
    return number


def format_size(value: float) -> str:
    """46.0 -> '46', 26.9 -> '26.9'."""
    return f"{value:g}"


def size_prompt(label: str, template_size: float | None) -> str:
    """Prompt text naming the size the template currently uses."""
    if template_size is None:
        return f"{label} (Enter = valor del template): "
    return f"{label} (Enter = {format_size(template_size)} del template): "


def ask_required(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("  Este campo es obligatorio.")


def ask_optional(label: str) -> str:
    """Free text that may be left blank.  Returned verbatim, never normalised."""
    return input(f"{label}\n  (Enter para omitir): ").strip()


def ask_optional_number(label: str, template_size: float | None = None) -> float | None:
    prompt = size_prompt(label, template_size)
    while True:
        try:
            return parse_optional_number(input(prompt))
        except ValueError as err:
            print(f"  {err}")


def choose(label: str, options: list[str]) -> str:
    """Pick one option by number."""
    print(f"\n{label}")
    for index, option in enumerate(options, start=1):
        print(f"  {index}) {option}")
    while True:
        raw = input("Opción: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"  Elegí un número entre 1 y {len(options)}.")


def pause(message: str = "\nPresioná Enter para cerrar...") -> None:
    """Hold the window open so the result stays readable.

    Kept here rather than in the .bat so the ending is identical however the
    tool is launched, and tolerant of a closed stdin.
    """
    try:
        input(message)
    except (EOFError, KeyboardInterrupt):
        pass
