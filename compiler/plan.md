# Compiler Cleanup Plan

The compiler works, but it accumulated hacks as it grew. This plan cleans it up without changing languages or derailing the self‑hosting goal.

## Roadmap – Early Items

### Core VM // Item 01
**PRINT pops from eval_stack**  
We change PRINT (8) to pop the top of eval_stack and print it directly. Then `print r;` becomes simply `LOAD 2; PRINT;` — no more temporary juggling.

### Core VM // Item 02
**Constant pool + PUSH_CONST**  
Add a constant pool to the `.outz` format and a `PUSH_CONST <idx>` opcode that references pool entries with a single byte. Same expressiveness, much denser bytecode.

### Core VM // Item 03
**DUP, DROP, SWAP**  
Reserve IDs 60‑62 for the three fundamental stack operations every stack VM needs: `DUP` duplicates the top, `DROP` discards it, `SWAP` exchanges the top two. Without them we end up with STORE/LOAD hacks — more bytes, more globals, more noise.