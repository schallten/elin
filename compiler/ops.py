"""Opcode definitions and operators for ELIN."""

# Instruction Set
PUSH = 1
LOAD = 2
STORE = 3
ADD = 4
SUB = 5
MUL = 6
DIV = 7
PRINT = 8
HALT = 9

# Comparison Operators
CMP_EQ = 10   # ==
CMP_NEQ = 11  # !=
CMP_LT = 12   # <
CMP_LTE = 13  # <=
CMP_GT = 14   # >
CMP_GTE = 15  # >=

# Control Flow
JMP = 16 # Unconditional jump
JZ  = 17 # Jump if zero
JNZ = 18 # Jump if not zero

OP_MAP = {
    '+': ADD,
    '-': SUB,
    '*': MUL,
    '/': DIV
}

CMP_OP_MAP = {
    '==': CMP_EQ,
    '!=': CMP_NEQ,
    '<': CMP_LT,
    '<=': CMP_LTE,
    '>': CMP_GT,
    '>=': CMP_GTE
}

CMP_OPERATORS = list(CMP_OP_MAP.keys())
