# Nsis7z NSIS Plugin

NSIS plugin for extracting 7z, ZIP and NSIS archives.

---

## Available Versions

| Version | 7-Zip | Formats | Notes |
|---------|-------|---------|-------|
| [19.00](7zip-19.00/README.md) | 7-Zip 19.00 | 7z, LZMA, XZ, Split | Original updated version |
| [25.01](7zip-25.01/README.md) | 7-Zip 25.01 | 7z, ZIP, LZMA, XZ, Split, **NSIS** | With NSIS archive support |
| [**26.00**](7zip-26.00/README.md) | 7-Zip 26.00 | 7z, ZIP, LZMA, XZ, Split, **NSIS** | **Recommended** |

## Supported Architectures

| Architecture | Description |
|--------------|-------------|
| x86-ansi | 32-bit ANSI (legacy) |
| x86-unicode | 32-bit Unicode |
| **amd64-unicode** | 64-bit Unicode |

## Quick Start

```nsis
!addplugindir "plugins\x86-unicode"

Section
  ; Simple extraction (7z, ZIP, NSIS)
  Nsis7z::Extract "$EXEDIR\data.7z"

  ; With progress text in label
  Nsis7z::ExtractWithDetails "$EXEDIR\data.7z" "Installing %s..."

  ; With callback to show files in listbox
  GetFunctionAddress $0 MyExtractCallback
  Nsis7z::ExtractWithFileCallback "$EXEDIR\data.7z" $0
SectionEnd

Function MyExtractCallback
  Pop $0   ; completedSize
  Pop $1   ; totalSize
  Pop $2   ; fileName
  DetailPrint "$2"
FunctionEnd
```

## Build Scripts

The repo includes a single unified `build_plugin.py` script that replaces the previous per-version scripts.

### Build

```powershell
# Recommended: 7-Zip 26.00 with auto-detected toolset
python build_plugin.py

# Select 7-Zip version (19.00 | 25.01 | 26.00)
python build_plugin.py --7zip-version 25.01

# Specific toolset (2022|2026|auto)
python build_plugin.py --toolset 2022

# Linux host path (cross-build with MinGW-w64, 26.00)
python build_plugin.py --host linux

# Print version and exit
python build_plugin.py --version
```

Linux notes:
- Local Linux path currently supports `--7zip-version 26.00`.
- Requires MinGW-w64 toolchains (`x86_64-w64-mingw32-*` and `i686-w64-mingw32-*`) and `make`.

## Repository Structure

```
nsis-plugin-ns7zip/
├── build_plugin.py              # Unified build script (all versions)
├── build_zstd.cmd               # Build script for 7-zip-zstd variant
├── rebuild_nsis7z1900-src.ps1   # Rebuilds 19.00 sources
├── versions/
│   ├── 19.00/                   # 7-Zip 19.00 modified
│   ├── 25.01/                   # 7-Zip 25.01 modified (ZIP + NSIS handler)
│   ├── 26.00/                   # 7-Zip 26.00 modified (ZIP + NSIS handler)
│   └── 7-zip-zstd/              # 7-Zip zstd fork (submodule)
├── plugins/                     # Compiled DLLs output
├── tools/
│   ├── fix_vcxproj.py           # Project file patcher
│   ├── update_gitea_releases.py # Backfill Gitea release bodies (one-shot)
│   ├── release-notes/           # Per-version Markdown snippets
│   ├── linux/                   # Linux-specific build helpers
│   └── legacy/                  # Old per-version build scripts
└── .github/workflows/
    ├── build.yml                # CI: Windows + Linux matrix build
    └── release.yml              # Release: build artifacts + publish to GitHub & Gitea
```

## CI / Release Workflow

- **build.yml** — runs on every push/PR; builds all three configs on Windows (MSBuild) and Linux (MinGW-w64) in parallel.
- **release.yml** — triggered by a `v*` tag push; builds and packages artifacts, creates a GitHub Release with the relevant CHANGELOG section as body, and updates the corresponding Gitea release body via API (`GITEA_TOKEN` secret required).

## Changes from Original

### NSIS Archive Handler (25.01, 26.00)
Added support for extracting `.exe` archives created with NSIS (not present in the original plugin):
- `Archive\Nsis\NsisHandler.cpp/h`
- `Archive\Nsis\NsisIn.cpp/h`
- `Archive\Nsis\NsisDecode.cpp/h`
- `Archive\Nsis\NsisRegister.cpp`
- `Compress\BZip2Decoder.cpp/h` (required by NsisDecode)
- `Compress\BZip2Crc.cpp`

### Bug Fixes (25.01, 26.00)
- **Divide-by-zero**: added guard `if (totalSize == 0) return 0` in `GetPercentComplete`
- **ExtractWithFileCallback**: NSIS callback triggered only on filename change (avoids crash with `totalSize = UINT64_MAX` on first `SetTotal` call)

## License

- **7-Zip**: LGPL 2.1 + BSD 3-clause
- **NSIS Plugin**: Afrow UK

## Credits

- Igor Pavlov (7-Zip)
- Afrow UK (Original plugin)
- Simone (x64 support, VS2022/VS2026, ZIP, NSIS handler, ExtractWithFileCallback)

---

*See [README_IT.md](README_IT.md) for the Italian version.*
