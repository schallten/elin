# Opcode Table

The following instructions are the raw commands the ELIN Virtual Machine understands. Every high-level command you write is translated into these decimal IDs.

<details>
<summary><strong>Click to expand opcode table</strong></summary>

| ID | Mnemonic | Action |
|----|----------|--------|
| 1 | PUSH | Push numeric literal to stack (deprecated, use PUSH_CONST) |
| 2 | LOAD | Load global variable to stack |
| 3 | STORE | Store stack top to global variable |
| 4 | ADD | Pop two values, push sum |
| 5 | SUB | Pop two values, push difference |
| 6 | MUL | Pop two values, push product |
| 7 | DIV | Pop two values, push quotient |
| 8 | PRINT | Pop top of stack and print to console |
| 9 | HALT | Stop program execution |
| 10 | GT | Pop two values, push 1 if first > second else 0 |
| 11 | LT | Pop two values, push 1 if first < second else 0 |
| 12 | EQ | Pop two values, push 1 if equal else 0 |
| 13 | NEQ | Pop two values, push 1 if not equal else 0 |
| 14 | GTE | Pop two values, push 1 if first >= second else 0 |
| 15 | LTE | Pop two values, push 1 if first <= second else 0 |
| 16 | JMP | Jump to instruction at specific index |
| 17 | JZ | Jump if popped value is Zero |
| 20 | PUSH_STR | Push string index reference |
| 21 | PRINT_STR | Print string from pool reference |
| 22 | PUSH_CONST | Push constant from pool by index |
| 30 | MAKE_ARR | Create array from stack values |
| 31 | LOAD_ARR | Load element from array by index |
| 32 | STORE_ARR | Store value into array at index |
| 33 | ARR_LEN | Push length of array |
| 34 | PUSH_ARR | Push array from pool by index |
| 40 | CALL | Shift to Local Frame & Jump |
| 41 | RET | Return value and pop Frame |
| 42 | PUSH_LOCAL | Push local variable from current frame |
| 43 | STORE_LOCAL | Store to local variable in current frame |
| 44 | ALLOC | Allocate N cells on heap, push handle |
| 45 | FREE | Invalidate a heap handle |
| 46 | LOAD_H | Read cell from heap via handle + index |
| 47 | STORE_H | Write cell to heap via handle + index |
| 48 | HEAP_LEN | Push size of a handle's block |
| 55 | MOD | Pop two values, push remainder of division |
| 56 | ABS | Pop one value, push its absolute value |
| 60 | DUP | Duplicate the top value on the stack |
| 61 | DROP | Remove the top value from the stack |
| 62 | SWAP | Swap the top two values on the stack |
| 63 | NEG | Negate the top value (flip sign) |
| 64 | NOT | Logical NOT: 1 if top is 0, else 0 |
| 65 | NOP | No operation (padding) |
| 66 | INC | Increment variable by 1 |
| 67 | DEC | Decrement variable by 1 |
| 68 | INPUT | Read integer from stdin and push to stack |
| 69 | READ | Read line from stdin into string pool, push handle |
| 70 | WRITE | Print string handle without newline |
| 71 | FLUSH | Flush stdout |
| 72 | STRLEN | Push length of string handle |
| 73 | STRCAT | Concatenate two string handles, push new handle |
| 74 | SUBSTR | Extract substring by handle, offset, length, push new handle |
| 75 | STRCMP | Compare two string handles, push -1/0/1 |
| 76 | FOPEN | Open file by path string, push fd |
| 77 | FREAD | Read from fd into string handle |
| 78 | FWRITE | Write string handle to fd |
| 79 | FCLOSE | Close fd |
| 80 | TIME | Push ms since boot |
| 81 | DELAY | Block for N ms |
| 82 | RTC_READ | Read ESP RTC memory (no-op on PC) |
| 83 | RTC_WRITE | Write ESP RTC memory (no-op on PC) |
| 84 | RAND | Push random 64-bit integer |
| 85 | SRAND | Seed the random generator |
| 86 | CALL_EXTERN | Call registered external function by ID |
| 90 | TRACE | Toggle debug output on/off |

</details>
