#!/usr/bin/env python3
"""Build script for nsis7z NSIS plugin.

Wraps per-version/per-toolset build scripts.
Defaults: 7-Zip 26.00, VS2026 (v145 toolset)
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path


class Colors:
    CYAN = "\033[36m";  GREEN = "\033[32m";  YELLOW = "\033[33m"
    RED = "\033[31m";   GRAY = "\033[90m";   RESET = "\033[0m"
    BOLD = "\033[1m";   BRIGHT_CYAN = "\033[96m"


ROOT = Path(__file__).resolve().parent
SCRIPTS = {
    "19.00": {"2022": "tools/legacy/build_plugin_vs2022.py",
               "2026": "tools/legacy/build_plugin_vs2026.py"},
    "25.01": {"2022": "tools/legacy/build_plugin_2501_vs2022.py",
               "2026": "tools/legacy/build_plugin_2501_vs2026.py"},
    "26.00": {"2022": None,
               "2026": "tools/legacy/build_plugin_2600_vs2026.py"},
    "zstd":  {"2022": None,
               "2026": "tools/legacy/build_plugin_zstd_vs2026.py"},
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build nsis7z NSIS plugin")
    parser.add_argument("--7zip-version", dest="zip_version",
                        choices=["19.00", "25.01", "26.00", "zstd"], default="26.00",
                        help="7-Zip version to build (default: 26.00); "
                             "'zstd' uses mcmilk/7-Zip-zstd submodule")
    parser.add_argument("--toolset", choices=["2022", "2026", "auto"], default="auto",
                        help="Visual Studio toolset version (default: auto)")
    parser.add_argument("--version", action="store_true",
                        help="Print plugin version and exit")
    known, rest = parser.parse_known_args()

    if known.version:
        print((ROOT / "VERSION").read_text(encoding="utf-8-sig").strip())
        return 0

    ver = (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip()
    zip_label = "7z-ZS" if known.zip_version == "zstd" else f"7z {known.zip_version}"
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}=== Building ns7zip v{ver} "
          f"({zip_label}) ==={Colors.RESET}")

    toolset = known.toolset
    if toolset == "auto":
        toolset = "2026"

    script_rel = SCRIPTS[known.zip_version][toolset]
    if script_rel is None:
        print(f"ERROR: no {known.zip_version} script for toolset {toolset}", file=sys.stderr)
        return 1
    script = ROOT / script_rel
    return subprocess.run([sys.executable, str(script)] + rest).returncode


if __name__ == "__main__":
    sys.exit(main())
