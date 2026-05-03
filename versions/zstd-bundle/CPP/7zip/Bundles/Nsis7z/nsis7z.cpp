#include "StdAfx.h"

#include "../../UI/NSIS/ExtractCallbackConsole.h"
#include "Common/StringConvert.h"

#pragma warning(disable: 4100)

#define IDC_PROGRESS                    1004
#define IDC_INTROTEXT                   1006

#define EXTRACTFUNC(funcname) extern "C" { \
void  __declspec(dllexport) __cdecl funcname(HWND hwndParent, int string_size, \
                                      TCHAR *variables, stack_t **stacktop, \
                                      extra_parameters *extra) \
{ \
	EXDLL_INIT();\
	g_lastVal = -1; \
	g_hwndParent=hwndParent; \
	HWND hwndDlg = FindWindowEx(g_hwndParent, NULL, TEXT("#32770"), NULL); \
	g_hwndProgress = GetDlgItem(hwndDlg, IDC_PROGRESS); \
	g_hwndText = GetDlgItem(hwndDlg, IDC_INTROTEXT); \
	TCHAR sArchive[1024], *outDir = getuservariable(INST_OUTDIR); \
	popstring(sArchive); \
	g_pluginExtra = extra; \

#define EXTRACTFUNCEND } }

HINSTANCE g_hInstance2;
HWND g_hwndParent;
HWND g_hwndProgress;
HWND g_hwndText;
extra_parameters *g_pluginExtra;

void DoInitialize();
int DoExtract(LPTSTR archive, LPTSTR dir, bool overwrite, bool expath, ExtractProgressHandler epc, const UStringVector& skipPatterns);
int DoExtractWithFile(LPTSTR archive, LPTSTR dir, bool overwrite, bool expath, ExtractProgressWithFileHandler epc, const UStringVector& skipPatterns);

int g_progressCallback = -1;
int g_lastVal = -1;
TCHAR* g_sDetails;

static void PopSkipPatterns(UStringVector& skipPatterns)
{
	TCHAR *buf = new TCHAR[g_stringsize];
	while (popstring(buf) == 0 && lstrlen(buf) > 0)
	{
#ifdef UNICODE
		skipPatterns.Add(UString(buf));
#else
		skipPatterns.Add(MultiByteToUnicodeString(AString(buf)));
#endif
	}
	delete[] buf;
}

int GetPercentComplete(UInt64 completedSize, UInt64 totalSize)
{
	if (totalSize == 0) return 0;
	const int nsisProgressMax = 30000;
	int val = (int)((completedSize*nsisProgressMax)/totalSize);
	if (val < 0) return 0;
	if (val > nsisProgressMax) return nsisProgressMax;
	return val;
}

void SimpleProgressHandler(UInt64 completedSize, UInt64 totalSize)
{
	int val = GetPercentComplete(completedSize, totalSize);
	if (g_lastVal != val)
		SendMessage(g_hwndProgress, PBM_SETPOS, g_lastVal = val, 0);
}

void CallbackProgressHandler(UInt64 completedSize, UInt64 totalSize)
{
	int val = 0;

	if (totalSize > 0)
	{
		val = GetPercentComplete(completedSize, totalSize);

		static TCHAR buf[32];
		wsprintf(buf, TEXT("%lu"), totalSize);
		pushstring(buf);
		wsprintf(buf, TEXT("%lu"), completedSize);
		pushstring(buf);
		g_pluginExtra->ExecuteCodeSegment(g_progressCallback-1, 0);
	}

	if (g_lastVal != val)
		SendMessage(g_hwndProgress, PBM_SETPOS, g_lastVal = val, 0);
}

void CallbackFileProgressHandler(UInt64 completedSize, UInt64 totalSize, const wchar_t *fileName)
{
	int val = 0;

	if (totalSize > 0)
		val = GetPercentComplete(completedSize, totalSize);

	// Notify NSIS only when a new file starts (filename changes)
	if (fileName && fileName[0])
	{
		static TCHAR fileNameBuf[MAX_PATH];
		static TCHAR prevFileNameBuf[MAX_PATH];
		static TCHAR buf[32];

		lstrcpyn(fileNameBuf, (const TCHAR*)fileName, MAX_PATH);
		if (lstrcmp(fileNameBuf, prevFileNameBuf) != 0)
		{
			lstrcpy(prevFileNameBuf, fileNameBuf);
			pushstring(fileNameBuf);
			wsprintf(buf, TEXT("%lu"), (DWORD)totalSize);
			pushstring(buf);
			wsprintf(buf, TEXT("%lu"), (DWORD)completedSize);
			pushstring(buf);
			g_pluginExtra->ExecuteCodeSegment(g_progressCallback-1, 0);
		}
	}

	if (g_lastVal != val)
		SendMessage(g_hwndProgress, PBM_SETPOS, g_lastVal = val, 0);
}

void DetailsProgressHandler(UInt64 completedSize, UInt64 totalSize)
{
	int val = 0;

	if (totalSize > 0)
	{
		val = GetPercentComplete(completedSize, totalSize);

		TCHAR* buf = new TCHAR[g_stringsize];
		TCHAR* buf2 = new TCHAR[g_stringsize];
		wsprintf(buf, TEXT("%d%% (%d / %d MB)"), (int)(val?val/300:0), (int)(completedSize?completedSize/(1024*1024):0), (int)(totalSize/(1024*1024)));
		wsprintf(buf2, g_sDetails, buf);
		SetWindowText(g_hwndText, buf2);
		delete[] buf;
		delete[] buf2;
	}

	if (g_lastVal != val)
		SendMessage(g_hwndProgress, PBM_SETPOS, g_lastVal = val, 0);
}

EXTRACTFUNC(Extract)
{
	UStringVector skipPatterns;
	PopSkipPatterns(skipPatterns);
	DoExtract(sArchive, outDir, true, true, (ExtractProgressHandler)SimpleProgressHandler, skipPatterns);
}
EXTRACTFUNCEND

EXTRACTFUNC(ExtractWithDetails)
{
	g_sDetails = new TCHAR[string_size];
	popstring(g_sDetails);
	UStringVector skipPatterns;
	PopSkipPatterns(skipPatterns);
	DoExtract(sArchive, outDir, true, true, (ExtractProgressHandler)DetailsProgressHandler, skipPatterns);
	delete[] g_sDetails;
}
EXTRACTFUNCEND

EXTRACTFUNC(ExtractWithCallback)
{
	g_progressCallback = popint();
	UStringVector skipPatterns;
	PopSkipPatterns(skipPatterns);
	DoExtract(sArchive, outDir, true, true, (ExtractProgressHandler)CallbackProgressHandler, skipPatterns);
}
EXTRACTFUNCEND

EXTRACTFUNC(ExtractWithFileCallback)
{
	g_progressCallback = popint();
	UStringVector skipPatterns;
	PopSkipPatterns(skipPatterns);
	DoExtractWithFile(sArchive, outDir, true, true, CallbackFileProgressHandler, skipPatterns);
}
EXTRACTFUNCEND

extern "C" BOOL WINAPI DllMain(HANDLE hInst, ULONG ul_reason_for_call, LPVOID lpReserved)
{
	g_hInstance2=(HINSTANCE)hInst;
	if (ul_reason_for_call == DLL_PROCESS_ATTACH)
	{
		DoInitialize();
	}
	return TRUE;
}
