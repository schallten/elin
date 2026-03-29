# ELIN Programming Language

ELIN is a simple, stack-based toy programming language. It currently consists of a compiler written in Python that translates human-readable source code into a string-based bytecode format.

## Current Capabilities

The language currently supports the following features:

- **Variables**: Assign values and retrieve them using `let` (e.g., `let x = 10`).
- **Arithmetic**: Basic math operations including addition (`+`), subtraction (`-`), multiplication (`*`), and division (`/`).
- **Strongly Typed**: Variables must have a declared type (`int` or `str`). Types are checked at compile-time.
- **String Support**: Literal strings (e.g., `"hello"`) are supported and stored in an efficient string pool.
- **Arithmetic**: Basic math operations including addition (`+`), subtraction (`-`), multiplication (`*`), and division (`/`).
- **I/O**: A `print` command to output values or variables.
- **Comments**: Lines starting with `#` or `//` are ignored by the compiler.
- **Stack-Based Execution**: The compiler prepares bytecode meant for a stack-based virtual machine.
- **Control**: A `halt` command to safely stop program execution.

## Language Rules

ELIN enforces strict variable usage and type safety:

- **Explicit Typing**: Use `let <type> <name> = <value>` to declare new variables. Example: `let int x = 10`.
- **Reassignment**: To update an existing variable, omit `let`. Example: `x = 20`.
- **Variables must be used**: All declared variables must be used at least once.
- **No undefined variables**: You cannot use or reassign a variable before it has been defined.
- **Automatic HALT**: If your program doesn't end with a `halt` statement, the compiler automatically adds one.

## The Compiler

The compiler takes a `.elin` file and generates a `.outz` file with a string pool header.

### Example

```elin
let str msg = "hello"
let int x = 42
print msg
print x
```

**Bytecode Output (`test.outz` snippets):**
```
# --- STRING POOL ---
STR 0 hello
# --- END STRINGS ---
20 0    # PUSH_STR index 0 ("hello")
3 0     # STORE into var 0
1 0 0 0 42 # PUSH int 42
3 1     # STORE into var 1
8 0     # PRINT var 0
8 1     # PRINT var 1
9       # HALT
```

| Code | Instruction | Description |
| :--- | :--- | :--- |
| **1** | PUSH | Pushes a numeric value onto the stack |
| **2** | LOAD | Loads a variable's value onto the stack |
| **3** | STORE | Stores the top stack value into a variable |
| **4** | ADD | Adds the top two values |
| **5** | SUB | Subtracts the top two values |
| **6** | MUL | Multiplies the top two values |
| **7** | DIV | Divides the top two values |
| **8** | PRINT | Prints the value of a variable |
| **9** | HALT | Stops execution |
| **20** | PUSH_STR | Pushes a string pool index onto the stack |
| **10** | CMP_EQ | Pop two, push 1 if equal, 0 if not (==) |
| **11** | CMP_NEQ | Pop two, push 1 if not equal, 0 if equal (!=) |
| **12** | CMP_LT | Pop two, push 1 if less than, 0 if not (<) |
| **13** | CMP_LTE | Pop two, push 1 if less than or equal, 0 if not (<=) |
| **14** | CMP_GT | Pop two, push 1 if greater than, 0 if not (>) |
| **15** | CMP_GTE | Pop two, push 1 if greater than or equal, 0 if not (>=) |
| **16** | JMP | Unconditional jump to address |
| **17** | JZ | Jump if zero (pop value, if 0 jump) |
| **18** | JNZ | Jump if not zero (pop value, if !0 jump) |

## Control Flow

ELIN supports `if` and `if-else` statements.

```elin
let a = 10
let b = 20

if a < b
    print a
end
else
    print b
end
```

## How to Run

To compile an ELIN file:
```bash
python3 compiler/main.py path/to/your_file.elin
```
