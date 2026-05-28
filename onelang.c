#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void get_pure_basename(const char *path, char *output, size_t max_len) {
    const char *last_slash = strrchr(path, '\\');
    if (!last_slash) last_slash = strrchr(path, '/');
    const char *filename = (last_slash != NULL) ? (last_slash + 1) : path;
    strncpy(output, filename, max_len - 1);
    output[max_len - 1] = '\0';
    char *dot = strstr(output, ".onelang");
    if (dot) *dot = '\0';
}

int main(int argc, char *argv[]) {
    if (argc < 3) return 1;
    char base_name[256];
    get_pure_basename(argv[2], base_name, sizeof(base_name));

    char transpiler_cmd[512];
    snprintf(transpiler_cmd, sizeof(transpiler_cmd), "python main.py --compile %s", argv[2]);
    printf("[Toolchain]: Running syntax transpiler pass...\n");
    int transpiler_res = system(transpiler_cmd);
    
    // Safety Break Threshold: Abort execution step if Python parsing encounters bugs
    if (transpiler_res != 0) {
        printf("[Toolchain Error]: Structural translation failed. Linker pass aborted.\n");
        return 1;
    }

    char gcc_cmd[512];
    snprintf(gcc_cmd, sizeof(gcc_cmd), "gcc %s.c -o app.exe -lwininet", base_name);
    printf("\n[REAL-TIME VERIFICATION]: Executing: >> %s <<\n", gcc_cmd);
    printf("[Toolchain]: Invoking GCC native machine linker...\n");
    int res = system(gcc_cmd);
    
    char clean_cmd[256];
    snprintf(clean_cmd, sizeof(clean_cmd), "del %s.c", base_name);
    system(clean_cmd);
    return res;
}
