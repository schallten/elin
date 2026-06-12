# Input & Output

## Numeric Input

`input()` reads a number from the keyboard while the program is running and pushes it onto the stack. Use it to make interactive programs:

```elin
print "Enter a number:";
let int x = input();
print "You typed:";
print x;
```

!!! warning
    `input()` blocks until you type a number and press Enter. The VM expects a valid integer — any non-numeric input will cause a runtime error.

## String Input

`read()` reads an entire line of text from stdin into the string pool and pushes its handle onto the stack. Unlike `input()`, it accepts any text, not just numbers:

```elin
print "What is your name?";
let str name = read();
print strcat("Hello, ", name);
```

## Writing Without Newlines

The `print` statement always appends a newline. Use `write` to output a string handle without a newline — useful for prompts:

```elin
write "Enter name: ";
flush;
let str name = read();
print strcat("Hello, ", name);
```

## Flushing Output

`flush` forces any buffered output to be written immediately. Combine with `write` for prompt-style interactions where the output must appear before blocking on input.
