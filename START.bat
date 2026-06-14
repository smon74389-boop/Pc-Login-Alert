@echo off
title PC Login Monitor
color 0A

:: ─────────────────────────────────────────────────────
::  Find Python  (checks real locations, skips Store stub)
:: ─────────────────────────────────────────────────────
set PY=

:: Check the exact path where winget just installed Python 3.11
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PY="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :found
)

:: Other common real locations
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

:: py launcher
where py >nul 2>&1
if not errorlevel 1 (
    py -c "import sys; exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
    if not errorlevel 1 ( set PY=py & goto :found )
)

echo.
echo  Python not found. Please run this as Administrator or reinstall Python.
pause & exit /b 1

:found

:: ─────────────────────────────────────────────────────
::  Install packages if missing  (first run only)
:: ─────────────────────────────────────────────────────
%PY% -c "import win32api, pystray, PIL, cv2, google.auth" >nul 2>&1
if errorlevel 1 (
    echo  Installing packages - one time only, please wait...
    %PY% -m pip install pywin32 pystray Pillow opencv-python google-auth-oauthlib google-api-python-client google-auth-httplib2 --quiet
    echo  Done.
)

:: ─────────────────────────────────────────────────────
::  Launch  -  UAC dialog will pop up, click YES
:: ─────────────────────────────────────────────────────
%PY% "%~dp0monitor.py"
