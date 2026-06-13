# Packages

ELIN ships with official packages you can add to your projects. Each package is a collection of `.elin` functions that extend the language.

## Installing Packages

```bash
# From the ELIN repo
python3 compiler/pkg.py add math ./packages/math
python3 compiler/pkg.py add strings ./packages/strings

# From any git repo
python3 compiler/pkg.py add mylib https://github.com/user/elin-mylib
```

## Available Packages

### math

Extended math operations.

| Function | Signature | Description |
|----------|-----------|-------------|
| `power` | `int power(int base, int exp)` | Raise base to exp |
| `min` | `int min(int a, int b)` | Return smaller value |
| `max` | `int max(int a, int b)` | Return larger value |
| `clamp` | `int clamp(int val, int lo, int hi)` | Clamp val between lo and hi |
| `abs_val` | `int abs_val(int a)` | Absolute value |
| `sign` | `int sign(int a)` | Returns -1, 0, or 1 |

```elin
extern "math" power;
let int x = power(2, 10);
print x;   # 1024
```

---

### strings

String manipulation utilities.

| Function | Signature | Description |
|----------|-----------|-------------|
| `repeat_str` | `str repeat_str(str s, int n)` | Repeat string n times |
| `reverse` | `str reverse(str s)` | Reverse a string |
| `contains` | `int contains(str haystack, str needle)` | Check if substring exists |
| `starts_with` | `int starts_with(str s, str prefix)` | Check prefix |
| `ends_with` | `int ends_with(str s, str suffix)` | Check suffix |

```elin
let str greeting = repeat_str("ha", 3);
print strlen(greeting);   # 6
```

---

### collections

Dynamic data structures backed by heap allocation.

#### Stack

| Function | Signature | Description |
|----------|-----------|-------------|
| `stack_create` | `int stack_create(int capacity)` | Create a stack, returns handle |
| `stack_push` | `int stack_push(int h, int val)` | Push value, returns 0 or -1 |
| `stack_pop` | `int stack_pop(int h)` | Pop value, returns -1 if empty |
| `stack_peek` | `int stack_peek(int h)` | Peek at top, returns -1 if empty |
| `stack_size` | `int stack_size(int h)` | Current number of elements |
| `stack_destroy` | `int stack_destroy(int h)` | Free the stack |

#### Queue

| Function | Signature | Description |
|----------|-----------|-------------|
| `queue_create` | `int queue_create(int capacity)` | Create a queue, returns handle |
| `queue_enqueue` | `int queue_enqueue(int h, int val)` | Add to back, returns 0 or -1 |
| `queue_dequeue` | `int queue_dequeue(int h)` | Remove from front, returns -1 if empty |
| `queue_size` | `int queue_size(int h)` | Current number of elements |

```elin
let int s = stack_create(10);
stack_push(s, 42);
stack_push(s, 99);
print stack_pop(s);   # 99
print stack_pop(s);   # 42
```

---

### io

Formatted I/O helpers.

| Function | Signature | Description |
|----------|-----------|-------------|
| `prompt` | `str prompt(str message)` | Print message, read input |
| `print_repeat` | `int print_repeat(str c, int n)` | Print character n times |
| `print_sep` | `int print_sep()` | Print separator line |
| `print_header` | `int print_header(str title)` | Print section header |

```elin
let str name = prompt("Enter your name: ");
write "Hello, ";
write name;
write "!\n";
```

---

### time

Timing and duration utilities.

| Function | Signature | Description |
|----------|-----------|-------------|
| `elapsed` | `int elapsed(int start_time)` | Ms since start_time |
| `wait_until` | `int wait_until(int target_ms)` | Wait until absolute time |
| `ms_to_sec` | `int ms_to_sec(int ms)` | Convert ms to seconds |
| `ms_to_min` | `int ms_to_min(int ms)` | Convert ms to minutes |
| `seconds_since` | `int seconds_since(int start_time)` | Seconds since start_time |

```elin
let int start = time();
delay(1500);
print seconds_since(start);   # 1
```

---

### random

Random number utilities.

| Function | Signature | Description |
|----------|-----------|-------------|
| `rand_range` | `int rand_range(int lo, int hi)` | Random int in [lo, hi] |
| `rand_bool` | `int rand_bool(int chance_pct)` | True with N% probability |
| `pick` | `int pick(int a, int b)` | Randomly pick a or b |
| `rand_seed` | `int rand_seed(int seed)` | Seed the RNG |

```elin
let int dice = rand_range(1, 6);
print dice;   # random 1-6
```

---

### debug

Debugging and assertion utilities.

| Function | Signature | Description |
|----------|-----------|-------------|
| `assert_eq` | `int assert_eq(int actual, int expected)` | Fail if not equal |
| `assert_neq` | `int assert_neq(int actual, int unexpected)` | Fail if equal |
| `trace` | `int trace(str msg)` | Print trace message |
| `trace_val` | `int trace_val(str msg, int val)` | Print trace with value |
| `dump_heap` | `int dump_heap(int h)` | Print all cells in a heap block |

```elin
let int x = 42;
assert_eq(x, 42);   # passes
assert_eq(x, 0);    # prints 99999, 42, 0
```

---

## Writing Your Own Package

1. Create a folder with `.elin` files
2. Add it: `pkg.py add mylib ./path/to/mylib`
3. Use functions from your library in `main.elin`
4. Build: `pkg.py build`

Packages are just `.elin` files — no special format needed. The package manager finds all `.elin` files in the package directory and compiles them alongside your project.
