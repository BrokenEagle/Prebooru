@echo off

echo.
echo ----Checking Python levels----
echo.
where python.exe
if errorlevel 1 (
    echo Python not installed.
    GOTO :EOF
)
for /f "delims=" %%a in ('python.exe --version ^| findstr /N /R /C:"Python[ ]3\.[789]"') do set SUPPORTED_VERSION=%%a
if "%SUPPORTED_VERSION%"=="" (
    echo Python version must be 3.7 - 3.9.
    GOTO :EOF
)
set SUPPORTED_VERSION=
echo.

echo ----Installing Dependencies----
echo.
pip install -r requirements.txt
echo.

echo Done!
