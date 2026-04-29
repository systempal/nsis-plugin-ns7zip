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

# Print version and exit
python build_plugin.py --version
```

## Repository Structure

```
ns7zip/
├── build_plugin.py              # Unified build script (all versions)
├── rebuild_nsis7z1900-src.ps1   # Rebuilds 19.00 sources
├── 7zip-19.00/                  # 7-Zip 19.00 modified
├── 7zip-25.01/                  # 7-Zip 25.01 modified (ZIP + NSIS handler)
└── 7zip-26.00/                  # 7-Zip 26.00 modified (ZIP + NSIS handler)
```

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
