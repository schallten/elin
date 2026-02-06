"""ELIN Compiler
A simple stack-based bytecode compiler for the ELIN language.

Instruction Set:
1 = PUSH <4-byte operand>
2 = LOAD <index>
3 = STORE <index>
4 = ADD
5 = SUB
6 = MUL
7 = DIV
8 = PRINT
9 = HALT
"""

import os
import sys

class Compiler:
    """
    Compiler class to translate ELIN source code into a string-based bytecode.
    Each bytecode instruction is on its own line.
    """
    def __init__(self, package_name):
        self.package_name = package_name
        self.bytecode = []  # Each element is a complete instruction line
        self.variables = {}  # var_name -> {'index': int, 'defined': bool, 'used': bool}
        self.next_var_index = 0

    def add_push(self, value):
        """Adds a PUSH instruction with a 4-byte string representation."""
        # PUSH instruction is: 1 0 0 0 <value>
        self.bytecode.append(f"1 0 0 0 {value}")

    def add_load(self, index):
        """Adds a LOAD instruction."""
        # LOAD instruction is: 2 <index>
        self.bytecode.append(f"2 {index}")

    def add_store(self, index):
        """Adds a STORE instruction."""
        # STORE instruction is: 3 <index>
        self.bytecode.append(f"3 {index}")

    def add_op(self, op_code):
        """Adds a single-operation instruction (ADD, SUB, MUL, DIV, PRINT, HALT)."""
        self.bytecode.append(str(op_code))

    def define_variable(self, name):
        """Defines a new variable and returns its index."""
        if name not in self.variables:
            self.variables[name] = {
                'index': self.next_var_index,
                'defined': True,
                'used': False
            }
            self.next_var_index += 1
        return self.variables[name]['index']

    def use_variable(self, name):
        """Marks a variable as used and returns its index."""
        if name not in self.variables:
            print(f"Error: Variable '{name}' used before definition.")
            sys.exit(1)
        
        self.variables[name]['used'] = True
        return self.variables[name]['index']

    def get_var_index(self, name):
        """Retrieves variable index (for reading/using a variable)."""
        return self.use_variable(name)

    def parse_operand(self, operand):
        """Parses an operand and adds corresponding LOAD or PUSH bytecode."""
        if operand.isdigit() or (operand.startswith('-') and operand[1:].isdigit()):
            # It's a number, push it
            self.add_push(operand)
        else:
            # It's a variable, load it
            index = self.use_variable(operand)
            self.add_load(index)

    def handle_assignment(self, segments):
        """
        Handles 'let' statements.
        Supports:
            let x = 10
            let x = y + 5
        """
        # segments: ['let', 'x', '=', '10'] or ['let', 'x', '=', 'y', '+', '5']
        if len(segments) < 4:
            return

        target_var = segments[1]
        target_index = self.define_variable(target_var)

        if len(segments) == 4:
            # Simple assignment: let x = 10
            self.parse_operand(segments[3])
        elif len(segments) >= 6:
            # Expression assignment: let x = a + b
            self.parse_operand(segments[3])
            self.parse_operand(segments[5])
            op = segments[4]
            op_map = {'+': 4, '-': 5, '*': 6, '/': 7}
            if op in op_map:
                self.add_op(op_map[op])
            else:
                print(f"Error: Unknown operator '{op}'")
                sys.exit(1)
        
        # Store the result in the target variable
        self.add_store(target_index)

    def handle_print(self, segments):
        """Handles 'print' statements."""
        if len(segments) < 2:
            return
        
        var_name = segments[1]
        index = self.use_variable(var_name)
        
        # PRINT instruction is: 8 <index>
        self.bytecode.append(f"8 {index}")

    def handle_halt(self):
        """Adds a HALT instruction."""
        self.add_op(9)  # HALT

    def check_unused_variables(self):
        """Checks if all defined variables have been used at least once."""
        unused = []
        for var_name, var_info in self.variables.items():
            if var_info['defined'] and not var_info['used']:
                unused.append(var_name)
        
        if unused:
            print(f"Error: The following variables are defined but never used:")
            for var in unused:
                print(f"  - {var}")
            sys.exit(1)

    def generate_header(self):
        """Generates the 4-line header comment with package name."""
        header = [
            f"# Package: {self.package_name}",
            "#",
            "#",
            "#"
        ]
        return header

    def compile(self, lines):
        """Compiles source lines into bytecode with each instruction on its own line."""
        for line in lines:
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue
            
            segments = line.split()
            command = segments[0]

            if command == "let":
                self.handle_assignment(segments)
            elif command == "print":
                self.handle_print(segments)
            elif command == "halt":
                self.handle_halt()
            else:
                print(f"Warning: Unknown command '{command}' in line: {line}")
        
        # Ensure the program ends with a HALT instruction if not already there
        if not self.bytecode or self.bytecode[-1] != "9":
            self.bytecode.append("9")
        
        # Check for unused variables before finalizing
        self.check_unused_variables()
        
        # Generate the complete output with header
        header = self.generate_header()
        output_lines = header + self.bytecode
        
        return "\n".join(output_lines)

def main():
    """Main entry point for the ELIN compiler."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <source_file.elin>")
        sys.exit(1)

    source_path = sys.argv[1]
    if not os.path.exists(source_path):
        print(f"Error: File '{source_path}' not found.")
        sys.exit(1)

    # Determine output filename (source.elin -> source.outz)
    # Also use the filename (without extension) as package name
    stem = os.path.splitext(os.path.basename(source_path))[0]
    output_path = stem + ".outz"
    package_name = stem

    try:
        with open(source_path, "r") as f:
            lines = f.readlines()
        
        compiler = Compiler(package_name)
        bytecode_output = compiler.compile(lines)
        
        with open(output_path, "w") as f:
            f.write(bytecode_output)
            
        print(f"✓ Compilation successful: {source_path} -> {output_path}")
        print(f"\nGenerated Bytecode:")
        print(bytecode_output)

    except Exception as e:
        print(f"Error during compilation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()