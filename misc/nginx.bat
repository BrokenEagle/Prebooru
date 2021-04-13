@echo off

pushd "C:\Program Files (x86)\nginx-1.19.10\"
if "%~1"=="start" (
    echo Starting image server.
    start nginx.exe
)
if "%~1"=="stop" (
    echo Stopping image server.
    nginx.exe -s stop
)
popd