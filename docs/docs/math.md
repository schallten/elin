# Mathematical Operations

ELIN supports standard arithmetic operations on integers: addition (+), subtraction (-), multiplication (*), and division (/). Operations follow stack-based evaluation.

## Basic Math

```elin
let int a = 10;
let int b = 5;
let int sum = a + b;  # 15
let int diff = a - b; # 5
let int prod = a * b; # 50
let int quot = a / b; # 2
```

## Complex Expressions

You can nest operations and function calls:

```elin
let int result = (a + b) * (a - b);  # 75
```

!!! info
    All math is performed on 64-bit integers. Division truncates towards zero.

## Modulo

The `%` operator gives you the remainder after division:

```elin
let int a = 17;
let int b = 5;
let int r = a % b;  # 2  (17 / 5 = 3 remainder 2)
```

## Absolute Value

`abs(x)` strips the sign off a number, always returning a non-negative result:

```elin
let int x = -42;
let int y = abs(x);  # 42
let int z = abs(5);   # 5
```
