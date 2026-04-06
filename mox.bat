@echo off
REM Windows launcher for mox.py using isolated venv in /venv/venv/

REM cd to repo root so all scripts see a consistent cwd; pushd/popd restores caller's directory
pushd "%~dp0"

REM Ensure the venv exists and requirements are installed
python %~dp0venv\venv.py
IF %ERRORLEVEL% NEQ 0 (popd & exit /b %ERRORLEVEL%)

REM Add venv Scripts folder to PATH
SET "PATH=%~dp0venv\venv\Scripts;%PATH%"

REM Run the script with venv python
%~dp0venv\venv\Scripts\python.exe %~dp0scripts\mox.py %*
SET MOX_EXIT=%errorlevel%
popd
exit /b %MOX_EXIT%
