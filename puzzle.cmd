@echo off
rem Blindfold lichess puzzle trainer, for cmd.exe and PowerShell.
rem Uses the local .venv if one exists, otherwise whatever python is on PATH.
setlocal
set "DIR=%~dp0"
if exist "%DIR%.venv\Scripts\python.exe" (
    set "PY=%DIR%.venv\Scripts\python.exe"
) else (
    set "PY=python"
)
pushd "%DIR%"
"%PY%" -m blindpuzzle %*
set "CODE=%ERRORLEVEL%"
popd
exit /b %CODE%
