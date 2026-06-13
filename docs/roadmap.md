# ELIN Roadmap

*Our wishlist. No deadlines. Subject to whims.*

---

<div class="version-header">
<span class="version-badge v040">v0.4.0</span>
<h2>Libraries & Tooling — Ecosystem</h2>
<p>Items 12–21 ship a standard library and developer toolchain, alongside the core bump allocator (M1) for dynamic allocation. This is how we turn ELIN from a bare VM into a usable programming environment.</p>
</div>

## Libraries

### Item 12 — Standard I/O <span style="color: #4ade80;">✓ Done</span>

Three opcodes for interactive programs:
- **READ (69)** — read a line from stdin into the string pool and push the handle
- **WRITE (70)** — print a string handle without newline
- **FLUSH (71)** — flushes stdout

`read()`, `write`, and `flush` keyword syntax in the compiler.

---

### Item 13 — String operations <span style="color: #4ade80;">✓ Done</span>

Four opcodes for text handling:
- **STRLEN (72)** — push the length of a string handle
- **STRCAT (73)** — concatenate two handles and push a new one
- **SUBSTR (74)** — extract a substring by handle, offset, and length
- **STRCMP (75)** — compare two handles and push -1/0/1

Accessed via `strlen()`, `strcat()`, `substr()`, and `strcmp()` in source.

---

### Item 14 — File I/O <span style="color: #4ade80;">✓ Done</span>

Four opcodes:
- **FOPEN (76)** — open file by path string, push fd
- **FREAD (77)** — read from fd into string handle
- **FWRITE (78)** — write string handle to fd
- **FCLOSE (79)** — close fd

On PC they wrap the C stdio API; on ESP they wrap LittleFS. Same API surface, different backend.

---

### Item 15 — Time <span style="color: #4ade80;">✓ Done</span>

Four opcodes for anything real-time:
- **TIME (80)** — push milliseconds since boot (`std::chrono` on PC, `millis()` on ESP)
- **DELAY (81)** — block for N ms
- **RTC_READ (82)** — read ESP RTC memory (no-op on PC)
- **RTC_WRITE (83)** — write ESP RTC memory (no-op on PC)

---

### Item 16 — Random <span style="color: #4ade80;">✓ Done</span>

Two opcodes:
- **RAND (84)** — push a random 64-bit integer
- **SRAND (85)** — seed the generator

On PC we use `std::mt19937_64`; on ESP we use the hardware `random()`. Same interface, platform-appropriate implementation underneath.

---

### Item 17 — FFI (CALL_EXTERN) <span style="color: #4ade80;">✓ Done</span>

This is how we bridge ELIN to the host system. A source declaration like `extern "math" add;` emits **CALL_EXTERN (86)**. We maintain a function registry per platform: C++ stdlib on PC, GPIO and WiFi on ESP. Same opcode, different registration tables.

---

## Tooling

### Item M1 — Core bump allocator <span style="color: #4ade80;">✓ Done</span>

A single heap segment using bump-pointer allocation. Each allocation returns a handle (integer ID) rather than a raw address. A flat handle table maps IDs to block metadata (pointer, size, validity flag). Allocation is O(1) — increment a pointer. Deallocation is explicit: `FREE` invalidates the handle and recycles its slot; memory is not reclaimed, the bump pointer only advances. `LOAD_H` / `STORE_H` opcodes access cells with bounds checking. Use-after-free, double-free, and OOB are caught at runtime — no silent corruption.

---

### Item 18 — Bytecode assembler <span style="color: #4ade80;">✓ Done</span>

We built `elin-asm` — a human-readable text format that assembles to `.outz`:

```
PUSH_CONST 0
STORE 0
HALT
```

For hand-writing optimized bytecode, testing individual opcodes, and bootstrapping the compiler — all without hex-editing raw `.outz` files. Supports labels, forward references, and pool definitions.

---

### Item 21 — Package manager

We're building `elin-pkg` to manage dependencies:

- `elin-pkg init` — creates an `elin.json` manifest
- `elin-pkg add math` — pulls from a git repo or local path
- `elin-pkg build` — compiles everything together

Dependencies are just `.elin` files with their own `elin.json`. No registry server — git URLs or local paths. This also serves as a prototype for Loom so we can figure out what it really needs before writing it in C++ for ESP.

---

### Item 19 — Source-level debugger

We're building `elin-debug`: set breakpoints, single-step through source lines, inspect state. The compiler will emit a line-number table in `.outz` that maps source lines to bytecode offsets. On PC it's an interactive terminal; on ESP it accepts serial commands (`s` = step, `c` = continue, `p` = print stack).

---

### Item 20 — REPL

We're building `elin-repl`: read a line of ELIN source, compile it, run it, print the result, repeat. This requires making the compiler embeddable as a library (or building a separate JIT mode). On PC it gives us immediate feedback for learning; on ESP it lets us write interactive shell commands in ELIN instead of hardcoded C++.

---

<div class="version-header">
<span class="version-badge v050">v0.5.0</span>
<h2>Memory + Self-Hosting — The Turning Point</h2>
<p>Multi-segment memory regions (M2) provide temp allocation for function-local work without manual <code>FREE</code>, powering the self-hosting compiler (Item 22). Once ELIN can compile itself, it stops being a toy and becomes a self-sustaining system.</p>
</div>

### Item M2 — Multi-segment architecture + regions

Four logical bump-allocated arenas:
- **Main (0)** — explicitly managed allocations
- **Temp (1)** — function-local scratch (compiler auto-inserts `REGION_ENTER`/`REGION_EXIT` around function bodies)
- **Interrupt (2)** — ISR-safe allocations
- **Spare (3)** — overflow or special-purpose use

`REGION_EXIT` resets the bump pointer and invalidates all handles in that segment — no per-object tracking needed. Recursive functions and loops can allocate temporaries without leaking and without manual `FREE`.

---

### Item 22 — Write the ELIN compiler in ELIN

Our endgame: write the ELIN compiler in ELIN itself. That's the proof that we've built something complete. We'll break it into three stages:

**Stage 1:** Write a lexer in ELIN. It takes a string handle to source code and produces an array of token structs (type, value). We'll validate it against the output of our Python/Haskell lexer.

**Stage 2:** Write a parser in ELIN. It consumes the token array and produces an AST using nested arrays or structs.

**Stage 3:** Write a bytecode emitter in ELIN. It walks the AST and writes valid `.outz` bytes through the file I/O library (Item 14).

Prerequisite: we need structs or records first — or a convention of using arrays with fixed offsets:

```
struct Token {
    int type;
    str value;
};
```

We'll start with Stage 1 only. The moment our ELIN lexer produces the same token stream as the reference implementation for a real program, we'll know the language is viable for self-hosting.

---

<div class="version-header">
<span class="version-badge v060">v0.6.0</span>
<h2>Memory — Hardening & PC Comfort</h2>
<p>Embedded-hardening (M3) makes memory usage fully predictable at link time, while PC features (M4) add dynamic growth, compaction, and profiling for long-running desktop/server programs.</p>
</div>

### Item M3 — Embedded hardening

Segments bind to statically provided memory blocks (e.g. `static ll main_heap[2048]`) — no `malloc` or C++ heap usage. The VM performs zero runtime allocation; all memory is accounted for in the linker map. `ALLOC` returns null (handle 0) on segment full — no exceptions, no crashes. Generation counters make temp reclamation O(1): each `REGION_EXIT` increments a per-segment generation number, and handle validity becomes a generation comparison instead of a table scan. `SEG_USED` opcode reports current utilization for runtime pressure monitoring. Published worst-case cycle counts for all memory ops enable hard real-time scheduling.

---

### Item M4 — PC comfort features

Additive features gated behind build flags:
- **Dynamic growth** — allows segments backed by `malloc`/`new` to grow on demand
- **Compaction** — moves live objects to segment start, can run incrementally across VM cycles to avoid visible pauses
- **Profiling hooks** — runtime callbacks for allocation events and segment pressure thresholds

All PC features are optional — the embedded binary remains unchanged.

---

<div class="version-summary">
<div class="version-summary-item">
<span class="version-badge v040">v0.4.0</span>
<span>Items 12–21 + M1 — Libraries, tooling & bump allocator</span>
</div>
<div class="version-summary-item">
<span class="version-badge v050">v0.5.0</span>
<span>Items M2 + 22 — Multi-segment memory & self-hosting</span>
</div>
<div class="version-summary-item">
<span class="version-badge v060">v0.6.0</span>
<span>Items M3–M4 — Embedded hardening & PC comfort</span>
</div>
<p class="version-summary-note">
These versions aren't about keeping up with other languages — they're our own milestones toward something complete.
</p>
</div>

---

## Syntax Evolution — Toward Professional Readability

> **TL;DR:** We are transitioning ELIN into a "calm systems language"—procedural, data-oriented, and non-OOP. The upcoming syntax revision will replace keyword-heavy noise with minimal, C-style braces, enforcing explicit control flow, flat architectures, and a single unified declaration style. The goal is code that is readable at a glance, easy to parse, and simple to debug.

### The Motivation

The current syntax was built incrementally as the VM grew, and it shows. Semicolons as statement terminators, `wend` to close `while`, `end` to close every block — these were expedient choices that served well during early prototyping but now constrain how the language reads.

A formal syntax revision is planned to shift the language toward a style where structure and data flow are immediately apparent from the surface form of the code — where a function's signature, a block's boundaries, and an error path all announce themselves without requiring the reader to hold context in their head.

### What Will Need to Change

- **No Classes or Methods.** We separate data and behavior entirely. We will use structs, enums, unions, procedures, and modules. Instead of calling methods like `player.move(dir)`, we will write procedures like `player_move(player, dir)`. This keeps logic isolated, APIs flat, and architecture simpler.
- **Unified Declaration Style.** We will adopt one consistent style everywhere: `name: Type` for declarations and `value := expression` for inference.
- **Visually Calm Syntax.** We will replace semicolon spam, keyword-delimited blocks (`if ... end`, `while ... wend`), and excessive punctuation with clean `{ }` blocks. Conditions will be written without unnecessary parentheses (e.g., `if x > 10 { }`).
- **Explicitness over Cleverness.** Control flow and error paths must be obvious and readable top-to-bottom. We will avoid hidden allocations, magic iterators, implicit type coercion, decorators, and chained calls.
- **Tagged Unions + Match.** Instead of inheritance, subclass hierarchies, or virtual methods, we will use explicit tagged unions and `match` statements to handle variants safely.

### How We Will Achieve This

This revision will be informed directly by our self-hosting compiler effort (Item 22). Nothing reveals syntax friction faster than writing a compiler in the language itself. We will incrementally introduce the new parser alongside the old one, migrating the standard library and existing tools (like `elin-asm` and `elin-pkg`) to the new syntax.

The immediate focus remains items 14–21 (libraries and tooling), but the syntax redesign is the next major language-level project after the ecosystem stabilises.

### Code Comparison: Binary Search

To illustrate the difference, here is what a standard binary search looks like in our current syntax compared to our target future syntax.

<details>
<summary><strong>Current Syntax</strong></summary>

```
func int binary_search arr int data int size int target;
    let int low = 0;
    let int high = size - 1;
    
    while low <= high;
        let int mid = (low + high) / 2;
        let int val = data[mid];
        
        if val == target;
            return mid;
        end;
        
        if val < target;
            low = mid + 1;
        else;
            high = mid - 1;
        end;
    wend;
    
    return -1;
end;
```
</details>

<details open>
<summary><strong>Future Syntax</strong></summary>

```
package main

import "core:io"

binary_search :: proc(arr: []int, target: int) -> int {
    left := 0
    right := len(arr) - 1

    for left <= right {
        mid := (left + right) / 2
        value := arr[mid]

        if value == target {
            return mid
        }

        if value < target {
            left = mid + 1
        } else {
            right = mid - 1
        }
    }

    return -1
}

main :: proc() {
    nums := []int{1, 3, 5, 7, 9, 11, 13}
    index := binary_search(nums, 7)
    io.println(index)
}
```
</details>
