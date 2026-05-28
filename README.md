# 💎 OneLang: Native Ahead-Of-Time (AOT) Compiler Toolchain

OneLang is a high-performance, statically-typed systems language and automated transpiler suite optimized for native desktop execution. By combining an elegant, modern syntax wrapper over an engineering-hardened translation pipeline, OneLang bridges the gap between high-level language ergonomics and bare-metal machine performance. 

The compiler reads `.onelang` source files, evaluates lexical constraints, resolves dependency maps recursively, performs static type inference, and emits clean, independent target machine binaries (`app.exe`) with absolute zero runtime or virtual machine overhead.

---

## 🛠️ How It Works: The Core Architecture

The OneLang compilation pipeline is broken down into four distinct, decoupled processing passes to guarantee structural performance and safety:


```

[ Source Script (.onelang) ]
│
▼
[ Lexer Pass ]          ──> Strips whitespace, sanitizes comments, and isolates Token types
│
▼
[ LL(1) Parser ]         ──> Employs an arbitrary single-token lookahead buffer to construct the AST
│
▼
[ Static Type Inferrer ]    ──> Resolves register sizes (int, double, string, bool) & isolates scopes
│
▼
[ Code Generator Pass ]    ──> Emits structured C text strings and safety injection guards
│
▼
[ Linker Pass ]          ──> Streams C source directly into GCC to compile the final 'app.exe'

```

### 1. The Token Lookahead Pipeline
Unlike traditional basic interpreters that evaluate source paths linearly, OneLang utilizes an LL(1) parsing layout backed by a dedicated token lookahead check (`peek_next_token()`). This allows the parsing engine to peek ahead at the incoming token state cleanly without mutating the active execution cursor. This technique resolves grammar ambiguities, allowing the parser to cleanly differentiate inline variable evaluations from assignment targets (`var = expr;`) and explicit array mutations (`matrix[idx] = val;`).

### 2. Static Type Inference & Lexical Scope Isolation
To eliminate variable tracking bloat, the code generator runs a type inference calculation pass over the Abstract Syntax Tree (AST) before emitting code. Every high-level identifier is mapped directly to its optimal native hardware data layout (`int`, `double`, `const char*`, or `bool`). 

Furthermore, the code generator maintains a multi-tiered dictionary framework to isolate function local symbol tables from the global context. This enables safe **Variable Shadowing**, allowing function parameters and localized loops to reuse global identifier names without risking memory state pollution.

### 3. "Pay-As-You-Go" Inline Bounds Protection
OneLang enforces memory safety without requiring a slow runtime garbage collector or forcing the developer to deal with a complex compile-time borrow checker. 
* **For Array Reads:** The compiler automatically wraps calculations inside a runtime boundary check macro (`ONELANG_CHECK_BOUNDS`).
* **For Array Writes:** The compiler generates explicit pointer mutation validation statements. 

If an index falls outside the statically declared layout boundaries, the application halts immediately with a clear diagnostics log, preventing lethal buffer overflow exploits.

---

## 📁 Repository Map

```text
I:\onelang\
│
├── core/                         # Compiler Infrastructure Subsystem
│   ├── lexer.py                  # Stream tokenization and lookahead peeking passes
│   ├── parser.py                 # Abstract Syntax Tree (AST) compilation and lookahead routing
│   └── codegen.py                # Hierarchical type inference, scoping, and C string emission
│
├── tests/                        # Modular Source Playground Hub
│   ├── math_library.onelang      # Decoupled utility library module dependency script
│   └── core_utils.onelang        # Primary execution entry application script
│
├── main.py                       # Python CLI Wrapper & Module Dependency Graph Flattener
├── onelang.c                     # Native C Toolchain orchestrator driver source
└── onelang.exe                   # Stdin-Hardened, single-command compiler driver binary

```

---

## 🚀 Getting Started

### Prerequisites

* A standard **Python 3.x** runtime environment.
* The **GCC compiler** (via MinGW-w64 or MSYS64) added to your machine's environment variables (`PATH`).

### 1. Compile the Unified Toolchain Driver

From your repository root directory, run the following command to build the native single-command toolchain orchestrator:

```powershell
gcc onelang.c -o onelang.exe

```

### 2. Build Your Code

To compile any standalone or modular multi-file program, pass the primary script file into the toolchain driver:

```powershell
.\onelang.exe build tests/core_utils.onelang

```

*Behind the scenes, the toolchain flattens multi-file import dependencies, validates types, injects safe pointer code, invokes GCC to link required OS network bindings (`-lwininet`), and silently sweeps away all intermediate `.c` residues from your disk.*

### 3. Run the Standalone Native Binary

Execute the resulting ultra-compact target binary:

```powershell
.\app.exe

```

---

## 📝 Syntax & Language Specification

### Predictive Variable Re-assignments

Variables are bound using the `let` keyword and can be safely mutated using standard expressions without explicit block re-declarations:

```text
let tracker = 10;
tracker = tracker + 5;
print tracker; # Outputs 15

```

### Explicit Array Parameters & Automated Length Tracking

Functions accept explicit array pointers using a bracket postfix signature (`matrix[]`). OneLang automatically passes and manages size characteristics behind the scenes, exposing the intrinsic `len()` utility anywhere inside your function:

```text
fn calculate_average(dataset[]) {
    let sum = 0;
    let i = 0;
    let total = len(dataset);
    
    while (i < total) {
        sum = sum + dataset[i];
        i = i + 1;
    }
    return sum / total;
}

let metrics = [85, 90, 95, 100];
print calculate_average(metrics); # Outputs 92.5

```

### Recursive Multi-File Imports

De-clutter enterprise scripts by organizing modular utilities across multiple dependency files. The compiler resolves dependency trees cleanly to prevent circular module deadlocks:

```text
# tests/math_library.onelang
fn calculate_square(val) {
    return val * val;
}

# tests/core_utils.onelang
import math_library;
let result = calculate_square(9);
print result; # Outputs 81

```

---

## 🗺️ Roadmap & Ecosystem Vision

OneLang is actively evolving. While the foundational version is deeply optimized for Windows automation environments, the pipeline is architected to remain platform-agnostic.

### 🌟 Coming Soon: Universal Cross-Platform Support

Development is currently underway to decouple the core code generator from platform-specific APIs. Future iterations will support:

* 🐧 **Linux (Native POSIX):** Swapping WinInet hooks for native POSIX socket architectures to compile microsecond-fast background automation daemons for Linux servers.
* 🍏 **macOS (Darwin AOT):** Expanding code-generation paths to match Darwin system architectures seamlessly.
* 🌐 **WebAssembly (WASM Target):** Introducing a dedicated WASM compilation target pass, allowing OneLang modules to run safely at native engine speeds right inside modern web browser runtimes.

---

## 👤 Author

Developed by **TheDevilHimselfCodes** 🚀

```

```
