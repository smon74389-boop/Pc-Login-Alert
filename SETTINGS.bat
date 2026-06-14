@echo off
title PC Login Monitor — Settings
color 0B

:: ─────────────────────────────────────────────────────
::  Find Python
:: ─────────────────────────────────────────────────────
set PY=

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PY="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :found
)

for %%P in (
  "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
  "C:\Python313\python.exe"
  "C:\Python312\python.exe"
  "C:\Python311\python.exe"
  "C:\Python310\python.exe"
) do (
  if exist %%P ( set PY=%%P & goto :found )
)

where py >nul 2>&1
if not errorlevel 1 (
    py -c "import sys; exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
    if not errorlevel 1 ( set PY=py & goto :found )
)

echo.
echo  Python not found. Please reinstall Python.
pause & exit /b 1

:found

:: ─────────────────────────────────────────────────────
::  Open Settings Window
:: ─────────────────────────────────────────────────────
%PY% "%~dp0monitor.py" --settings
