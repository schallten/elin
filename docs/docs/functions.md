# Functions & Scoping

Functions allow you to compartmentalize logic. In ELIN, every function has its own **Private Memory** (a Local Frame). Variables defined inside `func` stay inside `func`.

```elin
func int double int value;
    let int result = value * 2;
    return result;
end;

print double 5; # Outputs 10
```

!!! warning
    Attempting to access a variable defined inside a function from the "Main" script will result in a **Compilation Error**. This prevents "Side Effects" that can crash small hardware.
