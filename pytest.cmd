@echo off
REM Run from project root: pytest.cmd
cd /d "%~dp0"
if exist ".venv\Scripts\pytest.exe" (
    ".venv\Scripts\pytest.exe" %*
) else (
    python -m pytest %*
)
exit /b %ERRORLEVEL%
