@echo off
:: Generic wrapper for build_plugin.py
:: Usage: build.cmd [--7zip-version 19.00|25.01|26.00|zstd] [--toolset 2022|2026|auto] [...]
::   Default: --7zip-version 26.00 --toolset auto
setlocal
python "%~dp0build_plugin.py" %*
exit /b %errorlevel%
