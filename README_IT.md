# Nsis7z NSIS Plugin

**Plugin NSIS per l'estrazione di archivi 7z, ZIP e NSIS**

---

## Versioni Disponibili

| Versione                          | 7-Zip       | Formati                            | Note                          |
| --------------------------------- | ----------- | ---------------------------------- | ----------------------------- |
| [19.00](7zip-19.00/README.md)     | 7-Zip 19.00 | 7z, LZMA, XZ, Split                | Versione originale aggiornata |
| [25.01](7zip-25.01/README.md)     | 7-Zip 25.01 | 7z, ZIP, LZMA, XZ, Split, **NSIS** | Con supporto NSIS archive     |
| [**26.00**](7zip-26.00/README.md) | 7-Zip 26.00 | 7z, ZIP, LZMA, XZ, Split, **NSIS** | **Consigliata**               |

## Architetture Supportate

| Architettura      | Descrizione          |
| ----------------- | -------------------- |
| x86-ansi          | 32-bit ANSI (legacy) |
| x86-unicode       | 32-bit Unicode       |
| **amd64-unicode** | 64-bit Unicode       |

## Quick Start

```nsis
!addplugindir "plugins\x86-unicode"

Section
  ; Estrazione semplice (7z, ZIP, NSIS)
  Nsis7z::Extract "$EXEDIR\data.7z"

  ; Con testo di progresso nella label
  Nsis7z::ExtractWithDetails "$EXEDIR\data.7z" "Installing %s..."

  ; Con callback per mostrare i file nella listbox
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

Il repo include un unico script unificato `build_plugin.py` che sostituisce i precedenti script per-versione.

### Compilazione

```powershell
# Raccomandato: 7-Zip 26.00 con toolset rilevato automaticamente
python build_plugin.py

# Seleziona versione 7-Zip (19.00 | 25.01 | 26.00)
python build_plugin.py --7zip-version 25.01

# Toolset specifico (2022|2026|auto)
python build_plugin.py --toolset 2022

# Stampa versione ed esce
python build_plugin.py --version
```

## Struttura Repository

```
ns7zip/
├── build_plugin.py              # Script di build unificato (tutte le versioni)
├── rebuild_nsis7z1900-src.ps1   # Ricostruisce sorgenti 19.00
├── 7zip-19.00/                  # 7-Zip 19.00 modificato
├── 7zip-25.01/                  # 7-Zip 25.01 modificato (ZIP + NSIS handler)
└── 7zip-26.00/                  # 7-Zip 26.00 modificato (ZIP + NSIS handler)
```

## Modifiche rispetto all'originale

### NSIS Archive Handler (25.01, 26.00)
Aggiunto supporto per estrarre archivi `.exe` creati con NSIS (non presente nel plugin originale):
- `Archive\Nsis\NsisHandler.cpp/h`
- `Archive\Nsis\NsisIn.cpp/h`
- `Archive\Nsis\NsisDecode.cpp/h`
- `Archive\Nsis\NsisRegister.cpp`
- `Compress\BZip2Decoder.cpp/h` (richiesto da NsisDecode)
- `Compress\BZip2Crc.cpp`

### Bug Fix (25.01, 26.00)
- **Divide-by-zero**: aggiunto guard `if (totalSize == 0) return 0` in `GetPercentComplete`
- **ExtractWithFileCallback**: callback NSIS triggerata solo al cambio filename (evita crash con `totalSize = UINT64_MAX` alla prima chiamata `SetTotal`)

## License

- **7-Zip**: LGPL 2.1 + BSD 3-clause
- **Plugin NSIS**: Afrow UK

## Credits

- Igor Pavlov (7-Zip)
- Afrow UK (Plugin originale)
- Simone (Supporto x64, VS2022/VS2026, ZIP, NSIS handler, ExtractWithFileCallback)
