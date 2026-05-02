#!/usr/bin/env python3
"""Thin wrapper — delegates to setup_bundle_symlinks.py for version 25.01."""
import subprocess, sys, pathlib
script = pathlib.Path(__file__).parent / "setup_bundle_symlinks.py"
sys.exit(subprocess.call([sys.executable, str(script), "25.01"]))
