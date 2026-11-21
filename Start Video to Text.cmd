@echo off
setlocal
cd /d "%~dp0"
set "TCL_LIBRARY=%~dp0runtime\tcl\tcl8.6"
set "TK_LIBRARY=%~dp0runtime\tcl\tk8.6"
start "" "%~dp0runtime\pythonw.exe" -E -s "%~dp0app\app.py"
