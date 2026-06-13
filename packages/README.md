# ELIN Standard Packages

Community and official packages for the ELIN programming language.

## Available Packages

| Package | Description | Source |
|---------|-------------|--------|
| **math** | Power, min, max, clamp, sign | `packages/math/` |
| **strings** | Repeat, reverse, contains, starts_with, ends_with | `packages/strings/` |
| **collections** | Stack and queue data structures (heap-backed) | `packages/collections/` |
| **io** | Formatted print, prompts, separators | `packages/io/` |
| **time** | Elapsed time, unit conversion | `packages/time/` |
| **random** | Rand range, random bool, seeding | `packages/random/` |
| **debug** | Assert, trace, heap dump | `packages/debug/` |

## Usage

Add any package to your project:

```bash
python3 compiler/pkg.py add math ./packages/math
python3 compiler/pkg.py add strings ./packages/strings
```

Then use the functions in your ELIN code:

```elin
extern "math" power;
let int x = power(2, 10);
print x;   # 1024
halt;
```

## Writing Your Own Package

1. Create a folder with your `.elin` files
2. Add it: `pkg.py add mylib ./path/to/mylib`
3. Use functions from your library in `main.elin`
4. Build: `pkg.py build`

## License

Same as ELIN — see LICENSE in project root.
