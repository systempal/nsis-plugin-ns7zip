// ExtractCallbackConsole.h

#include "StdAfx.h"

#include "../../../Common/Common.h"
#include "ExtractCallbackConsole.h"
#include "UserInputUtils2.h"
#include "NSISBreak.h"

#include "Common/Wildcard.h"

#include "Windows/FileDir.h"
#include "Windows/FileFind.h"
#include "Windows/TimeUtils.h"
#include "Windows/Defs.h"
#include "Windows/PropVariant.h"
#include "Windows/ErrorMsg.h"
#include "Windows/PropVariantConv.h"

#include "../../Common/FilePathAutoRename.h"

#include "../Common/ExtractingFilePath.h"

using namespace NWindows;
using namespace NFile;
using namespace NDir;

extern HWND g_hwndProgress;

static const UInt64 k_SizeUnknown = (UInt64)(Int64)-1;

void CExtractCallbackConsole::UpdateProgress()
{
	// Prima controlla se c'è il callback con filename (nuova funzione)
	if (ProgressWithFileHandler != NULL)
	{
		if (completedSize != k_SizeUnknown || totalSize > 0)
			ProgressWithFileHandler(completedSize, totalSize, CurrentFileName.Ptr());
		else
			ProgressWithFileHandler(0, 0, CurrentFileName.Ptr());
	}
	// Altrimenti usa il callback originale (per compatibilità)
	else if (ProgressHandler != NULL)
	{
		if (completedSize != k_SizeUnknown || totalSize > 0)
			ProgressHandler(completedSize, totalSize);
		else
			ProgressHandler(0, 0);
	}
}

Z7_COM7F_IMF(CExtractCallbackConsole::SetTotal(UInt64 val))
{
  totalSize = val;
  UpdateProgress();
  if (NNSISBreak::TestBreakSignal())
    return E_ABORT;
  return S_OK;
}

Z7_COM7F_IMF(CExtractCallbackConsole::SetCompleted(const UInt64 *val))
{
  completedSize = *val;
  UpdateProgress();
  if (NNSISBreak::TestBreakSignal())
    return E_ABORT;
  return S_OK;
}

Z7_COM7F_IMF(CExtractCallbackConsole::AskOverwrite(
    const wchar_t *existName, const FILETIME *, const UInt64 *,
    const wchar_t *newName, const FILETIME *, const UInt64 *,
    Int32 *answer))
{
  (void)existName; (void)newName;
  *answer = NOverwriteAnswer::kYesToAll;
  return S_OK;
}

Z7_COM7F_IMF(CExtractCallbackConsole::PrepareOperation(const wchar_t *name, Int32 isFolder, Int32 askExtractMode, const UInt64 *position))
{
  (void)isFolder; (void)askExtractMode; (void)position;
  // Memorizza il nome del file corrente per passarlo al callback
  CurrentFileName = name;
  return S_OK;
}

Z7_COM7F_IMF(CExtractCallbackConsole::MessageError(const wchar_t *message))
{
  (void)message;
  NumFileErrorsInCurrentArchive++;
  NumFileErrors++;
  return S_OK;
}

Z7_COM7F_IMF(CExtractCallbackConsole::SetOperationResult(Int32 opRes, Int32 encrypted))
{
  (void)encrypted;
  switch(opRes)
  {
    case NArchive::NExtract::NOperationResult::kOK:
      break;
    default:
    {
      NumFileErrorsInCurrentArchive++;
      NumFileErrors++;

    }
  }
  return S_OK;
}

#ifndef Z7_NO_CRYPTO

HRESULT CExtractCallbackConsole::SetPassword(const UString &password)
{
  PasswordIsDefined = true;
  Password = password;
  return S_OK;
}

Z7_COM7F_IMF(CExtractCallbackConsole::CryptoGetTextPassword(BSTR *password))
{
  if (!PasswordIsDefined)
  {
    Password = GetPassword(OutStream);
    PasswordIsDefined = true;
  }
  return StringToBstr(Password, password);
}

#endif

HRESULT CExtractCallbackConsole::BeforeOpen(const wchar_t *name, bool testMode)
{
  (void)name; (void)testMode;
  NumArchives++;
  NumFileErrorsInCurrentArchive = 0;
  return S_OK;
}

HRESULT CExtractCallbackConsole::OpenResult(const CCodecs *codecs, const CArchiveLink &arcLink, const wchar_t *name, HRESULT result)
{
  (void)codecs; (void)arcLink; (void)name;
  if (result != S_OK)
  {
    NumArchiveErrors++;
  }
  return S_OK;
}
  
HRESULT CExtractCallbackConsole::ThereAreNoFiles()
{
  return S_OK;
}

HRESULT CExtractCallbackConsole::ExtractResult(HRESULT result)
{
  if (result == S_OK)
  {
    if (NumFileErrorsInCurrentArchive != 0)
    {
      NumArchiveErrors++;
    }
    return result;
  }
  NumArchiveErrors++;
  if (result == E_ABORT || result == ERROR_DISK_FULL)
    return result;
  return S_OK;
}
