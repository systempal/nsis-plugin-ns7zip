// test_nsis7z.cpp
// Emula la chiamata NSIS a nsis7z::ExtractWithFileCallback fuori da NSIS
// Compila: cl /W3 /EHsc /DUNICODE /D_UNICODE test_nsis7z.cpp /link /OUT:test_nsis7z.exe
// Uso: test_nsis7z.exe <archive.exe> <outdir> [skip1] [skip2] ...

#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// ---- Replica di pluginapi.h ----

typedef struct _stack_t {
    struct _stack_t *next;
    wchar_t text[1];
} stack_t;

enum {
    INST_0, INST_1, INST_2, INST_3, INST_4,
    INST_5, INST_6, INST_7, INST_8, INST_9,
    INST_R0, INST_R1, INST_R2, INST_R3, INST_R4,
    INST_R5, INST_R6, INST_R7, INST_R8, INST_R9,
    INST_CMDLINE, INST_INSTDIR, INST_OUTDIR, INST_EXEDIR, INST_LANG,
    __INST_LAST
};

typedef struct {
    int exec_flags;
    int (__cdecl *ExecuteCodeSegment)(int, HWND);
    void (__cdecl *validate_filename)(wchar_t *);
    int (__cdecl *RegisterPluginCallback)(HMODULE, LPVOID);
} extra_parameters;

// Tipo della funzione esportata dalla DLL
typedef void (__cdecl *NSISPluginFunc)(
    HWND hwndParent,
    int string_size,
    wchar_t *variables,
    stack_t **stacktop,
    extra_parameters *extra
);

// ---- Stato globale simulato ----

#define STRING_SIZE 4096
#define NUM_VARS    __INST_LAST

static wchar_t g_variables[NUM_VARS][STRING_SIZE];
static stack_t *g_stacktop = NULL;

// ---- Callback simulato per il progresso ----

static int __cdecl FakeExecuteCodeSegment(int segment, HWND hwnd)
{
    // La callback NSIS popa 3 valori dallo stack (completedSize, totalSize, fileName)
    // Li leggiamo e stampiamo
    if (g_stacktop)
    {
        stack_t *s1 = g_stacktop;
        stack_t *s2 = s1 ? s1->next : NULL;
        stack_t *s3 = s2 ? s2->next : NULL;

        wprintf(L"  [CB] completed=%s total=%s file=%s\n",
            s1 ? s1->text : L"?",
            s2 ? s2->text : L"?",
            s3 ? s3->text : L"?");

        // Popa i 3 item
        for (int i = 0; i < 3 && g_stacktop; i++)
        {
            stack_t *tmp = g_stacktop;
            g_stacktop = g_stacktop->next;
            free(tmp);
        }
    }
    return 0;
}

static extra_parameters g_extra = { 0, FakeExecuteCodeSegment, NULL, NULL };

// ---- Gestione stack ----

static void push_str(const wchar_t *str)
{
    size_t len = wcslen(str);
    stack_t *item = (stack_t*)malloc(sizeof(stack_t) + len * sizeof(wchar_t));
    if (!item) { wprintf(L"OOM\n"); exit(1); }
    wcscpy_s(item->text, len + 1, str);
    item->next = g_stacktop;
    g_stacktop = item;
}

// Imposta INST_OUTDIR (indice 22) nella variabile array
static void set_outdir(const wchar_t *dir)
{
    wcscpy_s(g_variables[INST_OUTDIR], STRING_SIZE, dir);
}

// ---- Flat variables array per la DLL ----
// La DLL riceve un puntatore a un array piatto: ogni slot e' STRING_SIZE wchar_t
static wchar_t g_flat_vars[NUM_VARS * STRING_SIZE];

static void build_flat_vars()
{
    memset(g_flat_vars, 0, sizeof(g_flat_vars));
    for (int i = 0; i < NUM_VARS; i++)
        wcscpy_s(g_flat_vars + i * STRING_SIZE, STRING_SIZE, g_variables[i]);
}

// ---- main ----

int wmain(int argc, wchar_t *argv[])
{
    if (argc < 3)
    {
        wprintf(L"Uso: test_nsis7z.exe <archive> <outdir> [skip1] [skip2] ...\n");
        wprintf(L"\nEsempio:\n");
        wprintf(L"  test_nsis7z.exe \"C:\\tmp\\nsis.exe\" \"C:\\tmp\\out\" \"$PLUGINSDIR\" \"$PLUGINSDIR\\*\"\n");
        return 1;
    }

    const wchar_t *archive = argv[1];
    const wchar_t *outdir  = argv[2];

    /* Cerca la DLL nella directory del tool */
    wchar_t dllPath[MAX_PATH];
    GetModuleFileNameW(NULL, dllPath, MAX_PATH);
    wchar_t *last = wcsrchr(dllPath, L'\\');
    if (last) *(last+1) = 0;
    wcscat_s(dllPath, MAX_PATH, L"nsis7z.dll");

    wprintf(L"Carico DLL: %s\n", dllPath);
    HMODULE hDll = LoadLibraryW(dllPath);
    if (!hDll)
    {
        wprintf(L"ERRORE: LoadLibrary fallito (err=%lu)\n", GetLastError());
        return 2;
    }
    wprintf(L"DLL caricata OK\n");

    NSISPluginFunc fnExtract = (NSISPluginFunc)GetProcAddress(hDll, "ExtractWithFileCallback");
    if (!fnExtract)
    {
        wprintf(L"ERRORE: GetProcAddress(ExtractWithFileCallback) fallito (err=%lu)\n", GetLastError());
        FreeLibrary(hDll);
        return 3;
    }
    wprintf(L"Funzione trovata OK\n");

    // Prepara OUTDIR
    set_outdir(outdir);
    wprintf(L"OutDir = %s\n", outdir);

    // Prepara stack NSIS (push in ordine inverso - l'ultimo pushato e' il primo poppato)
    // Ordine di pop nella DLL: 1) popint() = callback segment, 2..N) popstring() = skip patterns + ""
    // Per il callback usiamo segmento 1 (FakeExecuteCodeSegment ricevera' segmento-1 = 0)
    //
    // Push ordine (il primo push e' il fondo dello stack):
    //   "" (terminatore skip)
    //   skip[N-1] ... skip[0]  (in reverse per avere l'ordine giusto al pop)
    //   callback_int

    // Prima: push terminatore
    push_str(L"");

    // Push skip patterns in ordine inverso (argv[3..])
    for (int i = argc - 1; i >= 3; i--)
        push_str(argv[i]);

    // Push archive path (popstring in EXTRACTFUNC macro)
    push_str(archive);

    // Il callback viene poppato con popint() DENTRO ExtractWithFileCallback (dopo EXDLL_INIT e popstring(archive))
    // Dobbiamo quindi mettere sull'apice dello stack il valore int callback
    // Ma... push_str prima e poi push_str archive: l'archivio e' sul top, poi il callback
    // Riordino: prima il callback (fondo), poi archive (top)
    // Svuota e rifai nell'ordine corretto:
    
    // Libera stack corrente
    while (g_stacktop) {
        stack_t *t = g_stacktop;
        g_stacktop = g_stacktop->next;
        free(t);
    }

    // L'EXTRACTFUNC macro fa:
    //   popstring(sArchive)   <- primo pop = archive
    // Poi ExtractWithFileCallback fa:
    //   g_progressCallback = popint()  <- secondo pop = callback segment
    //   PopSkipPatterns():
    //     while popstring(buf)==0 && len>0 <- terzo+ pop = skip patterns, fino a ""
    //
    // Quindi push in ordine inverso (ultimo push = primo pop):
    //   push ""         (terminatore, ultimo da poppare)
    //   push skip[n-1]..skip[0]
    //   push "2"        (callback segment: ExecuteCodeSegment(2-1=1,...) ma usiamo 1 -> exec(0))
    //   push archive    (primo da poppare)

    // Push "" terminatore
    push_str(L"");
    // Push skip patterns
    for (int i = argc - 1; i >= 3; i--)
        push_str(argv[i]);
    // Push callback segment (1 -> FakeExecuteCodeSegment(0, ...))
    wchar_t segbuf[32];
    swprintf_s(segbuf, 32, L"%d", 1);
    push_str(segbuf);
    // Push archive (top of stack = first to pop)
    push_str(archive);

    wprintf(L"\nChiamo ExtractWithFileCallback...\n");
    wprintf(L"  archive = %s\n", archive);
    wprintf(L"  outdir  = %s\n", outdir);
    for (int i = 3; i < argc; i++)
        wprintf(L"  skip[%d] = %s\n", i-3, argv[i]);
    wprintf(L"\n");

    build_flat_vars();

    __try
    {
        fnExtract(
            NULL,           // hwndParent (NULL = no progress bar)
            STRING_SIZE,    // string_size
            g_flat_vars,    // variables (flat array)
            &g_stacktop,    // stacktop
            &g_extra        // extra
        );
        wprintf(L"\nESTRAZIONE COMPLETATA SENZA CRASH\n");
    }
    __except(EXCEPTION_EXECUTE_HANDLER)
    {
        DWORD code = GetExceptionCode();
        wprintf(L"\nSEH EXCEPTION: 0x%08lX\n", code);
        switch(code)
        {
            case EXCEPTION_ACCESS_VIOLATION:     wprintf(L"  -> ACCESS VIOLATION\n"); break;
            case EXCEPTION_STACK_OVERFLOW:       wprintf(L"  -> STACK OVERFLOW\n"); break;
            case EXCEPTION_ILLEGAL_INSTRUCTION:  wprintf(L"  -> ILLEGAL INSTRUCTION\n"); break;
            default: break;
        }
    }

    FreeLibrary(hDll);
    return 0;
}
