# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e il progetto aderisce al [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.2.1] — 2026-05-02

### Added
- Linux CI jobs for the GitHub `build` and `release` workflows using the MinGW-w64 cross-build path

### Changed
- GitHub Actions workflows now opt into Node 24 for JavaScript-based actions to avoid Node 20 deprecation warnings

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

[Unreleased]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.2.1...HEAD
[2.2.1]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.2.0...v2.2.1
[2.1.0]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.0.1...v2.1.0
[2.0.1]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/compare/v2.0.0...v2.0.1
[2.0.0]: https://gitea.emulab.it/Simone/nsis-plugin-ns7zip/releases/tag/v2.0.0
