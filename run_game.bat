@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Windows launcher for Python Maze Adventure.
rem The first run creates .venv and installs the packages; later runs start at once.
rem Keep this file in CRLF line endings: cmd.exe needs them to find the goto labels.

set "PY=.venv\Scripts\python.exe"

if exist "%PY%" goto launch

echo First run: creating a Python environment (this can take a minute)...
if exist ".venv" (
  echo A .venv from another computer is here. Rebuilding it for Windows...
  rmdir /s /q ".venv"
)
set "BASE="

:try_py
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto try_python
set "BASE=py -3"
goto have_python

:try_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto try_python3
set "BASE=python"
goto have_python

:try_python3
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto setup_error
set "BASE=python3"

:have_python
%BASE% -m venv .venv
if errorlevel 1 goto setup_error
if not exist "%PY%" goto setup_error

"%PY%" -m pip install --upgrade pip >nul 2>&1
"%PY%" -m pip install -r game\requirements.txt
if errorlevel 1 goto setup_error

:launch
rem UTF-8 for any text the game or Python prints to the console.
set "PYTHONUTF8=1"
"%PY%" game\main.py
if errorlevel 1 goto game_error
exit /b 0

:setup_error
echo.
echo Could not set up Python. Install Python 3.10 or newer from python.org and try again.
pause
exit /b 1

:game_error
echo.
echo The game stopped with an error. The message above explains what happened.
pause
exit /b 1
