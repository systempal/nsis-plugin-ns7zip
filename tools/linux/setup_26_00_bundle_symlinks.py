#!/usr/bin/env python3
"""Creates symlinks in versions/26.00-bundle to mirror vendor directory structure."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
bundle_root = ROOT / "versions/26.00-bundle"
vendor_root = ROOT / "versions/26.00"
bundle_7zip = bundle_root / "CPP/7zip"
vendor_7zip = vendor_root / "CPP/7zip"
bundle_cpp  = bundle_root / "CPP"
vendor_cpp  = vendor_root / "CPP"

# Root-level symlinks: C and Asm
for name in ("C", "Asm"):
    target = bundle_root / name
    if not target.exists() and not target.is_symlink():
        rel = os.path.relpath(vendor_root / name, bundle_root)
        os.symlink(rel, target)
        print(f"  symlink: {target.relative_to(ROOT)} -> {rel}")

for item in vendor_7zip.iterdir():
    target = bundle_7zip / item.name
    if not target.exists() and not target.is_symlink():
        rel = os.path.relpath(item, bundle_7zip)
        os.symlink(rel, target)
        print(f"  symlink: {target.relative_to(ROOT)} -> {rel}")

bundle_ui = bundle_7zip / "UI"
vendor_ui = vendor_7zip / "UI"
bundle_ui.mkdir(exist_ok=True)
for item in vendor_ui.iterdir():
    target = bundle_ui / item.name
    if not target.exists() and not target.is_symlink():
        rel = os.path.relpath(item, bundle_ui)
        os.symlink(rel, target)
        print(f"  symlink: {target.relative_to(ROOT)} -> {rel}")

for item in vendor_cpp.iterdir():
    if item.name == "7zip":
        continue
    target = bundle_cpp / item.name
    if not target.exists() and not target.is_symlink():
        rel = os.path.relpath(item, bundle_cpp)
        os.symlink(rel, target)
        print(f"  symlink: {target.relative_to(ROOT)} -> {rel}")

print("Done")
