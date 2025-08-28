@echo off
REM Windows launcher for mox.py using isolated venv in /venv/venv/

REM Ensure the venv exists and requirements are installed
python %~dp0venv\venv.py
IF %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

REM Add venv Scripts folder to PATH
SET "PATH=%~dp0venv\venv\Scripts;%PATH%"

REM Run the script with venv python
%~dp0venv\venv\Scripts\python.exe %~dp0scripts\mox.py %*
exit /b %errorlevel%
