#!/usr/bin/env python3
# Rewrite vcxproj files in *-bundle directories to use direct relative paths
# to the vendor submodule, removing the dependency on POSIX symlinks.
#
# Usage: python3 tools/fix_bundle_vcxproj_paths.py [--dry-run]
#
# Before this script the vcxproj paths were:
#   ..\..\..\..\C\         (4 levels = bundle root, then symlink)
#   ..\..\..\Common\       (3 levels = bundle CPP, then symlink)
#   ..\..\Archive\         (2 levels = bundle 7zip, then symlink)
#
# After this script (same as versions/zstd bundle):
#   ..\..\..\..\..\VER\C\                (5 levels = versions/, then vendor)
#   ..\..\..\..\..\VER\CPP\Common\       (5 levels)
#   ..\..\..\..\..\VER\CPP\7zip\Archive\ (5 levels)
#
# UI\NSIS paths are kept as-is (real bundle files, no symlink needed).

import re
import os
import sys

bs = "\\"

BUNDLES = {
    "25.01": "versions/25.01-bundle/CPP/7zip/Bundles/Nsis7z",
    "26.00": "versions/26.00-bundle/CPP/7zip/Bundles/Nsis7z",
    "26.01": "versions/26.01-bundle/CPP/7zip/Bundles/Nsis7z",
}


def fix_path(path, v7z, vcpp, vc):
    """Rewrite a single Include= path value."""
    p = path
    # depth-4: ..\..\..\..\  → vendor root
    prefix4 = bs.join([".."] * 4) + bs
    if p.startswith(prefix4):
        rest = p[len(prefix4):]
        # C\ or C
        if rest.startswith("C" + bs) or rest == "C":
            suffix = rest[2:] if rest.startswith("C" + bs) else ""
            return vc + (bs + suffix if suffix else "")
        # generic (shouldn't appear, but handle gracefully)
        return vcpp + bs + ".." + bs + rest
    # depth-3: ..\..\..\ → vendor CPP
    prefix3 = bs.join([".."] * 3) + bs
    if p.startswith(prefix3):
        rest = p[len(prefix3):]
        return vcpp + bs + rest
    # depth-2: ..\..\ → vendor CPP\7zip\  (except UI\NSIS which stays)
    prefix2 = bs.join([".."] * 2) + bs
    if p.startswith(prefix2):
        rest = p[len(prefix2):]
        if rest.startswith("UI" + bs + "NSIS"):
            return path  # bundle-local real file
        return v7z + bs + rest
    # depth-0: local bundle file
    return path


def transform_file(fpath, ver, dry_run):
    vendor  = bs.join([".."] * 5) + bs + ver
    v7z     = vendor + bs + "CPP" + bs + "7zip"
    vcpp    = vendor + bs + "CPP"
    vc      = vendor + bs + "C"
    old_inc = bs.join([".."] * 3) + bs + ";"

    with open(fpath, "rb") as f:
        raw = f.read()
    # Detect BOM
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    content = raw.lstrip(b"\xef\xbb\xbf").decode("utf-8")

    lines = content.splitlines(keepends=True)
    out = []
    changed = 0

    for line in lines:
        orig = line

        # Fix AdditionalIncludeDirectories
        if "<AdditionalIncludeDirectories>" in line:
            # Remove spurious trailing space before semicolon
            line = re.sub(r"(\.\.[/\\]\.\.)[/\\]\s+;", r"\1" + bs + ";", line)
            # Replace "..\..\..\;" with vendor paths
            if old_inc in line:
                new_inc = vcpp + bs + ";" + vendor + bs + ";" + old_inc
                line = line.replace(old_inc, new_inc)

        # Fix ClCompile / ClInclude Include paths
        m = re.search(r'(Include=")([^"]+)(")', line)
        if m and ("<ClCompile" in line or "<ClInclude" in line):
            newpath = fix_path(m.group(2), v7z, vcpp, vc)
            if newpath != m.group(2):
                line = line[: m.start()] + m.group(1) + newpath + m.group(3) + line[m.end():]

        if line != orig:
            changed += 1
        out.append(line)

    new_content = "".join(out)
    print(f"  {os.path.basename(fpath)}: {changed} lines changed")
    if not dry_run and changed > 0:
        with open(fpath, "wb") as f:
            f.write(bom + new_content.encode("utf-8"))


def main():
    dry_run = "--dry-run" in sys.argv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if dry_run:
        print("DRY RUN — no files will be written\n")

    for ver, rel_dir in BUNDLES.items():
        bundle_dir = os.path.join(root, rel_dir)
        print(f"version {ver}:")
        for fname in ["Nsis7z.vcxproj", "Nsis7z_vs2026.vcxproj"]:
            fpath = os.path.join(bundle_dir, fname)
            if not os.path.exists(fpath):
                print(f"  {fname}: SKIP (not found)")
                continue
            transform_file(fpath, ver, dry_run)


if __name__ == "__main__":
    main()
