# auto-zócalos

Genera zócalos de After Effects desde la línea de comandos. Elegís la plantilla,
escribís los textos, elegís la carpeta y te deja un `.mov` ProRes 4444 con canal
alfa, listo para la timeline.

Las plantillas originales nunca se modifican: cada corrida trabaja sobre una
copia temporal que se borra al terminar.

## Qué genera

**Rótulo** — nombre + hasta tres redes sociales.

- **Nombre** (obligatorio).
- **Redes sociales 1, 2 y 3**: todas opcionales. Elegís la plataforma y se
  antepone el ícono de Font Awesome. El usuario se escribe **tal cual**: el `@`,
  la `/` o nada al principio lo ponés vos, y no se corrige nada.
- Si dejás una vacía, se corta ahí: esa y las siguientes quedan ocultas.
- **Tamaño de fuente** del nombre, opcional y al final. Enter mantiene el del
  template.

**Música** — tema + juego.

- **Nombre del tema** y **nombre del juego** (obligatorios, van en mayúsculas).
- **Tamaño de fuente** del tema, opcional y al final.
- Siempre exporta exactamente los primeros 7 segundos.

## Qué necesitás

1. **Windows** y **Python 3.11+**. No hay que instalar librerías.
2. **After Effects** (se detecta solo; si no, definí `AE_HOME` apuntando a su
   carpeta `Support Files`).
3. **Las fuentes de la carpeta [fonts/](fonts/)** instaladas: `ZeroesTwo.ttf`,
   `Kanit-SemiBoldItalic.ttf` y `Font Awesome 7 Brands-Regular-400.otf`.
   Seleccionalas, botón derecho, *Instalar*.
4. **Dos plantillas creadas dentro de After Effects**, con estos nombres exactos:
   - Módulo de salida **`ProRes4444_Alpha`** — QuickTime, Apple ProRes 4444,
     RGB + Alfa, **audio apagado**.
   - Ajustes de procesamiento **`AutoZocalos_RS`** — Óptima, Completo, velocidad
     de la composición.
5. **After Effects cerrado** antes de correr el script.

Todo esto se verifica antes de empezar y te avisa si falta algo.

## Cómo se usa

Doble clic en `generar.bat`, o desde una terminal:

```
python -m autozocalos
```

Respondés las preguntas, elegís la carpeta de destino en la ventana que se abre,
y el render arranca. El avance se muestra cada 10%.

## Notas

- Se renderiza el **área de trabajo** de la composición, la que marcaste en la
  timeline. Música es la excepción: está fijada a 7 segundos en
  [config.py](autozocalos/config.py).
- Si algo falla, la carpeta temporal **no** se borra y se imprime su ruta, para
  poder abrir el proyecto y revisarlo.
- Los nombres de composiciones y capas viven en
  [config.py](autozocalos/config.py). Si renombrás algo en After Effects,
  actualizalo ahí.

## Tests

```
python -m unittest discover -s tests -t .
```
