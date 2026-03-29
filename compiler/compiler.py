import sys
from ops import (
    HALT, PUSH, LOAD, STORE, JMP, JZ, PRINT, PRINT_STR, PUSH_STR,
    OP_MAP, CMP_OP_MAP, CMP_OPERATORS
)
from ast_nodes import *

class Compiler:
    """
    The ELIN Code Generator walks the Abstract Syntax Tree (AST) and 
    translates it into linear bytecode instructions for the Virtual Machine.
    It now includes a compile-time type system and string pool.
    """
    def __init__(self, package_name):
        self.package_name = package_name
        self.bytecode = []
        # Symbol table to track variable memory indices and types
        self.variables = {}  # { name: {index, type, is_defined, is_used} }
        self.next_available_index = 0
        self.string_pool = [] # List of unique string literals

    def register_variable(self, name, var_type):
        """Assigns a memory index and type to a new variable."""
        if name in self.variables:
            print(f"Compilation Error: Variable '{name}' is already declared. Use reassignment without 'let'.")
            sys.exit(1)
            
        self.variables[name] = {
            'index': self.next_available_index,
            'type': var_type,
            'is_defined': True,
            'is_used': False
        }
        self.next_available_index += 1
        return self.variables[name]['index']

    def register_internal_variable(self, name, var_type):
        """Assigns or retrieves an internal variable index (used for print literals)."""
        if name not in self.variables:
            return self.register_variable(name, var_type)
        return self.variables[name]['index']


    def lookup_variable_index(self, name):
        """Retrieves variable index, ensuring it has been previously defined."""
        if name not in self.variables:
            print(f"Compilation Error: You are trying to use '{name}' before defining it.")
            sys.exit(1)
        self.variables[name]['is_used'] = True
        return self.variables[name]['index']

    def get_variable_type(self, name):
        """Retrieves the declared type of a variable."""
        if name not in self.variables:
            print(f"Compilation Error: Variable '{name}' is undefined.")
            sys.exit(1)
        return self.variables[name]['type']

    def infer_type(self, node):
        """Determines the result type of an expression node."""
        if isinstance(node, NumberNode):
            return "int"
        if isinstance(node, StringNode):
            return "str"
        if isinstance(node, VariableNode):
            return self.get_variable_type(node.name)
        if isinstance(node, BinaryOpNode):
            # For simplicity, ELIN currently assumes all math results in an int
            left_t = self.infer_type(node.left)
            right_t = self.infer_type(node.right)
            if left_t != "int" or right_t != "int":
                print(f"Type Error: Math operations only supported for 'int', found {left_t} and {right_t}.")
                sys.exit(1)
            return "int"
        if isinstance(node, ConditionNode):
            # Comparisons return boolean results (stored as int 0 or 1)
            return "int"
        return "unknown"

    def add_push(self, value):
        """Emits a PUSH instruction. Format: PUSH <0> <0> <0> <value>."""
        self.bytecode.append(f"{PUSH} 0 0 0 {value}")

    def add_push_str(self, string_value):
        """Adds a string to the pool and emits PUSH_STR with its index."""
        if string_value not in self.string_pool:
            self.string_pool.append(string_value)
        index = self.string_pool.index(string_value)
        self.bytecode.append(f"{PUSH_STR} {index}")

    def add_load(self, var_index):
        """Emits a LOAD instruction for a specific memory address."""
        self.bytecode.append(f"{LOAD} {var_index}")

    def add_store(self, var_index):
        """Emits a STORE instruction for a specific memory address."""
        self.bytecode.append(f"{STORE} {var_index}")

    def add_operation(self, opcode):
        """Emits a raw opcode (add, sub, halt, etc.)."""
        self.bytecode.append(str(opcode))

    def generate(self, ast):
        """
        Recursively walks the AST and generates corresponding bytecode.
        Implementation of the Visitor pattern (simplified).
        """
        if isinstance(ast, ProgramNode):
            for stmt in ast.statements:
                self.generate(stmt)

        elif isinstance(ast, AssignNode):
            # 1. Check types at compile time
            val_type = self.infer_type(ast.value)
            if ast.type_name != val_type:
                print(f"Type Error: Attempting to assign {val_type} to variable '{ast.name}' declared as {ast.type_name}.")
                sys.exit(1)
            
            # 2. Register variable and emit storage ops
            index = self.register_variable(ast.name, ast.type_name)
            self.generate(ast.value)
            self.add_store(index)

        elif isinstance(ast, ReassignNode):
            # 1. Ensure variable exists
            if ast.name not in self.variables:
                print(f"Compilation Error: Variable '{ast.name}' is undefined. Use 'let' to declare it.")
                sys.exit(1)

            # 2. Check types
            val_type = self.infer_type(ast.value)
            existing_type = self.variables[ast.name]['type']
            if val_type != existing_type:
                print(f"Type Error: Cannot assign {val_type} to variable '{ast.name}' of type {existing_type}.")
                sys.exit(1)

            # 3. Emit store ops
            index = self.variables[ast.name]['index']
            self.generate(ast.value)
            self.add_store(index)

        elif isinstance(ast, PrintNode):
            # The VM's PRINT expects a memory index, so literals must be stored first
            if isinstance(ast.value_node, NumberNode):
                val = ast.value_node.value
                temp_name = f"__literal_{val}"
                idx = self.register_internal_variable(temp_name, "int")
                self.add_push(val)
                self.add_store(idx)
                self.variables[temp_name]['is_used'] = True
                self.bytecode.append(f"{PRINT} {idx}")
            elif isinstance(ast.value_node, StringNode):
                val = ast.value_node.value
                temp_name = f"__literal_str_{val}"
                idx = self.register_internal_variable(temp_name, "str")
                self.add_push_str(val)
                self.add_store(idx)
                self.variables[temp_name]['is_used'] = True
                self.bytecode.append(f"{PRINT_STR} {idx}")
            else:
                # Variable: use type info to decide which print opcode to emit
                idx = self.lookup_variable_index(ast.value_node.name)
                var_type = self.get_variable_type(ast.value_node.name)
                if var_type == "str":
                    self.bytecode.append(f"{PRINT_STR} {idx}")
                else:
                    self.bytecode.append(f"{PRINT} {idx}")

        elif isinstance(ast, IfNode):
            self.generate(ast.condition)
            jz_index = len(self.bytecode)
            self.bytecode.append("PLACEHOLDER_JZ")
            for stmt in ast.body:
                self.generate(stmt)
            if ast.else_body:
                jmp_index = len(self.bytecode)
                self.bytecode.append("PLACEHOLDER_JMP")
                else_start = len(self.bytecode)
                self.bytecode[jz_index] = f"{JZ} {else_start}"
                for stmt in ast.else_body:
                    self.generate(stmt)
                finish = len(self.bytecode)
                self.bytecode[jmp_index] = f"{JMP} {finish}"
            else:
                finish = len(self.bytecode)
                self.bytecode[jz_index] = f"{JZ} {finish}"
        elif isinstance(ast, WhileNode):
            loop_start = len(self.bytecode)
            self.generate(ast.condition)
            jz_index = len(self.bytecode)
            self.bytecode.append("PLACEHOLDER_JZ")
            for stmt in ast.body:
                self.generate(stmt)
            self.bytecode.append(f"{JMP} {loop_start}")
            loop_end = len(self.bytecode)
            self.bytecode[jz_index] = f"{JZ} {loop_end}"
        elif isinstance(ast, HaltNode):
            self.add_operation(HALT)
        elif isinstance(ast, ConditionNode):
            self.generate(ast.left)
            self.generate(ast.right)
            self.add_operation(CMP_OP_MAP[ast.op])
        elif isinstance(ast, BinaryOpNode):
            self.generate(ast.left)
            self.generate(ast.right)
            self.add_operation(OP_MAP[ast.op])
        elif isinstance(ast, NumberNode):
            self.add_push(ast.value)
        elif isinstance(ast, StringNode):
            self.add_push_str(ast.value)
        elif isinstance(ast, VariableNode):
            idx = self.lookup_variable_index(ast.name)
            self.add_load(idx)

    def compile(self, source_code_string_or_lines):
        from lexer import lex
        from parser import Parser
        if isinstance(source_code_string_or_lines, list):
            source_code_string = "\n".join(source_code_string_or_lines)
        else:
            source_code_string = source_code_string_or_lines
        tokens = lex(source_code_string)
        parser = Parser(tokens)
        ast = parser.parse()
        self.generate(ast)
        if not self.bytecode or not self.bytecode[-1].startswith(str(HALT)):
            self.add_operation(HALT)
        self.verify_variables_were_used()
        
        # Build Section: String Pool
        string_section = [f"STR {i} {s}" for i, s in enumerate(self.string_pool)]
        if string_section:
            string_section = ["# --- STRING POOL ---"] + string_section + ["# --- END STRINGS ---", ""]
        else:
            string_section = []
            
        header = [
            f"# Package: {self.package_name}",
            "# Generated by ELIN Compiler",
            "#"
        ]
        return "\n".join(header + string_section + self.bytecode)
        
    def verify_variables_were_used(self):
        """Simple linter to catch unused variables."""
        unused_vars = [name for name, info in self.variables.items() if not info['is_used']]
        if unused_vars:
            print(f"Compilation Warning: You defined these variables but never used them: {', '.join(unused_vars)}")
            sys.exit(1)
