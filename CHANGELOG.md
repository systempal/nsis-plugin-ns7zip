# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e il progetto aderisce al [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.3.1] — 2026-05-05

### Added
- `tools/update_github_releases.py`: one-shot script to sync GitHub Release bodies via API using local `tools/release-notes/` snippets

### Fixed
- Linux overlay shims (`tools/linux/overlay/include/`) now use `#include_next` instead of `#include` to forward to the real MinGW system header, avoiding infinite preprocessor recursion on Linux/WSL (GCC 12+)
- Removed stale prebuilt `plugins/*/nsis7z.dll` binaries from the repository

## [2.3.0] — 2026-05-03

### Added
- Auto-recreation of bundle POSIX symlinks on Linux if missing after a fresh clone (`_ensure_bundle_symlinks()` in `tools/linux/build_plugin_linux.py`)

### Changed
- Default 7-zip version changed from `26.00` to `26.01` in `build_plugin.py` and `tools/linux/build_plugin_linux.py`
- Renamed `versions/zstd` → `versions/zstd-bundle` for naming consistency with the other bundle directories
- Auto-generated bundle symlinks are now excluded from git tracking (`.gitignore`)

### Fixed
- Windows build error `C1083: Cannot open include file` for `Common/Common.h`, `IPassword.h`, `C/Alloc.h` and other vendor headers: added `versions/VER/CPP/7zip/UI/Common/` to `AdditionalIncludeDirectories` in all five bundle vcxproj files (25.01, 26.00, 26.01)
- f-string nested-quote syntax errors in all `tools/legacy/` build scripts (patterns `{"="*60}`, `{"-"*50}`, `{'Rebuild' if ...}`): replaced with Python 3.10/3.11-compatible equivalents

### Removed
- One-shot `tools/fix_bundle_vcxproj_paths.py` helper (no longer needed)

## [2.2.2] — 2026-05-02

### Added
- `tools/update_gitea_releases.py`: one-shot script to backfill Gitea release bodies with CHANGELOG content via the Gitea API
- `tools/release-notes/`: per-version Markdown snippets used by the backfill script

### Changed
- Release workflow now extracts the relevant CHANGELOG section and uses it as the GitHub Release body (`body_path`)
- Release workflow adds a step to update the corresponding Gitea release body via API (`GITEA_TOKEN` secret)
- All GitHub Actions upgraded to node24-native major versions (no more Node 20 deprecation warnings)

## [2.2.1] — 2026-05-02

### Added
- Linux CI jobs for the GitHub `build` and `release` workflows using the MinGW-w64 cross-build path

### Changed
- GitHub Actions workflows now opt into Node 24 for JavaScript-based actions to avoid Node 20 deprecation warnings

## [2.2.0] — 2026-05-02

### Added
- Linux MinGW-w64 cross-build support in `build_plugin.py` via `--host linux`
- `tools/linux/build_plugin_linux.py` for standalone Linux builds
- Color output and progress spinner in all legacy build scripts

### Changed
- `build_plugin.py` now supports both Windows (MSBuild) and Linux (MinGW-w64) targets
- Windows build-script f-string fixes

## [2.1.0] — 2026-04-30

### Added
- NSIS plugin API (`pluginapi.cpp`/`pluginapi.h`) for 7-Zip zstd build
- `ExtractCallbackConsole` class for extraction progress and user input
- Main extraction logic (`Main.cpp`, `MainAr.cpp`) for the zstd bundle
- User input utilities (`UserInputUtils2`) for password handling and prompts
- Break signal handling (`NSISBreak`) for graceful interruption
- `Nsis7z_vs2026.vcxproj` (v145 toolset) for Visual Studio 2026 builds
- `tools/fix_vcxproj.py` helper for project file patching
- `versions/7-zip-zstd` submodule added
- `build_zstd.cmd` top-level build script for the zstd variant

## [2.0.1] — 2026-04-29

### Fixed
- Restored `tools/legacy/` build scripts lost from repository
- Fixed `UnicodeEncodeError` on CI: replaced Unicode checkmarks with ASCII OK/FAIL in build summary
- Fixed MSB8020 toolset error on GitHub Actions: `build_plugin_2600_vs2026.py` now detects the installed VS toolset dynamically (falls back to v143 on VS2022 runners)
- Build script for 26.00 selects `Nsis7z_vs2026.vcxproj` (v145) or `Nsis7z.vcxproj` (v143) based on detected toolset

## [2.0.0] — 2026-04-29

### Added
- Prima release come repository indipendente
- Build script unificato (`build_plugin.py`) con CLI canonica
- CI/CD via GitHub Actions (mirror automatico Gitea → GitHub)
- Documentazione completa (README, CONTRIBUTING, SECURITY)

[Unreleased]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.3.1...HEAD
[2.3.1]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.3.0...v2.3.1
[2.3.0]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.2.2...v2.3.0
[2.2.2]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.2.1...v2.2.2
[2.2.1]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.2.0...v2.2.1
[2.2.0]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.1.0...v2.2.0
[2.1.0]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.0.1...v2.1.0
[2.0.1]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.0.0...v2.0.1
[2.0.0]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/releases/tag/v2.0.0
