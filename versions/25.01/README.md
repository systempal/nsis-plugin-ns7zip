# Nsis7z Plugin - 7-Zip 25.01

**Plugin NSIS per l'estrazione di archivi 7z e ZIP**

## Informazioni

| Proprietà        | Valore                                                        |
|------------------|---------------------------------------------------------------|
| Versione 7-Zip   | 25.01                                                         |
| Autore originale | Afrow UK                                                      |
| Basato su        | 7-Zip by Igor Pavlov                                          |
| Modifiche        | Supporto ZIP, x64, VS2022/VS2026, ExtractWithFileCallback     |

## Formati Supportati

| Formato  | Estensione | Crittografia              |
|----------|------------|---------------------------|
| 7z       | .7z        | AES-256                   |
| **ZIP**  | .zip       | ZipCrypto, WzAES-256      |
| LZMA     | .lzma      | —                         |
| XZ       | .xz        | —                         |
| Split    | .001       | —                         |

### Codec 7z Supportati

- LZMA / LZMA2
- PPMd
- BCJ / BCJ2 (filtri)
- Delta
- Copy

### Codec ZIP Supportati

- Deflate / Deflate64
- LZMA
- ZSTD (Zstandard)
- PPMd
- Implode
- Shrink

## Architetture

| Architettura    | Descrizione           |
|-----------------|-----------------------|
| x86-ansi        | 32-bit ANSI (legacy)  |
| x86-unicode     | 32-bit Unicode        |
| amd64-unicode   | 64-bit Unicode        |

## Novità rispetto alla versione 19.00

1. **Supporto ZIP** - Estrazione di file ZIP, inclusi quelli criptati
2. **7-Zip 25.01** - 6 anni di miglioramenti (2019→2025)
3. **Nuovi codec** - ZSTD, migliori performance LZMA
4. **Sicurezza** - Fix vulnerabilità scoperte tra 2019-2025
5. **Ottimizzazioni** - Supporto CPU moderne (AVX2)

## Usage

```nsis
!addplugindir "plugins\x86-unicode"

Section
  ; Extract 7z archive
  Nsis7z::ExtractWithDetails "$EXEDIR\data.7z" "Installing package %s..."
  
  ; Extract ZIP archive
  Nsis7z::ExtractWithDetails "$EXEDIR\data.zip" "Installing package %s..."
  
  ; Or simple extraction
  Nsis7z::Extract "$EXEDIR\archive.7z"
SectionEnd
```

### Functions

#### Nsis7z::Extract

```nsis
Nsis7z::Extract "archive.7z"
```

Extracts the archive to `$OUTDIR` silently.

#### Nsis7z::ExtractWithDetails

```nsis
Nsis7z::ExtractWithDetails "archive.7z" "Installing %s..."
```

Extracts the archive showing progress with the specified format string.

#### Nsis7z::ExtractWithCallback

```nsis
Nsis7z::ExtractWithCallback "archive.7z" callback_function
```

Extracts with a callback that receives `completedSize` and `totalSize`.

#### Nsis7z::ExtractWithFileCallback (Nuovo)

```nsis
Nsis7z::ExtractWithFileCallback "archive.7z" callback_function
```

Extracts with a callback that receives `completedSize`, `totalSize` and `fileName`.

> Questa funzione è stata aggiunta nella versione personale.

## Compilazione

### Requisiti

- Visual Studio 2022 o 2026 con workload C++
- Python 3.x

### Build

```powershell
cd ns7zip

# VS2022
python build_plugin_2501_vs2022.py

# VS2026
python build_plugin_2501_vs2026.py
```

### Opzioni

```powershell
# Solo una configurazione
python build_plugin_2501_vs2022.py --configs x64-unicode

# Verbosity minima
python build_plugin_2501_vs2022.py --verbosity minimal

# Help
python build_plugin_2501_vs2022.py --help
```

## Dimensioni DLL

| Architettura    | VS2022   | VS2026   |
|-----------------|----------|----------|
| x86-unicode     | 659 KB   | 656 KB   |
| x64-unicode     | 793 KB   | 776 KB   |
| x86-ansi        | 662 KB   | 659 KB   |

## Sorgenti

I sorgenti 7-Zip 25.01 originali sono scaricabili da:
- https://7-zip.org/a/7z2501-src.7z

## License

- **7-Zip**: LGPL 2.1 + BSD 3-clause
- **Plugin NSIS**: Afrow UK

## Credits

- Igor Pavlov (7-Zip)
- Afrow UK (Plugin originale)
- Simone (Aggiornamento 25.01, supporto ZIP/x64)
