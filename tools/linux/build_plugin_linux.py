#!/usr/bin/env python3
"""Linux build path for nsis7z plugin.

Builds Windows DLL artifacts from Linux using MinGW-w64 cross compilers.
Current support: 7-Zip 26.00.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SUPPORTED = {"26.00"}

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


def _build_one(
    zip_version: str,
    cfg_name: str,
    verbose: bool,
    jobs: int,
    clean: bool,
    cleanup_artifacts: bool,
) -> int:
    cfg = CONFIGS[cfg_name]
    triplet = cfg["triplet"]

    bundle_dir = ROOT / "versions" / zip_version / "CPP" / "7zip" / "Bundles" / "Nsis7z"
    cpp_root = ROOT / "versions" / zip_version / "CPP"
    makefile = bundle_dir / "makefile.gcc"
    if not makefile.exists():
        print(f"ERROR: Linux makefile not found: {makefile}", file=sys.stderr)
        return 1

    out_obj = f"_o_{cfg_name.replace('-', '_')}"
    local_flags = "-DNDEBUG"
    if cfg["unicode"]:
        local_flags += " -DUNICODE -D_UNICODE"
    else:
        # Precomp.h forces UNICODE=1 unconditionally; suppress it for the ansi
        # build so that LPTSTR resolves to char* consistently in all TUs.
        local_flags += " -DZ7_NO_UNICODE"

    base_cmd = [
        "make",
        "-f",
        "makefile.gcc",
        f"O={out_obj}",
        "SystemDrive=1",
        "IS_MINGW=1",
        "MSYSTEM=LINUX",
        f"IS_X64={cfg['is_x64']}",
        f"CC={triplet}-gcc",
        f"CXX={triplet}-g++",
        f"RC={triplet}-windres",
        f"LOCAL_FLAGS_EXTRA={local_flags} -Wno-unknown-pragmas",
        f"CXX_INCLUDE_FLAGS=-I{cpp_root}",
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

    built = bundle_dir / out_obj / "nsis7z.dll"
    if not built.exists():
        print(f"ERROR: expected artifact not found: {built}", file=sys.stderr)
        return 1

    dest = ROOT / cfg["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, dest)

    if cleanup_artifacts:
        shutil.rmtree(bundle_dir / out_obj, ignore_errors=True)

    if verbose:
        print(f"[linux] Copied -> {dest}")
        if cleanup_artifacts:
            print(f"[linux] Cleaned build artifacts -> {bundle_dir / out_obj}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Linux build path for nsis7z")
    parser.add_argument(
        "--7zip-version",
        dest="zip_version",
        choices=["19.00", "25.01", "26.00", "zstd"],
        default="26.00",
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
    args = parser.parse_args()

    if args.zip_version not in SUPPORTED:
        print(
            "ERROR: Linux local build is currently supported only for 26.00. "
            f"Requested: {args.zip_version}",
            file=sys.stderr,
        )
        return 2

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
        )
        if code != 0:
            return code

    print("[linux] Build completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
