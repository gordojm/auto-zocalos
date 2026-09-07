import sys

from autozocalos import prompts
from autozocalos.cli import main

code = main()
# The pause lives here, not in generar.bat, so both templates and both launch
# methods end the same way: one prompt, Enter closes.
prompts.pause()
sys.exit(code)
