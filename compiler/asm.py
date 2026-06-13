"""
ELIN Bytecode Assembler (Item 18)
Human-readable text format that assembles to .outz bytecode files.

Input format:
  - Header section: VERSION, CONST_COUNT, STR_COUNT, ARR_COUNT
  - Pool sections: CONST, STR, ARR entries
  - Bytecode instructions (opcode name or number + args)
  - Labels: NAME: defines a label, JMP/JZ/JNZ/CALL reference by name

Usage:
  python3 asm.py input.asm output.outz
"""

import sys
from pathlib import Path
from ops import (
    PUSH, LOAD, STORE, ADD, SUB, MUL, DIV, PRINT, HALT,
    CMP_EQ, CMP_NEQ, CMP_LT, CMP_LTE, CMP_GT, CMP_GTE,
    JMP, JZ, JNZ,
    PUSH_STR, PRINT_STR, PUSH_CONST,
    MAKE_ARR, ARR_GET, ARR_SET, ARR_LEN, PUSH_ARR,
    CALL, RET, LOAD_LOCAL, STORE_LOCAL,
    DUP, DROP, SWAP, NEG, NOT, NOP, INC, DEC,
    MOD, ABS, INPUT, TRACE,
    READ, WRITE, FLUSH,
    STRLEN, STRCAT, SUBSTR, STRCMP,
    FOPEN, FREAD, FWRITE, FCLOSE,
    TIME, DELAY, RTC_READ, RTC_WRITE,
    RAND, SRAND,
    ALLOC, FREE, LOAD_H, STORE_H, HEAP_LEN,
)

CALL_EXTERN = 86

MNEMONIC_TO_OPCODE = {
    "PUSH": PUSH, "LOAD": LOAD, "STORE": STORE,
    "ADD": ADD, "SUB": SUB, "MUL": MUL, "DIV": DIV,
    "PRINT": PRINT, "HALT": HALT,
    "CMP_EQ": CMP_EQ, "CMP_NEQ": CMP_NEQ,
    "CMP_LT": CMP_LT, "CMP_LTE": CMP_LTE,
    "CMP_GT": CMP_GT, "CMP_GTE": CMP_GTE,
    "JMP": JMP, "JZ": JZ, "JNZ": JNZ,
    "PUSH_STR": PUSH_STR, "PRINT_STR": PRINT_STR,
    "PUSH_CONST": PUSH_CONST,
    "MAKE_ARR": MAKE_ARR, "ARR_GET": ARR_GET,
    "ARR_SET": ARR_SET, "ARR_LEN": ARR_LEN, "PUSH_ARR": PUSH_ARR,
    "CALL": CALL, "RET": RET,
    "LOAD_LOCAL": LOAD_LOCAL, "STORE_LOCAL": STORE_LOCAL,
    "DUP": DUP, "DROP": DROP, "SWAP": SWAP,
    "NEG": NEG, "NOT": NOT, "NOP": NOP,
    "INC": INC, "DEC": DEC,
    "MOD": MOD, "ABS": ABS,
    "INPUT": INPUT, "TRACE": TRACE,
    "READ": READ, "WRITE": WRITE, "FLUSH": FLUSH,
    "STRLEN": STRLEN, "STRCAT": STRCAT,
    "SUBSTR": SUBSTR, "STRCMP": STRCMP,
    "FOPEN": FOPEN, "FREAD": FREAD,
    "FWRITE": FWRITE, "FCLOSE": FCLOSE,
    "TIME": TIME, "DELAY": DELAY,
    "RTC_READ": RTC_READ, "RTC_WRITE": RTC_WRITE,
    "RAND": RAND, "SRAND": SRAND,
    "CALL_EXTERN": CALL_EXTERN,
    "ALLOC": ALLOC, "FREE": FREE,
    "LOAD_H": LOAD_H, "STORE_H": STORE_H, "HEAP_LEN": HEAP_LEN,
}

JUMP_OPCODES = {JMP, JZ, JNZ}


def assemble(source_lines):
    const_pool = {}
    str_pool = {}
    arr_pool = {}
    header = {"VERSION": 1}
    labels = {}
    instructions = []

    in_header = True
    for raw_line in source_lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if in_header:
            if line.startswith("VERSION"):
                parts = line.split()
                header["VERSION"] = int(parts[1]) if len(parts) > 1 else 1
                continue
            if line.startswith("CONST_COUNT") or line.startswith("STR_COUNT") or line.startswith("ARR_COUNT"):
                continue
            in_header = False

        if line.startswith("CONST "):
            parts = line.split(None, 2)
            idx = int(parts[1])
            val = int(parts[2]) if len(parts) > 2 else 0
            const_pool[idx] = val
            continue

        if line.startswith("STR "):
            parts = line.split(None, 2)
            idx = int(parts[1])
            val = parts[2] if len(parts) > 2 else ""
            str_pool[idx] = val
            continue

        if line.startswith("ARR "):
            parts = line.split(None, 2)
            idx = int(parts[1])
            val = parts[2] if len(parts) > 2 else ""
            arr_pool[idx] = val
            continue

        parts = line.split()
        mnemonic = parts[0].upper()

        if mnemonic.endswith(":"):
            label_name = mnemonic[:-1]
            labels[label_name] = len(instructions)
            continue

        if mnemonic == "LABEL" and len(parts) >= 2:
            label_token = parts[1]
            if label_token.endswith(":"):
                labels[label_token[:-1]] = len(instructions)
            else:
                labels[label_token] = len(instructions)
            continue

        if mnemonic not in MNEMONIC_TO_OPCODE:
            try:
                int(mnemonic)
                instructions.append(line)
            except ValueError:
                print(f"Warning: Unknown mnemonic '{mnemonic}', treating as raw", file=sys.stderr)
                instructions.append(line)
            continue

        opcode_num = MNEMONIC_TO_OPCODE[mnemonic]
        args = parts[1:]

        if opcode_num in JUMP_OPCODES:
            if args:
                instructions.append((opcode_num, args[0]))
            else:
                instructions.append((opcode_num, None))
        elif opcode_num == CALL:
            instructions.append((opcode_num, args))
        elif opcode_num == CALL_EXTERN:
            instructions.append((opcode_num, args))
        elif args:
            instructions.append(f"{opcode_num} {' '.join(args)}")
        else:
            instructions.append(str(opcode_num))

    resolved = []
    for inst in instructions:
        if isinstance(inst, tuple):
            opcode_num, arg = inst
            if opcode_num in JUMP_OPCODES:
                if arg in labels:
                    resolved.append(f"{opcode_num} {labels[arg]}")
                else:
                    try:
                        int(arg)
                        resolved.append(f"{opcode_num} {arg}")
                    except (ValueError, TypeError):
                        print(f"Error: Undefined label '{arg}'", file=sys.stderr)
                        resolved.append(f"{opcode_num} 0")
            elif opcode_num == CALL:
                if len(arg) >= 1 and arg[0] in labels:
                    resolved.append(f"{opcode_num} {labels[arg[0]]} {' '.join(arg[1:])}")
                else:
                    resolved.append(f"{opcode_num} {' '.join(arg)}")
            elif opcode_num == CALL_EXTERN:
                resolved.append(f"{opcode_num} {' '.join(arg)}")
            else:
                resolved.append(f"{opcode_num} {' '.join(arg)}")
        else:
            resolved.append(str(inst))

    const_count = max(const_pool.keys()) + 1 if const_pool else 0
    str_count = max(str_pool.keys()) + 1 if str_pool else 0
    arr_count = max(arr_pool.keys()) + 1 if arr_pool else 0

    output = []
    output.append(f"VERSION {header['VERSION']}")
    output.append(f"CONST_COUNT {const_count}")
    output.append(f"STR_COUNT {str_count}")
    output.append(f"ARR_COUNT {arr_count}")
    output.append("")

    if const_pool:
        for i in range(const_count):
            output.append(f"CONST {i} {const_pool.get(i, 0)}")
        output.append("")

    if str_pool:
        for i in range(str_count):
            output.append(f"STR {i} {str_pool.get(i, '')}")
        output.append("")

    if arr_pool:
        for i in range(arr_count):
            output.append(f"ARR {i} {arr_pool.get(i, '')}")
        output.append("")

    output.extend(resolved)
    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input.asm> [output.outz]")
        return

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File '{input_path}' not found.")
        return

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix(".outz")

    source = input_path.read_text().splitlines()
    result = assemble(source)
    output_path.write_text(result)

    print(f"Assembled: {input_path.name} -> {output_path.name}")
    print("-" * 30)
    print(result)
    print("-" * 30)


if __name__ == "__main__":
    main()
