#pragma GCC system_header
/*
 * Linux/MinGW cross-build shim for 7-zip 25.01 UI/NSIS sources.
 *
 * In 25.01, IDecl.h defines Z7_COM7F_E as throw().  Under GCC/C++17,
 * throw() is treated as noexcept, causing a hard "different exception
 * specifier" error when STDMETHODIMP out-of-class definitions (which carry
 * no exception spec) are compiled against class declarations that used the
 * noexcept-bearing Z7_COM7F_IMF macro.
 *
 * Strategy (no vendor files modified):
 *   1. Include IDecl.h now so its include guard (ZIP7_INC_IDECL_H) is set.
 *      Subsequent indirect includes of IDecl.h from the source file will be
 *      no-ops.
 *   2. Immediately undefine Z7_COM7F_E and redefine it as empty.
 *      Because the preprocessor expands macros lazily (at use site, not at
 *      definition site), all Z7_COM7F_IMF / Z7_COM7F_EO usages that follow
 *      will pick up the empty definition, producing declarations with no
 *      exception specifier — matching the STDMETHODIMP definitions.
 */
#include "7zip/IDecl.h"   /* searched via -I$(CPP_ROOT); resolves to versions/<ver>/CPP/7zip/IDecl.h */

#undef  Z7_COM7F_E
#define Z7_COM7F_E               /* empty – no exception specifier */

/* Cascade: Z7_COM7F_EO and Z7_COM7F_EOF reference Z7_COM7F_E by name,
 * so they pick it up automatically.  Redefine them explicitly to avoid
 * "macro redefined" warnings if they were already expanded anywhere. */
#undef  Z7_COM7F_EO
#define Z7_COM7F_EO   Z7_COM7F_E Z7_override

#undef  Z7_COM7F_EOF
#define Z7_COM7F_EOF  Z7_COM7F_EO Z7_final
