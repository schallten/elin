# Stack Operations

ELIN gives you direct control over the stack with a handful of low-level instructions. These let you rearrange values without going through variables.

## Duplicate & Drop

`dup` copies the top value and pushes the copy. `drop` removes the top value entirely:

```elin
# Stack: [10]
dup;       # Stack: [10, 10]  — top value doubled
drop;      # Stack: [10]      — back to one
```

## Swap

`swap` exchanges the top two values on the stack:

```elin
# Stack: [10, 20]
swap;      # Stack: [20, 10]  — positions flipped
```

## Negation & Logical Not

`neg` flips the sign of the top value. `not` turns zero into one, and anything else into zero:

```elin
# Stack: [42]
neg;       # Stack: [-42]
not;       # Stack: [0]       — -42 is non-zero, so NOT gives 0

# Stack: [0]
not;       # Stack: [1]       — zero becomes 1
```

## Increment & Decrement

`inc` and `dec` add or subtract 1 from a variable in a single instruction:

```elin
let int count = 5;
inc count;  # count is now 6
dec count;  # count is now 5
```
