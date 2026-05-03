/* Linux/MinGW cross-build shim: MAPI.h → mapi.h
 * Uses #include_next so this shim is skipped on the recursive search,
 * forwarding to the real MinGW system mapi.h without infinite recursion. */
#pragma GCC system_header
#include_next <mapi.h>
