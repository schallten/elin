# Compiler Cleanup Plan

The compiler works, but it accumulated hacks as it grew. This plan cleans it up without changing languages or derailing the self‑hosting goal.

## Roadmap – Early Items

### Core VM // Item 01 — DONE
**PRINT pops from eval_stack**  
We change PRINT (8) to pop the top of eval_stack and print it directly. Then `print r;` becomes simply `LOAD 2; PRINT;` — no more temporary juggling.

### Core VM // Item 02 — DONE
**Constant pool + PUSH_CONST**  
Add a constant pool to the `.outz` format and a `PUSH_CONST <idx>` opcode that references pool entries with a single byte. Same expressiveness, much denser bytecode.

### Core VM // Item 03 — DONE
**DUP, DROP, SWAP**  
Reserve IDs 60‑62 for the three fundamental stack operations every stack VM needs: `DUP` duplicates the top, `DROP` discards it, `SWAP` exchanges the top two. Without them we end up with STORE/LOAD hacks — more bytes, more globals, more noise.

### Core VM // Item 04 — DONE
**NEG and NOT**  
Add NEG (63) and NOT (64). `NEG` pops `a` and pushes `-a`. `NOT` pushes `1` if `a == 0` and `0` otherwise.

### Core VM // Item 05 — DONE
**NOP**  
Add a no-op instruction at ID 65. Advances PC, does nothing else — useful for padding and placeholder slots during optimization.

### Core VM // Item 06 — DONE
**INC and DEC**  
Add INC (66) and DEC (67). `INC 5` loads variable 5, increments it, and stores it back — 2 bytes instead of `LOAD 5; PUSH 1; ADD; STORE 5;` which takes 11.

### Core VM // Item 07 — DONE
**DEBUG / TRACE mode**  
Add a `--debug` / `-d` flag to the VM that prints every opcode, eval_stack state, and frame info. Also add a `TRACE` opcode (69) that toggles debug mode at runtime.

### Core VM // Item 08 — DONE
**INPUT opcode**  
Add INPUT (68): blocks until a number arrives (stdin), then pushes it onto eval_stack. Unlocks interactive programs — calculators, prompts, games.

### Core VM // Item 09 — DONE
**MOD and ABS**  
Add MOD (55) for `%` operator and ABS (56) for absolute value. MOD is needed for array indexing and circular buffers; ABS for distance calculations. Both slot into the 64-bit integer model.

### Core VM // Item 10 — DONE
**Version the .outz format**  
Our bytecode format has no header — raw opcodes from offset zero. We're fixing that with magic bytes (0x45 0x4C 0x49 0x4E = "ELIN"), a version byte, flags, and pool offsets. This lets us evolve the format over time, detect corruption, and reject unsupported files gracefully.

### Core VM // Item 11 — DONE
**Compile-time constant evaluation**  
If every operand in an expression is a compile-time constant, the compiler folds the result directly into the bytecode instead of emitting runtime instructions. `42 + 15` becomes a single `PUSH_CONST 57` rather than `PUSH 42; PUSH 15; ADD;`. Only pure operations (no function calls, no variables, no array accesses) will be folded in the first pass.


