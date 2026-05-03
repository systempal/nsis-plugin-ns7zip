/* Linux/MinGW cross-build shim: CommCtrl.h → commctrl.h
 * Uses #include_next so this shim is skipped on the recursive search,
 * forwarding to the real MinGW system commctrl.h without infinite recursion. */
#pragma GCC system_header
#include_next <commctrl.h>
