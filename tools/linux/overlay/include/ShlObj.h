/* Linux/MinGW cross-build shim: ShlObj.h → shlobj.h
 * Uses #include_next so this shim is skipped on the recursive search,
 * forwarding to the real MinGW system shlobj.h without infinite recursion. */
#pragma GCC system_header
#include_next <shlobj.h>
