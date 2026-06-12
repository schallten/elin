# Conditionals

ELIN supports basic branching via `if` blocks, allowing your script to make choices based on program state.

```elin
let int value = 5;
if value > 0;
    print "Positive";
else;
    print "Negative or Zero";
end;
```

Under the hood, these compile down to `JZ` (Jump if Zero) instructions, gracefully skipping sections of bytecode when conditions aren't met.
