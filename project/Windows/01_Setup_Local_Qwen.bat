@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 launch.py setup
    goto done
)
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python launch.py setup
    goto done
)
echo Python 3.10 or later is required. Install Python from python.org and enable Add Python to PATH.
exit /b 1
:done
set "RESULT=%ERRORLEVEL%"
echo.
pause
exit /b %RESULT%
