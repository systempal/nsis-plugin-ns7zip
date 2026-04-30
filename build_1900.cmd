@echo off
:: Build ns7zip using 7-Zip 19.00 sources
:: Usage: build_1900.cmd [--toolset 2022|2026|auto] [...]
setlocal
python "%~dp0build_plugin.py" --7zip-version 19.00 %*
exit /b %errorlevel%
