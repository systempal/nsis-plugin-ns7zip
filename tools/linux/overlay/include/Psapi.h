/* Linux/MinGW cross-build shim: Psapi.h → psapi.h
 * Uses #include_next so this shim is skipped on the recursive search,
 * forwarding to the real MinGW system psapi.h without infinite recursion. */
#pragma GCC system_header
#include_next <psapi.h>
