@echo off

echo ----Setting Environment Variables----
set FLASK_APP=prebooru

if "%~1"=="development" goto development

set FLASK_ENV=production
goto end

:development
set FLASK_ENV=development

:end
echo.
