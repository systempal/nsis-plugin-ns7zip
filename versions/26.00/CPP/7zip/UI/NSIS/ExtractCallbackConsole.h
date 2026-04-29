// ExtractCallbackConsole.h
// NSIS version adapted for 7-Zip 25.01 API

#ifndef __EXTRACTCALLBACKCONSOLE_H
#define __EXTRACTCALLBACKCONSOLE_H

#include "Common/MyCom.h"
#include "Common/MyString.h"
#include "Common/StdOutStream.h"
#include "../../Common/FileStreams.h"
#include "../../IPassword.h"
#include "../../Archive/IArchive.h"
#include "../Common/ArchiveExtractCallback.h"
#include "../Console/OpenCallbackConsole.h"

typedef void (*ExtractProgressHandler)(UInt64 completedSize, UInt64 totalSize);
typedef void (*ExtractProgressWithFileHandler)(UInt64 completedSize, UInt64 totalSize, const wchar_t *fileName);

class CExtractCallbackConsole Z7_final:
  public IFolderArchiveExtractCallback,
  public IExtractCallbackUI,
#ifndef Z7_NO_CRYPTO
  public ICryptoGetTextPassword,
#endif
  public COpenCallbackConsole,
  public CMyUnknownImp
{
  Z7_COM_QI_BEGIN2(IFolderArchiveExtractCallback)
#ifndef Z7_NO_CRYPTO
  Z7_COM_QI_ENTRY(ICryptoGetTextPassword)
#endif
  Z7_COM_QI_END
  Z7_COM_ADDREF_RELEASE

  // IProgress
  Z7_IFACE_COM7_IMP(IProgress)
  
  // IFolderArchiveExtractCallback
  Z7_IFACE_COM7_IMP(IFolderArchiveExtractCallback)

  // IExtractCallbackUI (non-COM interface)
  Z7_IFACE_IMP(IExtractCallbackUI)

#ifndef Z7_NO_CRYPTO
  Z7_IFACE_COM7_IMP(ICryptoGetTextPassword)
#endif

public:
#ifndef Z7_NO_CRYPTO
  bool PasswordIsDefined;
  UString Password;
#endif
  
  UInt64 NumArchives;
  UInt64 NumArchiveErrors;
  UInt64 NumFileErrors;
  UInt64 NumFileErrorsInCurrentArchive;

  CStdOutStream *OutStream;

  UInt64 totalSize, completedSize, lastVal;

  ExtractProgressHandler ProgressHandler;
  ExtractProgressWithFileHandler ProgressWithFileHandler;
  UString CurrentFileName;

  CExtractCallbackConsole():
    PasswordIsDefined(false),
    NumArchives(0),
    NumArchiveErrors(0),
    NumFileErrors(0),
    NumFileErrorsInCurrentArchive(0),
    OutStream(NULL),
    totalSize((UInt64)(Int64)-1),
    completedSize(0),
    lastVal(0),
    ProgressHandler(NULL),
    ProgressWithFileHandler(NULL)
  {}

  void Init()
  {
    NumArchives = 0;
    NumArchiveErrors = 0;
    NumFileErrors = 0;
    NumFileErrorsInCurrentArchive = 0;

    totalSize = (UInt64)(Int64)-1;
    completedSize = 0;
    lastVal = 0;
    ProgressHandler = NULL;
    ProgressWithFileHandler = NULL;
  }

  void UpdateProgress();
};

#endif
