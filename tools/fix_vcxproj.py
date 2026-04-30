#!/usr/bin/env python3
"""Add missing source files to Nsis7z_vs2026.vcxproj"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
vcxproj = ROOT / 'versions/zstd/CPP/7zip/Bundles/Nsis7z/Nsis7z_vs2026.vcxproj'

# Relative paths from vcxproj dir (versions/zstd/CPP/7zip/Bundles/Nsis7z/)
# 5 levels up = versions/
MISSING = [
    r'..\..\..\..\..\7-zip-zstd\CPP\Common\MyWindows.cpp',
    r'..\..\..\..\..\7-zip-zstd\C\hashes\xxhash.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\dict_buffer.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\fl2_common.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\fl2_compress.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\fl2_pool.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\fl2_threading.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\lzma2_enc.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\radix_bitpack.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\radix_mf.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\radix_struct.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\range_enc.c',
    r'..\..\..\..\..\7-zip-zstd\C\fast-lzma2\util.c',
]

content = vcxproj.read_text(encoding='utf-8')

ANCHOR = '    <ClCompile Include="..\\..\\UI\\NSIS\\ExtractCallbackConsole.cpp" />'
if ANCHOR not in content:
    print('ERROR: anchor not found in vcxproj')
    exit(1)

lines = [f'    <ClCompile Include="{p}" />' for p in MISSING]
block = '\n'.join(lines) + '\n    '
content = content.replace(ANCHOR, block + ANCHOR.lstrip())
vcxproj.write_text(content, encoding='utf-8')
print(f'Added {len(MISSING)} source files to vcxproj')
