"""
Opcode definitions for the ELIN compiler.
These numbers represent the instructions that the Virtual Machine understands.
"""

# --- Instruction Set ---
# Basic memory and value operations
PUSH  = 1  # Puts a value on the stack
LOAD  = 2  # Reads a variable from memory
STORE = 3  # Saves a value to a variable in memory

# Basic math operations
ADD   = 4  # +
SUB   = 5  # -
MUL   = 6  # *
DIV   = 7  # /

# System operations
PRINT     = 8  # Outputs an integer value to the screen
HALT      = 9  # Stops the program

# --- Comparison Instructions ---
# These compare two values and return true (1) or false (0)
CMP_EQ  = 10  # == (Equals)
CMP_NEQ = 11  # != (Not Equals)
CMP_LT  = 12  # <  (Less Than)
CMP_LTE = 13  # <= (Less Than or Equal)
CMP_GT  = 14  # >  (Greater Than)
CMP_GTE = 15  # >= (Greater Than or Equal)

# --- Control Flow Instructions ---
# These allow the program to jump to different lines of code
JMP = 16  # Jump to a specific address no matter what
JZ  = 17  # Jump only if the last value was Zero (False)
JNZ = 18  # Jump only if the last value was Not Zero (True)

# --- String Instructions ---
PUSH_STR  = 20 # Pushes a string pool index onto the stack
PRINT_STR = 21 # Prints a string variable (looks up string pool by stored index)

# --- Mappings ---
# These dictionaries help the compiler convert text like '+' or '==' into the numbers above.

# Map symbols to math opcodes
OP_MAP = {
    '+': ADD,
    '-': SUB,
    '*': MUL,
    '/': DIV
}

# Map symbols to comparison opcodes
CMP_OP_MAP = {
    '==': CMP_EQ,
    '!=': CMP_NEQ,
    '<':  CMP_LT,
    '<=': CMP_LTE,
    '>':  CMP_GT,
    '>=': CMP_GTE
}

# A simple list of all comparison symbols for quick checking
CMP_OPERATORS = list(CMP_OP_MAP.keys())
