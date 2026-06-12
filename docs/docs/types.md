# Memory & Types

In low-power systems, memory is a precious resource. ELIN uses fixed types to ensure the computer knows exactly how many "slots" to reserve for your data.

| Type | Storage | Use Case |
|------|---------|----------|
| `int` | 64-bit Integer | Whole numbers, loop counters, math. |
| `str` | Pool Pointer | Text display and logging prefixes. |
| `arr` | Fixed Buffer | Lists of numbers (e.g. sensor history). |
