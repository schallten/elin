# Loops

Use `while` loops to repeat actions until a condition fails. Combine with conditionals to build complex state machines.

```elin
let int limit = 3;
let int i = 0;
while i < limit;
    print i;
    i = i + 1;
wend;
```

!!! warning
    Because ELIN operates close to the hardware, infinite loops will stall the host CPU. Always make sure your loop condition will eventually be false.
