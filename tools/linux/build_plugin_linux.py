#!/usr/bin/env python3
"""Linux build path for nsis7z plugin.

Builds Windows DLL artifacts from Linux using MinGW-w64 cross compilers.
Supported versions: 7-Zip 25.01, 26.00 and zstd.

All project-owned build-infrastructure files (makefile.gcc, Nsis7z.def) live
under tools/linux/overlay/ and are never written into the vendor source trees.
Build artifacts go to _linux_build/<version>/<cfg>/ (gitignored).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

OVERLAY = ROOT / "tools" / "linux" / "overlay"
BUILD_DIR = ROOT / "_linux_build"

SUPPORTED = {"25.01", "26.00", "26.01", "zstd"}

# For all versions the upstream vendor does NOT ship a Nsis7z bundle, so a
# *-bundle wrapper directory mirrors the vendor tree via symlinks and provides
# project-owned sources (NSIS UI, wrapper cpp files, vcxproj).
#
# For zstd the 7-zip C++ sources live in the 7-zip-zstd submodule while our
# NSIS wrapper sits in versions/zstd-bundle/.  make is run with -C pointing to the
# wrapper dir and VENDOR_7ZIP overridden to the submodule tree so that
# include/source rules resolve correctly without touching the submodule.
VERSION_LAYOUT = {
    "25.01": {
        "vendor_7zip": ROOT / "versions" / "25.01" / "CPP" / "7zip",
        "bundle_dir":  ROOT / "versions" / "25.01-bundle" / "CPP" / "7zip" / "Bundles" / "Nsis7z",
    },
    "26.00": {
        "vendor_7zip": ROOT / "versions" / "26.00" / "CPP" / "7zip",
        "bundle_dir":  ROOT / "versions" / "26.00-bundle" / "CPP" / "7zip" / "Bundles" / "Nsis7z",
    },
    "26.01": {
        "vendor_7zip": ROOT / "versions" / "26.01" / "CPP" / "7zip",
        "bundle_dir":  ROOT / "versions" / "26.01-bundle" / "CPP" / "7zip" / "Bundles" / "Nsis7z",
    },
    # zstd: make runs in our wrapper dir; vendor_7zip points to submodule tree.
    "zstd": {
        "vendor_7zip": ROOT / "versions" / "7-zip-zstd" / "CPP" / "7zip",
        "bundle_dir":  ROOT / "versions" / "zstd-bundle" / "CPP" / "7zip" / "Bundles" / "Nsis7z",
    },
}

# Per-version extra flags for GCC/MinGW cross-compilation that apply to both
# C and C++ compilations.  Passed via LOCAL_FLAGS_EXTRA → merged into CFLAGS
# and CXXFLAGS alike.
VERSION_EXTRA_FLAGS: dict[str, str] = {
    # fast-lzma2 (part of the 7-zip-zstd vendor) triggers -Wsign-compare and
    # -Wcast-function-type on C code that was never compiled with GCC -Werror.
    "zstd": "-Wno-sign-compare -Wno-cast-function-type",
}

# Per-version C++-only extra flags for GCC/MinGW cross-compilation.
# These compensate for vendor code written exclusively for MSVC.
# Passed via LOCAL_CXXFLAGS_EXTRA → appended to CXXFLAGS only (not CFLAGS).
#
# If flag-based suppression is insufficient (e.g. the code must be modified),
# place a patched copy at tools/linux/overlay/src/<version>/<relative-path>
# and add a rule override in makefile.gcc using the OVERLAY_SRC variable.
VERSION_EXTRA_CXXFLAGS: dict[str, str] = {
    # 7-zip 25.01 NSIS UI code was never compiled with GCC:
    #   - STDMETHODIMP implementations lack `noexcept`/`throw()` while the COM
    #     interface macros (Z7_COM7F_IMP) declare the virtuals with `throw()`
    #     (= noexcept in C++17). Fixed per-TU via -include z7_idecl_noexcept_strip.h
    #     in the specific makefile rule for NsisExtractCallbackConsole.o.
    #   - Several unused parameters and sign-compare on UInt64 vs. literal -1.
    "25.01": "-Wno-sign-compare -Wno-unused-parameter",
    # 7-zip-zstd NSIS UI code has the same unused-parameter issues as 25.01.
    # sign-compare is in C code (fast-lzma2) and already in VERSION_EXTRA_FLAGS;
    # unused-parameter warnings are C++-only (NSIS wrapper and nsis7z.cpp).
    "zstd": "-Wno-unused-parameter",
}

CONFIGS = {
    "x86-ansi": {
        "triplet": "i686-w64-mingw32",
        "is_x64": "0",
        "unicode": False,
        "dest": "plugins/x86-ansi/nsis7z.dll",
    },
    "x86-unicode": {
        "triplet": "i686-w64-mingw32",
        "is_x64": "0",
        "unicode": True,
        "dest": "plugins/x86-unicode/nsis7z.dll",
    },
    "x64-unicode": {
        "triplet": "x86_64-w64-mingw32",
        "is_x64": "1",
        "unicode": True,
        "dest": "plugins/amd64-unicode/nsis7z.dll",
    },
}


def _require_tool(name: str) -> None:
    if shutil.which(name) is None:
        print(f"ERROR: required tool not found: {name}", file=sys.stderr)
        sys.exit(2)


def _resolve_jobs(value: str) -> int:
    if value == "auto":
        return max(1, os.cpu_count() or 1)

    jobs = int(value)
    if jobs < 1:
        raise ValueError("jobs must be >= 1")
    return jobs


def _ensure_bundle_symlinks(zip_version: str, bundle_dir: Path, vendor_7zip: Path) -> None:
    """Recreate bundle symlinks if they are missing (e.g. after a fresh clone).

    Symlinks are no longer committed to git (they are POSIX-only and break
    Windows clones), so they must be created on-the-fly on Linux before make
    can resolve the relative source paths inside the bundle directory.
    """
    # A sentinel: if the vendor C/ directory is not reachable via the bundle
    # root symlink, assume all symlinks need to be (re)created.
    sentinel = bundle_dir.parents[3] / "C"  # bundle/CPP/7zip/../../../C = bundle/C
    if sentinel.exists():
        return  # symlinks already in place

    setup_script = ROOT / "tools" / "linux" / "setup_bundle_symlinks.py"
    print(f"[linux] Bundle symlinks missing for {zip_version}, recreating via {setup_script.name} ...")
    proc = subprocess.run(
        [sys.executable, str(setup_script), zip_version],
        cwd=ROOT,
    )
    if proc.returncode != 0:
        print(f"ERROR: setup_bundle_symlinks.py failed for {zip_version}", file=sys.stderr)
        sys.exit(proc.returncode)


def _build_one(
    zip_version: str,
    cfg_name: str,
    verbose: bool,
    jobs: int,
    clean: bool,
    cleanup_artifacts: bool,
    dist: bool = False,
) -> int:
    layout = VERSION_LAYOUT[zip_version]
    vendor_7zip = layout["vendor_7zip"]
    bundle_dir  = layout["bundle_dir"]

    # Symlinks are not committed to git; recreate them on Linux if missing.
    if zip_version in VERSION_LAYOUT:
        _ensure_bundle_symlinks(zip_version, bundle_dir, vendor_7zip)

    cfg = CONFIGS[cfg_name]
    triplet = cfg["triplet"]

    # Output objects go to an absolute path under _linux_build/ so nothing
    # temporary is ever written into the vendor source trees.
    out_dir = BUILD_DIR / zip_version / cfg_name
    out_dir.mkdir(parents=True, exist_ok=True)

    local_flags = "-DNDEBUG"
    if cfg["unicode"]:
        local_flags += " -DUNICODE -D_UNICODE"
    else:
        # Precomp.h forces UNICODE=1 unconditionally; suppress it for the ansi
        # build so that LPTSTR resolves to char* consistently in all TUs.
        local_flags += " -DZ7_NO_UNICODE"

    # Version-specific workarounds for vendor code that was MSVC-only.
    # Flags that are C++-only (e.g. -fpermissive) must go into LOCAL_CXXFLAGS_EXTRA
    # which the makefile appends only to CXXFLAGS, not to CFLAGS.
    extra_flags = VERSION_EXTRA_FLAGS.get(zip_version, "")
    extra_cxx   = VERSION_EXTRA_CXXFLAGS.get(zip_version, "")

    # CXX_INCLUDE_FLAGS:
    #   1. overlay/include – case-sensitivity shims (Windows.h → windows.h, …)
    #      searched first so they shadow the actual MinGW system headers.
    #   2. CPP root – so vendor #include paths resolve from any working dir.
    cpp_root = vendor_7zip.parent  # …/CPP
    overlay_inc = OVERLAY / "include"

    # For bundle-based builds (zstd, 26.01) the UI/NSIS wrapper files live in
    # our bundle dir, not in the vendor tree.  Override NSIS_DIR accordingly.
    bundle_nsis = bundle_dir.parent.parent / "UI" / "NSIS"

    # The 7-zip-zstd vendor calls LocalFileTimeToFileTime2() which is defined
    # in MyWindows.cpp.  That TU is normally excluded from SYS_OBJS when
    # IS_MINGW=1, so we must inject it back via EXTRA_SYS_OBJS.
    extra_sys_objs = f"{out_dir}/MyWindows.o" if zip_version == "zstd" else ""

    base_cmd = [
        "make",
        "-C", str(bundle_dir),
        "-f", str(OVERLAY / "makefile.gcc"),
        f"O={out_dir}",
        f"DEF_FILE={OVERLAY / 'Nsis7z.def'}",
        f"VENDOR_7ZIP={vendor_7zip}",
        *([ f"NSIS_DIR={bundle_nsis}" ] if bundle_nsis.is_dir() else []),
        "SystemDrive=1",
        "IS_MINGW=1",
        "MSYSTEM=LINUX",
        f"IS_X64={cfg['is_x64']}",
        f"CC={triplet}-gcc",
        f"CXX={triplet}-g++",
        f"RC={triplet}-windres",
        f"LOCAL_FLAGS_EXTRA={local_flags} -Wno-unknown-pragmas {extra_flags}".rstrip(),
        f"LOCAL_CXXFLAGS_EXTRA={extra_cxx}",
        *([ f"EXTRA_SYS_OBJS={extra_sys_objs}" ] if extra_sys_objs else []),
        # Linux ld is case-sensitive; vendor makefile uses mixed-case lib names
        # (lUser32, lOle32, …) that don't exist on disk.  Override LIB2 with
        # fully-expanded lowercase equivalents.
        "LIB2=-loleaut32 -luuid -ladvapi32 -luser32 -lole32 -lgdi32 -lcomctl32 -lcomdlg32 -lshell32 -lhtmlhelp",
        f"CXX_INCLUDE_FLAGS=-I{overlay_inc} -I{cpp_root}",
    ]

    build_mode = "clean build" if clean else "incremental build"
    print(f"[linux] Building {cfg_name} ({zip_version}, {build_mode}, -j{jobs})")

    # Don't run 'clean' and 'all' in the same parallel make invocation:
    # with -j, GNU make may execute them concurrently and remove objects while
    # the linker is already consuming them.
    if clean:
        proc = subprocess.run(base_cmd + ["clean"], cwd=bundle_dir)
        if proc.returncode != 0:
            return proc.returncode

    proc = subprocess.run(base_cmd + [f"-j{jobs}", "all"], cwd=bundle_dir)
    if proc.returncode != 0:
        return proc.returncode

    built = out_dir / "nsis7z.dll"
    if not built.exists():
        print(f"ERROR: expected artifact not found: {built}", file=sys.stderr)
        return 1

    rel_dest = cfg["dest"]
    if dist and rel_dest.startswith("plugins/"):
        rel_dest = "dist/" + rel_dest[len("plugins/"):]
    dest = ROOT / rel_dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, dest)

    if cleanup_artifacts:
        shutil.rmtree(out_dir, ignore_errors=True)

    if verbose:
        print(f"[linux] Copied -> {dest}")
        if cleanup_artifacts:
            print(f"[linux] Cleaned build artifacts -> {out_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Linux build path for nsis7z")
    parser.add_argument(
        "--7zip-version",
        dest="zip_version",
        choices=sorted(SUPPORTED),
        default="26.01",
        help="7-Zip version to build",
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        choices=list(CONFIGS.keys()) + ["all"],
        default=["all"],
        help="Build configuration(s): x86-ansi, x86-unicode, x64-unicode, or all",
    )
    parser.add_argument(
        "--jobs",
        default="auto",
        help="Parallel make jobs. Use an integer or 'auto' (default: auto)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=True,
        help="Run 'make clean' before building (default: True)",
    )
    parser.add_argument(
        "--no-clean",
        action="store_false",
        dest="clean",
        help="Skip 'make clean' to enable incremental rebuilds",
    )
    parser.add_argument(
        "--cleanup-artifacts",
        action="store_true",
        default=True,
        help="Remove per-config build artifact directories after successful copy (default: True)",
    )
    parser.add_argument(
        "--no-cleanup-artifacts",
        action="store_false",
        dest="cleanup_artifacts",
        help="Keep per-config build artifact directories (_o_*)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--dist",
        action="store_true",
        help="Copy built DLLs to <repo>/dist/<config> instead of "
             "<repo>/plugins/<config>",
    )
    args = parser.parse_args()

    _require_tool("make")
    for cfg in CONFIGS.values():
        _require_tool(f"{cfg['triplet']}-gcc")
        _require_tool(f"{cfg['triplet']}-g++")
        _require_tool(f"{cfg['triplet']}-windres")

    try:
        jobs = _resolve_jobs(args.jobs)
    except ValueError as exc:
        print(f"ERROR: invalid --jobs value: {exc}", file=sys.stderr)
        return 2

    wanted = list(CONFIGS.keys()) if "all" in args.configs else args.configs

    for cfg_name in wanted:
        code = _build_one(
            args.zip_version,
            cfg_name,
            args.verbose,
            jobs,
            args.clean,
            args.cleanup_artifacts,
            args.dist,
        )
        if code != 0:
            return code

    print("[linux] Build completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
