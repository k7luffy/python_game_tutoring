@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Windows launcher for Python Maze Adventure.
rem It reuses an environment that already has pygame, and only builds one when
rem no Python on this computer has it.  Keep this file in CRLF line endings:
rem cmd.exe needs them to find the goto labels.

set "PY=.venv\Scripts\python.exe"

rem 1. The project environment, when it already imports pygame.
if not exist "%PY%" goto try_py
"%PY%" -c "import pygame" >nul 2>&1
if errorlevel 1 goto repair
goto launch_venv

:repair
echo The project environment is missing pygame. Repairing it...
"%PY%" -m pip install -r game\requirements.txt
if errorlevel 1 goto rebuild
"%PY%" -c "import pygame" >nul 2>&1
if errorlevel 1 goto rebuild
goto launch_venv

:rebuild
echo Rebuilding the project environment...
rmdir /s /q ".venv"
goto try_py

rem 2. Any Python on this computer that already has pygame can run the game.
:try_py
py -3 -c "import pygame" >nul 2>&1
if errorlevel 1 goto try_python
set "BASE=py -3"
goto launch_system

:try_python
python -c "import pygame" >nul 2>&1
if errorlevel 1 goto try_python3
set "BASE=python"
goto launch_system

:try_python3
python3 -c "import pygame" >nul 2>&1
if errorlevel 1 goto make_venv
set "BASE=python3"

:launch_system
set "PYTHONUTF8=1"
%BASE% game\main.py
if errorlevel 1 goto game_error
exit /b 0

rem 3. No pygame anywhere: build the project environment and install it.
:make_venv
echo First run: creating a Python environment (this can take a minute)...
if exist ".venv" (
  echo A .venv from another computer is here. Rebuilding it for Windows...
  rmdir /s /q ".venv"
)
set "BASE="

:pick_py
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto pick_python
set "BASE=py -3"
goto have_python

:pick_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto pick_python3
set "BASE=python"
goto have_python

:pick_python3
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto setup_error
set "BASE=python3"

:have_python
%BASE% -m venv .venv
if errorlevel 1 goto setup_error
if not exist "%PY%" goto setup_error
"%PY%" -m pip install --upgrade pip >nul 2>&1
"%PY%" -m pip install -r game\requirements.txt
if errorlevel 1 goto install_error
"%PY%" -c "import pygame" >nul 2>&1
if errorlevel 1 goto install_error

:launch_venv
set "PYTHONUTF8=1"
"%PY%" game\main.py
if errorlevel 1 goto game_error
exit /b 0

:setup_error
echo.
echo Python 3.10 or newer was not found. Install it from python.org, then run this file again.
pause
exit /b 1

:install_error
echo.
echo pygame could not be installed for this Python:
%BASE% -c "import sys; print('   ', sys.version.split()[0], sys.executable)"
echo.
echo Install Python 3.12 or 3.13 from python.org, delete the .venv folder, and try again.
pause
exit /b 1

:game_error
echo.
echo The game stopped with an error. The message above explains what happened.
pause
exit /b 1
