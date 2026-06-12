# Changelog

## v0.4.0 — Standard Library & OS Features

ELIN grows its standard library. Items 12, 13, 14, and 15 from the roadmap are now implemented: Standard I/O, String Operations, File I/O, and Time. You can read input, write files, manipulate strings at runtime, and handle millisecond-precision timing.

### Standard I/O — read, write, flush

Three new opcodes for interactive programs: **READ (69)** reads a line from stdin into the string pool and pushes its handle; **WRITE (70)** pops a string handle and prints it without a newline; **FLUSH (71)** flushes stdout. Use them together for prompts:

```elin
write "enter name: ";
flush;
let str name = read();
print strcat("hello ", name);
```

The compiler exposes these as `read()`, `write`, and `flush` keywords. TRACE was moved to opcode 90 to free up the 69-75 range.

### String operations — strlen, strcat, substr, strcmp

Four opcodes for text manipulation: **STRLEN (72)** pushes a string's length; **STRCAT (73)** concatenates two string handles and pushes a new one; **SUBSTR (74)** extracts a substring by handle, offset, and length; **STRCMP (75)** compares two strings and pushes -1, 0, or 1. All accessible via `strlen()`, `strcat()`, `substr()`, and `strcmp()` in source.

```elin
let str msg = strcat("hello", " world");
print strlen(msg);       # 11
print substr(msg, 0, 5); # hello
print strcmp("a", "b");  # -1
```

### File I/O — fopen, fread, fwrite, fclose

Four opcodes for persistent storage: **FOPEN (76)** opens a file and pushes a handle; **FREAD (77)** reads a line into a string handle; **FWRITE (78)** writes a string handle to a file; **FCLOSE (79)** closes the file.

```elin
let int fd = fopen("data.txt");
fwrite(fd, "hello file");
fclose(fd);
```

### Time & RTC — time, delay, rtc_read/write

Four opcodes for timing: **TIME (80)** pushes ms since boot; **DELAY (81)** blocks for N ms; **RTC_READ (82)** and **RTC_WRITE (83)** for non-volatile storage on ESP (no-op on PC).

```elin
let int now = time();
delay(500);
print time() - now; # ~500
```

!!! info "Opcode Allocations"
    READ=69, WRITE=70, FLUSH=71 (Standard I/O), STRLEN=72, STRCAT=73, SUBSTR=74, STRCMP=75 (String ops), FOPEN=76, FREAD=77, FWRITE=78, FCLOSE=79 (File I/O), TIME=80, DELAY=81, RTC_READ=82, RTC_WRITE=83 (Time). TRACE was moved to 90.

---

## v0.3.0 — Core VM Complete

ELIN's brain got a lot smarter. Every piece of the plan for the core virtual machine is done — more instructions, leaner files, a cleaner compiler, and a debug mode so you can finally see what's happening inside.

When v0.2.0 came out, ELIN worked — but it was rough. The instruction set had gaps, the bytecode was chunky, and the compiler's code was tangled up in hard-to-follow class structures. Over the last few versions we chipped away at all of it.

### More tools for the VM

Think of the VM as a tiny factory with a conveyor belt (the stack). When v0.2.0 shipped, the factory could only do basic math, load and store values, and jump around. Now it can do much more:

- **Stack tools** — `DUP` copies the top item, `DROP` throws it away, `SWAP` switches the top two. These let you rearrange values without going through memory.
- **Negation and logic** — `NEG` flips a number's sign, `NOT` turns zero into one and anything else into zero.
- **Compact counters** — `INC` and `DEC` add or subtract one from a variable in a single instruction.
- **Input** — `INPUT` reads a number you type and puts it on the stack.
- **Modulo and absolute value** — `MOD` gives you the remainder of a division, `ABS` strips the sign off a number.
- **Debug mode** — `TRACE` makes the VM print every single step it takes.

### Bytecode files got a header

Every `.outz` file now starts with a header that says which version of the format it uses and how many items are in each pool. The VM checks this header before running anything — so if the format changes in the future, it will give you a clear error instead of crashing on garbage. We also shrank the bytecode by storing each number only once in a **constant pool** and referencing it by index, rather than writing out the full number every time.

### A cleaner compiler

The compiler used to be built with classes — groups of related data and functions glued together by `self`. This made the code hard to follow because you never knew which function was changing which piece of data. Every class was torn out and replaced with plain functions that take their inputs as parameters and return their outputs directly. Now `parse(tokens, position)` gives you back a syntax tree and a new position. `check(tree, environment)` gives you back an updated environment. `generate(tree, state)` gives you back updated state. Every step is a simple *data in → data out* transformation, which makes the compiler easier to read, easier to test, and straightforward to rewrite in another language if we ever want to.

The compiler also learned to do math *at compile time*. If you write `42 + 15`, it works out the answer (57) while building the bytecode and just writes `PUSH_CONST 57`. The same goes for nested expressions like `(2 + 3) * (10 - 4) / 3` — the whole thing folds down to a single number. The VM never has to do arithmetic it doesn't need to.

### You can watch the VM work

Run the VM with `--debug` and it prints every instruction it runs, the current stack contents, and how deep it is in function calls. It's like lifting the hood and watching the engine run. You can also toggle this at runtime with the `TRACE` instruction from within an ELIN program. Finally — no more blind debugging.

---

## v0.2.2 – v0.2.6 — Fleshing Out the VM

A handful of smaller releases that filled in the gaps — more instructions, a versioned file format, a smarter output, and a compiler that's both cleaner and faster.

### New operations (v0.2.2 – v0.2.4)

We rounded out the VM's vocabulary. You can now use `%` to get the remainder of a division, `abs(x)` to strip the sign off a number, and `input()` to read values from the keyboard while a program is running. Stack manipulation got three new friends: `DUP` (copy the top value), `DROP` (discard the top value), and `SWAP` (swap the top two). Unary operators `NEG` (negate) and `NOT` (logical not) were added alongside compact increment and decrement instructions. A `TRACE` instruction toggles debug output at runtime — every opcode, stack state, and frame depth gets printed so you can see exactly what the VM is doing.

### Versioned bytecode (v0.2.5)

The `.outz` format now starts with a `VERSION 1` header followed by counts for each pool (constants, strings, arrays). The VM checks this header on load and pre-allocates space. If the format ever changes, the VM will tell you instead of crashing on garbage data. We also introduced a **constant pool** — each unique number is stored once and referenced by index, which cut bytecode size by about 60% on constant-heavy programs.

### Compiler overhaul (v0.2.6)

The compiler was rewritten from the ground up. Every class (TypeChecker, Compiler, etc.) was replaced with plain functions that take inputs and return outputs — no hidden state, no tangled `self`. Dozens of `isinstance` checks became clean `match/case` patterns. The compiler also learned **constant folding**: `42 + 15` is computed at compile time and emits `PUSH_CONST 57` instead of three separate instructions.

!!! info "Technical Details"
    **Opcode assignments:** MOD=55, ABS=56 (math slot), DUP=60, DROP=61, SWAP=62 (stack slot), NEG=63, NOT=64 (unary slot), NOP=65 (padding), INC=66, DEC=67 (counter slot), INPUT=68, READ=69, WRITE=70, FLUSH=71 (std I/O slot), STRLEN=72, STRCAT=73, SUBSTR=74, STRCMP=75 (string ops slot), TRACE=90 (debug slot).

    **Versioned .outz format:** Header: `VERSION 1`, `CONST_COUNT N`, `STR_COUNT N`, `ARR_COUNT N`. The VM parser reads these lines, validates the version, reserves vector capacity, then loads pool entries.

    **Class-to-function refactor:** 60+ methods across `TypeChecker` and `Compiler` classes → 20 module-level functions. All state (env dict, compilation dict) is threaded explicitly. `isinstance` dispatch replaced with Python 3.10 `match/case` (~50 branches across `infer_type`, `check`, `generate`).

    **Constant folding:** `generate` folds `BinaryOpNode`, `UnaryOpNode`, and `ConditionNode` when both operands are `ConstNode`. Nested trees are folded recursively via post-order traversal.

---

## v0.2.1 — A Smarter Brain for ELIN

We've rebuilt the core of the ELIN compiler to be more organized, efficient, and easier to grow.

### Thinking in Blueprints

When you write code, the computer doesn't just read it like a book. It needs to build a "mental map" of what you're trying to do. In technical terms, this map is called an **AST** (Abstract Syntax Tree), but you can think of it as a **blueprint**.

Previously, ELIN was "mashing" your code together into a messy string to understand it. In v0.2.1, it now builds a perfect, clean blueprint directly. This means fewer errors and a system that truly understands the structure of your logic.

### Better Math & Logic

Reading math is hard for computers. They need to know that `2 + 3 * 4` is 14, not 20. We've given ELIN a new "logic engine" (known as a *Pratt Parser*) that allows it to handle complex math and nested instructions with ease.

```elin
# v0.2.1 handles deep math effortlessly
let int result = (10 + 5) * (20 - 5);
```

### Clean House, Fast System

As projects grow, they collect "dust"—old code that isn't used anymore but still takes up space. We've gone through the system and deleted all the old, hacky workarounds. By separating the "reading," "checking," and "running" phases of the compiler, we've made ELIN lighter and much faster. It's a solid foundation for the future.

!!! info "Technical Details"
    **Pratt Parser Implementation:** We replaced the legacy infix-to-postfix converter with a top-down operator precedence (Pratt) parser. This allows the parser to handle **recursive descent** for expressions without a separate shunting-yard phase.

    **Architectural Decoupling:** The compiler has been refactored from a single-pass monolith into a multi-pass pipeline:
    - **Pass 1 (Lexer/Parser):** Generates a high-fidelity AST.
    - **Pass 2 (TypeChecker):** Performs recursive type inference and validation.
    - **Pass 3 (CodeGenerator):** Translates the verified AST into linear bytecode.

    **Optimization & Cleanup:** The removal of `expression_parser.py` eliminates the O(N) overhead of the node-to-string-to-postfix round-trip. Bytecode formatting is now isolated in `format_bytecode()`, allowing `compile()` to return a pure instruction list.

---

[:material-book-open: Learn how to use ELIN](docs/introduction.md){ .md-button .md-button--primary }
