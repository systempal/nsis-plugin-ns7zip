/* Linux/MinGW cross-build shim: NTSecAPI.h → ntsecapi.h
 * Uses #include_next so this shim is skipped on the recursive search,
 * forwarding to the real MinGW system ntsecapi.h without infinite recursion. */
#pragma GCC system_header
#include_next <ntsecapi.h>
