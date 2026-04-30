@echo off
:: Build ns7zip using 7-Zip 26.00 sources (default)
:: Usage: build_2600.cmd [--toolset 2022|2026|auto] [...]
setlocal
python "%~dp0build_plugin.py" --7zip-version 26.00 %*
exit /b %errorlevel%
