"""Start the desktop app using only its installed runtime and assets."""
import os
import runpy
import sys
from pathlib import Path

runtime = Path(sys.executable).parent
os.environ["TCL_LIBRARY"] = str(runtime / "tcl" / "tcl8.6")
os.environ["TK_LIBRARY"] = str(runtime / "tcl" / "tk8.6")
runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
