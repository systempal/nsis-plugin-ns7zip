@echo off
:: Build ns7zip using 7-Zip-zstd sources (mcmilk fork)
:: Usage: build_zstd.cmd [--toolset 2022|2026|auto] [...]
setlocal
python "%~dp0build_plugin.py" --7zip-version zstd %*
exit /b %errorlevel%
