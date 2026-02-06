# ELIN Programming Language

ELIN is a simple, stack-based toy programming language. It currently consists of a compiler written in Python that translates human-readable source code into a string-based bytecode format.

## Current Capabilities

The language currently supports the following features:

- **Variables**: Assign values and retrieve them using `let` (e.g., `let x = 10`).
- **Arithmetic**: Basic math operations including addition (`+`), subtraction (`-`), multiplication (`*`), and division (`/`).
- **I/O**: A `print` command to output values or variables.
- **Comments**: Lines starting with `#` or `//` are ignored by the compiler.
- **Stack-Based Execution**: The compiler prepares bytecode meant for a stack-based virtual machine.
- **Control**: A `halt` command to safely stop program execution.

## Language Rules

ELIN enforces strict variable usage to prevent common programming errors:

- **Variables must be used**: All declared variables must be used at least once. The compiler will error if you define a variable but never read from it.
- **No undefined variables**: You cannot use a variable before it has been defined with `let`. The compiler will error if you try to access an undefined variable.
- **Automatic HALT**: If your program doesn't end with a `halt` statement, the compiler automatically adds one to ensure clean termination.

## The Compiler

The compiler takes a `.elin` file and generates a `.outz` file. 

- **Input Format**: Simple statements like `let x = 5 + 10`.
- **Output Format**: Space-separated bytecode segments, with each source line's translation on a new line.

### Example

let x = 10
let y = 5
let z = x + y

**Bytecode Output (`test.outz`):**
1 0 0 0 10
3 0
1 0 0 0 5
3 1
2 0
2 1
4
3 2
8 2
9

| Code | Instruction | Description |
| :--- | :--- | :--- |
| **1** | PUSH | Pushes a value onto the stack |
| **2** | LOAD | Loads a variable's value onto the stack |
| **3** | STORE | Stores the top stack value into a variable |
| **4** | ADD | Adds the top two values |
| **5** | SUB | Subtracts the top two values |
| **6** | MUL | Multiplies the top two values |
| **7** | DIV | Divides the top two values |
| **8** | PRINT | Prints the top value of the stack |
| **9** | HALT | Stops execution |

## How to Run

To compile an ELIN file:
```bash
python3 compiler/main.py path/to/your_file.elin
```
