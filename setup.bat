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
if not "%SUPPORTED_VERSION%"=="" (
    set REQUIREMENTS_FILE=requirements.txt
    goto INSTALL
)
for /f "delims=" %%a in ('python.exe --version ^| findstr /N /R /C:"Python[ ]3\.1[01]"') do set SUPPORTED_VERSION=%%a
if not "%SUPPORTED_VERSION%"=="" (
    set REQUIREMENTS_FILE=requirements-3.10+.txt
    goto INSTALL
)
echo Python version must be 3.7 - 3.11.
GOTO :EOF

:INSTALL
echo ----Installing Dependencies----
echo.
pip install wheel
pip install -r %REQUIREMENTS_FILE%
echo %REQUIREMENTS_FILE%
echo.
set SUPPORTED_VERSION=
echo.
echo Done!
