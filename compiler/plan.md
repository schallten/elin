# Compiler Cleanup Plan

The compiler works, but it accumulated hacks as it grew. This plan cleans it up without changing languages or derailing the self‑hosting goal.

## Roadmap – Early Items

### Core VM // Item 01
**PRINT pops from eval_stack**  
We change PRINT (8) to pop the top of eval_stack and print it directly. Then `print r;` becomes simply `LOAD 2; PRINT;` — no more temporary juggling.

### Core VM // Item 02
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