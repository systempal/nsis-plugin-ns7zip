// StdAfx.h

#ifndef __STDAFX_H
#define __STDAFX_H

#ifdef _WIN32
  #if defined(__MINGW32__) || defined(__MINGW64__)
    #include <windows.h>
  #else
    #include <Windows.h>
  #endif
#endif
#include "../../Bundles/Nsis7z/pluginapi.h"

#endif
