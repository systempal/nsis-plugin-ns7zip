// Main.cpp

#include "StdAfx.h"

#include "Common/Common.h"
#include "Common/MyInitGuid.h"

#include "Common/CommandLineParser.h"
#include "Common/MyException.h"
#include "Common/IntToString.h"
#include "Common/StdOutStream.h"
#include "Common/StringConvert.h"
#include "Common/StringToInt.h"

#include "Windows/FileDir.h"
#include "Windows/FileName.h"
#include "Windows/Defs.h"
#include "Windows/ErrorMsg.h"
#ifdef _WIN32
#include "Windows/MemoryLock.h"
#endif

#include "7zip/IPassword.h"
#include "7zip/ICoder.h"
#include "7zip/UI/Common/UpdateAction.h"
#include "7zip/UI/Common/Update.h"
#include "7zip/UI/Common/Extract.h"
#include "7zip/UI/Common/ArchiveCommandLine.h"
#include "7zip/UI/Common/ExitCode.h"
#ifdef EXTERNAL_CODECS
#include "7zip/UI/Common/LoadCodecs.h"
#endif

//#include "../../Compress/LZMA_Alone/LzmaBenchCon.h"

#include "7zip/UI/Console/OpenCallbackConsole.h"
#include "ExtractCallbackConsole.h"

#include "7zip/MyVersion.h"

#if defined( _WIN32) && defined( _7ZIP_LARGE_PAGES)
extern "C"
{
#include "C/Alloc.h"
}
#endif

using namespace NWindows;
using namespace NFile;
using namespace NCommandLineParser;

HINSTANCE g_hInstance = 0;

// ---------------------------
// exception messages

#ifndef _WIN32
static void GetArguments(int numArguments, const char *arguments[], UStringVector &parts)
{
  parts.Clear();
  for(int i = 0; i < numArguments; i++)
  {
    UString s = MultiByteToUnicodeString(arguments[i]);
    parts.Add(s);
  }
}
#endif

#ifdef EXTERNAL_CODECS
static void PrintString(CStdOutStream &stdStream, const AString &s, int size)
{
  int len = s.Length();
  stdStream << s;
  for (int i = len; i < size; i++)
    stdStream << ' ';
}
#endif

static inline char GetHex(Byte value)
{
  return (char)((value < 10) ? ('0' + value) : ('A' + (value - 10)));
}

#ifdef _WIN32
void SwitchFileAPIEncoding(BOOL ansi)
{
  if (ansi)
  {
    SetFileApisToOEM();
  }
  else
  {
    SetFileApisToANSI();
  }
}
#endif

int DoExtractArchive(UString archive, UString targetDir, bool overwrite, bool extractPaths, ExtractProgressHandler epc, const UStringVector& skipPatterns)
{
	CCodecs *codecs = new CCodecs;
	CMyComPtr<IUnknown> compressCodecsInfo = codecs;
	HRESULT result = codecs->Load();

	if (result != S_OK)
		throw CSystemException(result);

	if (codecs->Formats.Size() == 0) throw -1;

	CIntVector formatIndices;

	if (!codecs->FindFormatForArchiveType(L"7z", formatIndices))
	{
		throw -1;
	}

	BOOL bApisAreAnsi = AreFileApisANSI();

#ifdef _WIN32
	if (bApisAreAnsi)
		SwitchFileAPIEncoding(bApisAreAnsi);
#endif

	CExtractCallbackConsole *ecs = new CExtractCallbackConsole();
	CMyComPtr<IFolderArchiveExtractCallback> extractCallback = ecs;
	ecs->Init();
	ecs->ProgressHandler = epc;  // Imposta DOPO Init()

	COpenCallbackConsole openCallback;

	CExtractOptions eo;
	eo.StdOutMode = false;
	eo.PathMode = extractPaths?NExtract::NPathMode::kCurPaths:NExtract::NPathMode::kNoPaths;
	eo.TestMode = false;
	eo.OverwriteMode = overwrite?NExtract::NOverwriteMode::kOverwrite:NExtract::NOverwriteMode::kSkip;
	eo.OutputDir = targetDir;
	eo.YesToAll = true;
#ifdef COMPRESS_MT
	CObjectVector<CProperty> prp;
	eo.Properties = prp;
#endif
	UString errorMessage;
	CDecompressStat stat;
	NWildcard::CCensor wildcardCensor;
	NWildcard::CCensorPathProps props;
	props.Recursive = true;
	props.WildcardMatching = true;
	wildcardCensor.AddItem(NWildcard::ECensorPathMode::k_FullPath, true, L"*", props);
	for (unsigned i = 0; i < skipPatterns.Size(); i++)
	{
		const UString &p = skipPatterns[i];
		if (p.IsEmpty()) continue;
		// Keep only single-name patterns: multi-segment ones land in a separate Pair
		// and would be silently ignored by Pairs.Front().Head below.
		if (p.Find(L'\\') >= 0 || p.Find(L'/') >= 0) continue;
		wildcardCensor.AddItem(NWildcard::ECensorPathMode::k_FullPath, false, p, props);
	}
	UStringVector ArchivePathsSorted;
	UStringVector ArchivePathsFullSorted;
	ArchivePathsSorted.Add(archive);
	UString fullPath;
	NFile::NDir::MyGetFullPathName(archive, fullPath);
	ArchivePathsFullSorted.Add(fullPath);

	UStringVector v1, v2;
	v1.Add(fs2us(archive));
	v2.Add(fs2us(archive));
	const NWildcard::CCensorNode &wildcardCensorHead =
		wildcardCensor.Pairs.Front().Head;
	
	result = Extract(
		codecs, CObjectVector<COpenType>(), CIntVector(),
		v1, v2,
		wildcardCensorHead,
		eo, ecs, ecs, ecs,
#ifndef Z7_SFX
		NULL, // hash
#endif
		errorMessage, stat);

#ifdef _WIN32
	if (bApisAreAnsi)
		SwitchFileAPIEncoding(!bApisAreAnsi);
#endif


	if (!errorMessage.IsEmpty())
	{
		if (result == S_OK)
		result = E_FAIL;
	}

	if (ecs->NumArchiveErrors != 0 || ecs->NumFileErrors != 0)
	{
		if (result != S_OK)
			throw CSystemException(result);

		return NExitCode::kFatalError;
	}

	if (result != S_OK)
		throw CSystemException(result);

  return 0;
}

int DoExtractArchiveWithFile(UString archive, UString targetDir, bool overwrite, bool extractPaths, ExtractProgressWithFileHandler epc, const UStringVector& skipPatterns)
{
	CCodecs *codecs = new CCodecs;
	CMyComPtr<IUnknown> compressCodecsInfo = codecs;
	HRESULT result = codecs->Load();

	if (result != S_OK)
		throw CSystemException(result);

	if (codecs->Formats.Size() == 0) throw -1;

	CIntVector formatIndices;

	if (!codecs->FindFormatForArchiveType(L"7z", formatIndices))
	{
		throw -1;
	}

	BOOL bApisAreAnsi = AreFileApisANSI();

#ifdef _WIN32
	if (bApisAreAnsi)
		SwitchFileAPIEncoding(bApisAreAnsi);
#endif

	CExtractCallbackConsole *ecs = new CExtractCallbackConsole();
	CMyComPtr<IFolderArchiveExtractCallback> extractCallback = ecs;
	ecs->Init();
	ecs->ProgressWithFileHandler = epc;  // Imposta DOPO Init() per evitare che venga resettato

	COpenCallbackConsole openCallback;

	CExtractOptions eo;
	eo.StdOutMode = false;
	eo.PathMode = extractPaths?NExtract::NPathMode::kCurPaths:NExtract::NPathMode::kNoPaths;
	eo.TestMode = false;
	eo.OverwriteMode = overwrite?NExtract::NOverwriteMode::kOverwrite:NExtract::NOverwriteMode::kSkip;
	eo.OutputDir = targetDir;
	eo.YesToAll = true;
#ifdef COMPRESS_MT
	CObjectVector<CProperty> prp;
	eo.Properties = prp;
#endif
	UString errorMessage;
	CDecompressStat stat;
	NWildcard::CCensor wildcardCensor;
	NWildcard::CCensorPathProps props;
	props.Recursive = true;
	props.WildcardMatching = true;
	wildcardCensor.AddItem(NWildcard::ECensorPathMode::k_FullPath, true, L"*", props);
	for (unsigned i = 0; i < skipPatterns.Size(); i++)
	{
		const UString &p = skipPatterns[i];
		if (p.IsEmpty()) continue;
		// Keep only single-name patterns: multi-segment ones land in a separate Pair
		// and would be silently ignored by Pairs.Front().Head below.
		if (p.Find(L'\\') >= 0 || p.Find(L'/') >= 0) continue;
		wildcardCensor.AddItem(NWildcard::ECensorPathMode::k_FullPath, false, p, props);
	}
	UStringVector ArchivePathsSorted;
	UStringVector ArchivePathsFullSorted;
	ArchivePathsSorted.Add(archive);
	UString fullPath;
	NFile::NDir::MyGetFullPathName(archive, fullPath);
	ArchivePathsFullSorted.Add(fullPath);

	UStringVector v1, v2;
	v1.Add(fs2us(archive));
	v2.Add(fs2us(archive));
	const NWildcard::CCensorNode &wildcardCensorHead =
		wildcardCensor.Pairs.Front().Head;
	
	result = Extract(
		codecs, CObjectVector<COpenType>(), CIntVector(),
		v1, v2,
		wildcardCensorHead,
		eo, ecs, ecs, ecs,
#ifndef Z7_SFX
		NULL, // hash
#endif
		errorMessage, stat);

#ifdef _WIN32
	if (bApisAreAnsi)
		SwitchFileAPIEncoding(!bApisAreAnsi);
#endif


	if (!errorMessage.IsEmpty())
	{
		if (result == S_OK)
		result = E_FAIL;
	}

	if (ecs->NumArchiveErrors != 0 || ecs->NumFileErrors != 0)
	{
		if (result != S_OK)
			throw CSystemException(result);

		return NExitCode::kFatalError;
	}

	if (result != S_OK)
		throw CSystemException(result);

  return 0;
}

