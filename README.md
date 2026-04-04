# ELIN Programming Language

ELIN is a simple, stack-based, strongly-typed programming language designed for resource-constrained environments (like microcontrollers). It features a Python-based compiler that generates lightweight bytecode for a custom Virtual Machine.

## New Features (v0.2.0)

- **Functions & Scoping**: Define reusable logic with `func`. Variables inside functions are **locally scoped** and isolated from globals via a call stack.
- **Fixed-Size Arrays**: Efficient array support using `let arr <type> <name> = [values]`. Arrays are pooled at compile-time for zero-runtime allocation overhead.
- **Explicit Terminators**: Support for `;` (semicolons) to clearly define statement boundaries, alongside traditional newlines.
- **Complex Expressions**: Nested math and function calls (e.g., `x = factorial(n-1) * results[0]`) are fully supported.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/schallten/elin.git
   cd elin
   ```

2. **Install Python dependencies (if any):**
   The compiler uses only Python standard library, so no additional packages are required.

3. **Build the C++ Executor (optional):**
   ```bash
   cd executor
   g++ -o elin_vm main.cpp  # Requires g++
   cd ..
   ```

## Web Visualizer

The project includes a web-based visualizer for debugging and learning:

1. Open `website/index.html` in your browser for the technical handbook.
2. Use `website/visualizer.html` to load and step through `.outz` bytecode files.
3. The visualizer shows stack state, memory, and execution flow in real-time.

## Quick Start

1. Create a simple ELIN program (`hello.elin`):
   ```elin
   let int x = 42;
   print x;
   halt;
   ```

2. Compile it:
   ```bash
   python3 compiler/main.py hello.elin
   ```

3. Run the bytecode:
   ```bash
   ./executor/elin_vm hello.outz
   ```

## Language Rules

ELIN enforces strict variable usage and type safety:

- **Explicit Typing**: Use `let <type> <name> = <value>` to declare new variables. Example: `let int x = 10`.
- **Functions**: `func <ret_type> <name> <arg_type> <arg_name> ...; <body>; end`.
- **Arrays**: `let arr int scores = [10, 20, 30]`. Access via `scores[index]`.
- **Reassignment**: To update an existing variable, omit `let`. Example: `x = 20`.
- **Variables must be used**: All declared variables must be used at least once.
- **Automatic HALT**: If your program doesn't end with a `halt` statement, the compiler adds one.

## The Compiler

The compiler takes a `.elin` file and generates a `.outz` file containing a String Pool, an Array Pool, and the bytecode instructions.

### Example: Recursive Factorial

```elin
func int factorial int n;
    if n <= 1;
        return 1;
    end;
    return n * factorial (n - 1);
end;

let int x = 5;
let int res = factorial x;
print res; # Outputs 120
halt;
```

## Instruction Set Table

| Opcode | Instruction | Description |
| :--- | :--- | :--- |
| **1** | PUSH | Pushes a numeric value onto the stack |
| **2** | LOAD | Loads a global variable onto the stack |
| **3** | STORE | Stores the top stack value into a global variable |
| **4** | ADD | Adds the top two values |
| **5** | SUB | Subtracts the top two values |
| **6** | MUL | Multiplies the top two values |
| **7** | DIV | Divides the top two values |
| **8** | PRINT | Prints a global variable |
| **9** | HALT | Stops execution |
| **10-15** | CMP_* | Comparison operators (==, !=, <, <=, >, >=) |
| **16-18** | JMP/JZ/JNZ | Jump and conditional jump operations |
| **20** | PUSH_STR | Pushes a string pool index onto the stack |
| **21** | PRINT_STR | Prints a string value from the pool |
| **30** | MAKE_ARR | Creates an array from the top N stack values |
| **31** | ARR_GET | Pops index and array ref, pushes value |
| **32** | ARR_SET | Pops value, index, and array ref, sets value |
| **33** | ARR_LEN | Pushes the length of the array onto the stack |
| **34** | PUSH_ARR | Pushes an array template index from the pool |
| **40** | CALL | Pushes a call frame and jumps to address |
| **41** | RET | Pops a call frame and returns with a value |
| **42** | LOAD_LOCAL | Loads a local variable from the current frame |
| **43** | STORE_LOCAL | Stores value into a local variable in the current frame |

## How to Run

To compile an ELIN file:
```bash
python3 compiler/main.py path/to/your_file.elin
```

To run the bytecode using the C++ Executor:
```bash
./executor/elin_vm path/to/your_file.outz
```
