# v0.4.0 — Libraries & Tooling

All Core VM items (01–11) are complete in v0.3.0. This plan covers the next
phase: a standard library and developer toolchain.

---

## Libraries

### Item 12 — Standard I/O ✅
Three opcodes for interactive programs:
- **READ (69)** — read a line from stdin into a string pool slot, push handle
- **WRITE (70)** — print string handle without newline
- **FLUSH (71)** — force pending output

Same opcodes on PC (C++ stdio) and ESP (serial buffer). Implemented in compiler and C++ VM with `read()`, `write`, `flush` syntax.

---

### Item 13 — String operations ✅
Four opcodes for text handling:
- **STRLEN (72)** — push length of string handle
- **STRCAT (73)** — concatenate two handles into a third
- **SUBSTR (74)** — extract substring by handle, offset, length
- **STRCMP (75)** — compare two handles, push -1/0/1

Accessible via `strlen()`, `strcat()`, `substr()`, `strcmp()` in source. String pool grows at runtime for concatenation and substring results.

---

### Item 14 — File I/O
Four opcodes wrapping C stdio / LittleFS:
- **FOPEN (76)** — open file by path string, push fd
- **FREAD (77)** — read from fd into string handle
- **FWRITE (78)** — write string handle to fd
- **FCLOSE (79)** — close fd

File handles are integer descriptors into a VM-internal table.

---

### Item 15 — Time
Four opcodes for real-time programs:
- **TIME (80)** — push ms since boot
- **DELAY (81)** — block for N ms
- **RTC_READ (82)** — read ESP RTC memory (no-op on PC)
- **RTC_WRITE (83)** — write ESP RTC memory (no-op on PC)

---

### Item 16 — Random
Two opcodes:
- **RAND (84)** — push random 64-bit integer
- **SRAND (85)** — seed the RNG

PC: `std::mt19937_64`. ESP: hardware `random()`.

---

### Item 17 — FFI (CALL_EXTERN)
Bridge ELIN to the host system:
- **CALL_EXTERN (86)** — call registered external function by ID
- Source declaration: `EXTERN "math" sin;`
- Per-platform function registry (C++ stdlib on PC, GPIO/WiFi on ESP)

---

## Tooling

### Item 18 — Bytecode assembler (elin-asm)
Human-readable text format that assembles to `.outz`:

```
PUSH 42
STORE 0
HALT
```

For hand-writing optimized bytecode, testing individual opcodes, and
bootstrapping the compiler.

---

### Item 19 — Source-level debugger (elin-debug)
Set breakpoints, single-step, inspect state.
- Compiler emits line-number table (source line → bytecode offset)
- Interactive terminal on PC
- Serial commands on ESP: `s` (step), `c` (continue), `p` (print stack)

---

### Item 20 — REPL (elin-repl)
Read a line of ELIN source, compile, run, print result, repeat.
- Requires making the compiler embeddable as a library
- On PC: immediate feedback for learning
- On ESP: interactive shell commands in ELIN

---

### Item 21 — Package manager (elin-pkg)
Manage dependencies:
- `elin-pkg init` — create `elin.json` manifest
- `elin-pkg add math` — pull from git URL or local path
- `elin-pkg build` — compile everything together

No registry server — just git URLs and local paths.

---

## Opcode allocations (v0.4.0)

| ID | Mnemonic   | Library       |
|----|------------|---------------|
| 69 | READ       | Standard I/O  |
| 70 | WRITE      | Standard I/O  |
| 71 | FLUSH      | Standard I/O  |
| 72 | STRLEN     | String ops    |
| 73 | STRCAT     | String ops    |
| 74 | SUBSTR     | String ops    |
| 75 | STRCMP     | String ops    |
| 76 | FOPEN      | File I/O      |
| 77 | FREAD      | File I/O      |
| 78 | FWRITE     | File I/O      |
| 79 | FCLOSE     | File I/O      |
| 80 | TIME       | Time          |
| 81 | DELAY      | Time          |
| 82 | RTC_READ   | Time          |
| 83 | RTC_WRITE  | Time          |
| 84 | RAND       | Random        |
| 85 | SRAND      | Random        |
| 86 | CALL_EXTERN| FFI           |
