@echo off
:: Build ns7zip using 7-Zip 25.01 sources
:: Usage: build_2501.cmd [--toolset 2022|2026|auto] [...]
setlocal
python "%~dp0build_plugin.py" --7zip-version 25.01 %*
exit /b %errorlevel%
