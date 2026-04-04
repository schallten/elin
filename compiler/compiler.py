import sys
from ops import (
    HALT, PUSH, LOAD, STORE, JMP, JZ, PRINT, PRINT_STR, PUSH_STR,
    OP_MAP, CMP_OP_MAP, CMP_OPERATORS,
    MAKE_ARR, ARR_GET, ARR_SET, ARR_LEN, PUSH_ARR,
    CALL, RET, LOAD_LOCAL, STORE_LOCAL
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
        self.array_pool = []  # List of unique array templates (list of values)
        self.functions = {}   # {name: {'address': int, 'argc': int, 'ret_type': str}}
        self.current_scope_locals = None
        self.local_next_index = 0

    def register_variable(self, name, var_type):
        """Assigns a memory index and type to a new variable."""
        if self.current_scope_locals is not None:
            if name in self.current_scope_locals:
                print(f"Compilation Error: Local variable '{name}' is already declared.")
                sys.exit(1)
            idx = self.local_next_index
            self.current_scope_locals[name] = {'index': idx, 'type': var_type, 'is_defined': True, 'is_used': False}
            self.local_next_index += 1
            return idx, True
        else:
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
            return self.variables[name]['index'], False

    def register_internal_variable(self, name, var_type):
        """Assigns or retrieves an internal variable index (used for print literals).
           MUST be a global variable since PRINT only reads globals."""
        if name not in self.variables:
            self.variables[name] = {
                'index': self.next_available_index,
                'type': var_type,
                'is_defined': True,
                'is_used': False
            }
            self.next_available_index += 1
        return self.variables[name]['index'], False


    def lookup_variable_index(self, name):
        """Retrieves variable index, ensuring it has been previously defined."""
        if self.current_scope_locals is not None and name in self.current_scope_locals:
            self.current_scope_locals[name]['is_used'] = True
            return self.current_scope_locals[name]['index'], True
        if name not in self.variables:
            print(f"Compilation Error: You are trying to use '{name}' before defining it.")
            sys.exit(1)
        self.variables[name]['is_used'] = True
        return self.variables[name]['index'], False

    def get_variable_type(self, name):
        """Retrieves the declared type of a variable."""
        if self.current_scope_locals is not None and name in self.current_scope_locals:
            return self.current_scope_locals[name]['type']
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
        if isinstance(node, ArrayNode):
            if not node.elements: return "arr int"
            inner = self.infer_type(node.elements[0])
            return f"arr {inner}"
        if isinstance(node, ArrayAccessNode):
            full_type = self.get_variable_type(node.name)
            if " " in full_type: return full_type.split(" ", 1)[1]
            return "int"
        if isinstance(node, ArrayLenNode):
            return "int"
        if isinstance(node, FunctionCallNode):
            if node.name not in self.functions:
                print(f"Compilation Error: Function '{node.name}' is undefined.")
                sys.exit(1)
            return self.functions[node.name]['ret_type']
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

    def add_push_arr(self, array_elements):
        """Adds an array template to the pool and emits PUSH_ARR with its index."""
        if array_elements not in self.array_pool:
            self.array_pool.append(array_elements)
        index = self.array_pool.index(array_elements)
        self.bytecode.append(f"{PUSH_ARR} {index}")

    def add_load(self, var_index, is_local=False):
        """Emits a LOAD instruction for a specific memory address."""
        if is_local:
            self.bytecode.append(f"{LOAD_LOCAL} {var_index}")
        else:
            self.bytecode.append(f"{LOAD} {var_index}")

    def add_store(self, var_index, is_local=False):
        """Emits a STORE instruction for a specific memory address."""
        if is_local:
            self.bytecode.append(f"{STORE_LOCAL} {var_index}")
        else:
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
            index, is_local = self.register_variable(ast.name, ast.type_name)
            self.generate(ast.value)
            self.add_store(index, is_local)

        elif isinstance(ast, ArrayAssignNode):
            # 1. Load array ref
            idx, is_local = self.lookup_variable_index(ast.name)
            self.add_load(idx, is_local)
            # 2. Gen index
            self.generate(ast.index)
            # 3. Gen value
            self.generate(ast.value)
            # 4. Emit SET
            self.add_operation(ARR_SET)

        elif isinstance(ast, ReassignNode):
            # 2. Check types
            val_type = self.infer_type(ast.value)
            existing_type = self.get_variable_type(ast.name)
            if val_type != existing_type:
                print(f"Type Error: Cannot assign {val_type} to variable '{ast.name}' of type {existing_type}.")
                sys.exit(1)

            # 3. Emit store ops
            index, is_local = self.lookup_variable_index(ast.name)
            self.generate(ast.value)
            self.add_store(index, is_local)

        elif isinstance(ast, PrintNode):
            # The VM's PRINT expects a memory index, so we generate the expression,
            # store it in a temporary internal variable, and then print that index.
            val_type = self.infer_type(ast.value_node)
            self.generate(ast.value_node)
            
            temp_name = f"__print_temp_{val_type}"
            idx, is_loc = self.register_internal_variable(temp_name, val_type)
            self.add_store(idx, is_local=False)
            self.variables[temp_name]['is_used'] = True
            
            if val_type == "str":
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
            idx, is_local = self.lookup_variable_index(ast.name)
            self.add_load(idx, is_local)
        elif isinstance(ast, ArrayNode):
            # If all elements are simple literals, we can pool it
            all_literals = True
            for e in ast.elements:
                if not isinstance(e, (NumberNode, StringNode)):
                    all_literals = False
                    break
            
            if all_literals:
                vals = []
                for e in ast.elements:
                    if isinstance(e, StringNode):
                        # Ensure string is in pool and use its index
                        if e.value not in self.string_pool:
                            self.string_pool.append(e.value)
                        vals.append(self.string_pool.index(e.value))
                    else:
                        vals.append(e.value)
                self.add_push_arr(vals)
            else:
                for e in ast.elements:
                    self.generate(e)
                self.add_operation(f"{MAKE_ARR} {len(ast.elements)}")
        elif isinstance(ast, ArrayAccessNode):
            idx, is_local = self.lookup_variable_index(ast.name)
            self.add_load(idx, is_local)
            self.generate(ast.index)
            self.add_operation(ARR_GET)
        elif isinstance(ast, ArrayLenNode):
            idx, is_local = self.lookup_variable_index(ast.name)
            self.add_load(idx, is_local)
            self.add_operation(ARR_LEN)
        elif isinstance(ast, FunctionDefNode):
            jz_index = len(self.bytecode)
            self.bytecode.append("PLACEHOLDER_JMP")
            
            func_start = len(self.bytecode)
            self.functions[ast.name] = {
                'address': func_start,
                'ret_type': ast.ret_type,
                'argc': len(ast.params)
            }
            
            # Setup local scope
            self.current_scope_locals = {}
            self.local_next_index = 0
            
            for p_type, p_name in ast.params:
                self.current_scope_locals[p_name] = {'index': self.local_next_index, 'type': p_type, 'is_defined': True, 'is_used': True}
                self.local_next_index += 1
                
            for stmt in ast.body:
                self.generate(stmt)
                
            if not self.bytecode[-1].startswith(str(RET)):
                self.add_push(0)
                self.add_operation(RET)
                
            self.current_scope_locals = None
            func_end = len(self.bytecode)
            self.bytecode[jz_index] = f"{JMP} {func_end}"
        elif isinstance(ast, FunctionCallNode):
            if ast.name not in self.functions:
                print(f"Compilation Error: Call to undefined function '{ast.name}'")
                sys.exit(1)
            
            func_info = self.functions[ast.name]
            if len(ast.args) != func_info['argc']:
                print(f"Compilation Error: Function '{ast.name}' expects {func_info['argc']} arguments, but got {len(ast.args)}")
                sys.exit(1)
                
            for arg in ast.args:
                self.generate(arg)
                
            self.bytecode.append(f"{CALL} {func_info['address']} {func_info['argc']}")
        elif isinstance(ast, ReturnNode):
            if self.current_scope_locals is None:
                print("Compilation Error: 'return' outside of function.")
                sys.exit(1)
            self.generate(ast.value)
            self.add_operation(RET)

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
            
        # Build Section: Array Pool
        array_section = [f"ARR {i} {','.join(map(str, vals))}" for i, vals in enumerate(self.array_pool)]
        if array_section:
            array_section = ["# --- ARRAY POOL ---"] + array_section + ["# --- END ARRAYS ---", ""]
        else:
            array_section = []
            
        header = [
            f"# Package: {self.package_name}",
            "# Generated by ELIN Compiler",
            "#"
        ]
        return "\n".join(header + string_section + array_section + self.bytecode)
        
    def verify_variables_were_used(self):
        """Simple linter to catch unused variables."""
        unused_vars = [name for name, info in self.variables.items() if not info['is_used']]
        if unused_vars:
            print(f"Compilation Warning: You defined these variables but never used them: {', '.join(unused_vars)}")
            sys.exit(1)
