/* Linux/MinGW cross-build shim: Windows.h → windows.h
 * Uses #include_next so this shim is skipped on the recursive search,
 * forwarding to the real MinGW system windows.h without infinite recursion. */
#pragma GCC system_header
#include_next <windows.h>
