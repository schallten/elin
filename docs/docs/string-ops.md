# String Operations

ELIN provides four built-in operations for text manipulation. All operate on string pool handles (the values stored in `str` variables).

## String Length

`strlen(s)` pushes the length of the string referenced by handle `s`:

```elin
let str msg = "hello";
let int n = strlen(msg);
print n;  # 5
```

## String Concatenation

`strcat(a, b)` concatenates two strings and pushes a new handle to the result. The original strings are unchanged:

```elin
let str a = "hello ";
let str b = "world";
let str c = strcat(a, b);
print c;  # hello world
```

## Substring

`substr(s, offset, length)` extracts a portion of a string and pushes a new handle. Offsets and lengths are clamped to the string bounds — out-of-range values won't crash:

```elin
let str s = "hello world";
let str a = substr(s, 0, 5);   # "hello"
let str b = substr(s, 6, 5);   # "world"
let str c = substr(s, 0, 100); # "hello world" (clamped)
```

## String Comparison

`strcmp(a, b)` compares two strings lexicographically and pushes `-1` if `a < b`, `0` if equal, or `1` if `a > b`:

```elin
print strcmp("abc", "def");  # -1
print strcmp("xyz", "xyz");  #  0
print strcmp("zzz", "aaa");  #  1
```

!!! info
    All string operations work with string pool handles, not raw pointers. The string pool grows at runtime to accommodate new strings created by `read()`, `strcat()`, and `substr()`.
