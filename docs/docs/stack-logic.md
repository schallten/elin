# The Stack Logic

Most modern languages (like Python) let you name every temporary value. ELIN is different. It uses a **Stack**—a vertical pile of data where you can only interact with the very top item.

## The Plate Analogy

Imagine a stack of dinner plates. To add two numbers (5 and 10):

1. You **PUSH** 10 onto the stack.
2. You **PUSH** 5 onto the stack (it sits on top of 10).
3. You call **ADD**. The computer "pops" the top two plates, adds them, and places a new plate with "15" back on the stack.

!!! info
    This "Push/Pop" model is why ELIN is so fast. The CPU doesn't have to search for names in memory; it always knows that the data it needs is at the very top of the stack.
