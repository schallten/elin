# VM Porting Plan

The current ELIN Virtual Machine is a monolithic C++ application (`main.cpp`). As the language and standard library grow, keeping everything in a single file will become unsustainable.

This document evaluates the options for refactoring or porting the ELIN VM, analyzing the pros and cons of four different approaches:

## 1. Many-file C++ (Refactoring)
Instead of porting to a new language, we simply refactor the existing `main.cpp` into multiple files (e.g., `executor/src/`, `executor/include/`) using CMake or a standard Makefile.

**Pros:**
- **Zero Porting Effort:** No need to rewrite existing working code (e.g., File I/O, opcode logic).
- **Embedded Target Compatibility:** C++ is the native language for ESP32/Arduino development, meaning the PC and Microcontroller VMs can easily share the same core codebase.
- **Performance:** C++ provides maximum control over memory and performance, crucial for a VM.

**Cons:**
- **Build Complexity:** C++ requires managing Makefiles/CMake, which can become complicated.
- **Safety:** Raw pointers and manual memory management (if used later) remain a risk.
- **Not "Modern":** Doesn't fit the "calm systems language" aesthetic ELIN is aiming for.

## 2. Odin
Odin is a fast, concise, readable, pragmatic, and open-sourced programming language designed with the intent of replacing C. It has a syntax that heavily inspired ELIN's design philosophy.

**Pros:**
- **Philosophy Alignment:** Odin aligns perfectly with ELIN's goal of being a "calm systems language" (data-oriented, non-OOP, explicit control flow).
- **Excellent C Interop:** Odin makes it very easy to call C libraries, which would be helpful for FFI.
- **Fast Compilation:** Odin compiles extremely quickly compared to C++.
- **Built-in Tools:** Comes with a built-in package manager and formatter.

**Cons:**
- **Microcontroller Support:** While Odin supports some freestanding targets (like WASM and some bare-metal), getting it to run on an ESP32 (xtensa or RISC-V) via the Arduino core is highly experimental and non-trivial. The ESP32 VM might still need to be written in C++.
- **Smaller Ecosystem:** Fewer libraries available compared to C/C++.

## 3. Nim
Nim is a statically typed compiled systems programming language that compiles down to C, C++, or JavaScript.

**Pros:**
- **Compiles to C/C++:** Since Nim outputs C/C++, it can theoretically be compiled directly for the ESP32 using the standard ESP-IDF or Arduino toolchains! This means a single Nim codebase could serve both PC and ESP32.
- **Syntax:** Clean, Python-like syntax that is highly readable.
- **Metaprogramming:** Excellent macro system which could be very useful for defining VM opcodes and dispatch loops efficiently.

**Cons:**
- **Hidden Control Flow:** Nim has features (like exceptions and garbage collection, though GC can be disabled/swapped for ARC/ORC) that slightly violate ELIN's "explicit control flow" philosophy.
- **C Interop Overhead:** While good, it's sometimes necessary to write C headers for Nim to understand underlying C structures (e.g., when interfacing with ESP-IDF).

## 4. Gleam
Gleam is a statically typed functional programming language that runs on the Erlang virtual machine (BEAM) or compiles to JavaScript.

**Pros:**
- **Safety:** Extremely robust type system and functional nature makes bugs very rare.
- **Concurrency:** Built on the Erlang VM, it has world-class concurrency support.
- **Modern syntax:** Very clean and developer-friendly.

**Cons:**
- **Not a Systems Language:** Gleam runs on a VM itself (BEAM) or Node.js/Browser (JavaScript). Writing a VM inside a VM introduces significant overhead.
- **Microcontroller Support:** Gleam cannot be compiled to run on an ESP32 microcontroller (unless running a heavy port of the Erlang VM or an embedded JS engine, which is not feasible for low-RAM devices).
- **Philosophy Mismatch:** Gleam is purely functional, whereas ELIN is procedural and data-oriented.

---

## 5. MicroPython

MicroPython is a lean implementation of Python 3 that runs on many microcontrollers (ESP32, STM32, etc.).

**Pros:**
- Familiar Python syntax, fast prototyping.
- Large standard library subset for IoT tasks.

**Cons:**
- Still an interpreter written in C; the ELIN VM would need to be re‑implemented in C and linked as a native module.
- **Main Issue:** Microcontrollers usually only support compiled C/C++ binaries. Languages like Nim, Odin, or Gleam must transpile to C/C++ to work, whereas MicroPython itself is limited to being an interpreter; you cannot run a full ELIN VM written in another language on the MCU without a C bridge.

Therefore, for strict MCU deployment the only reliable path remains native C/C++ (or a language that transpiles to C/C++ such as Nim).

## Conclusion & Recommendation

If **ESP32 Support** is a strict requirement for a single unified codebase, **Nim** and **Many-file C++** are the only truly viable options. 

- If you want to adhere strictly to the "calm systems" philosophy of ELIN and are okay with maintaining a separate C++ VM for the ESP32 (or pioneering bare-metal RISC-V compilation), **Odin** is the most aesthetically aligned choice.
- If you want the easiest path forward with the least friction for embedded support, **Many-file C++** is the safest bet. 
- **Nim** offers a middle ground (Pythonic syntax with C transpilation for ESP32).

*Recommendation:* **Refactor to Many-file C++** first to establish a solid architecture, then consider porting the PC version to **Odin** if you want the tooling to match the language's philosophy.
