# Random Number Generation

ELIN includes a pseudorandom number generator for games, simulations, and any program that needs unpredictable values.

## Generating Random Numbers

`rand()` pushes a random 64-bit integer onto the stack:

```elin
let int x = rand();
print x;  # Something like 4964309973687637289
```

## Seeding the Generator

`srand(seed)` initializes the generator with a specific seed. Using the same seed always produces the same sequence — useful for reproducible results:

```elin
srand(42);
let int a = rand();
let int b = rand();

srand(42);
let int c = rand();
let int d = rand();

# a == c and b == d — same seed, same sequence
```

!!! info
    On PC, ELIN uses the Mersenne Twister algorithm (`std::mt19937_64`). On ESP, it uses the hardware `random()` function. If you don't call `srand()`, the generator is automatically seeded with a non-deterministic value at startup.

## Random in a Range

To get a random number within a specific range, use modulo:

```elin
# Random number between 0 and 99
let int dice = rand() % 100;
```
