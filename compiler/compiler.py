import sys
from ops import (
    HALT, PUSH, LOAD, STORE, JMP, JZ, PRINT, PRINT_STR, PUSH_STR,
    OP_MAP, CMP_OP_MAP,
    MAKE_ARR, ARR_GET, ARR_SET, ARR_LEN, PUSH_ARR,
    CALL, RET, LOAD_LOCAL, STORE_LOCAL,
    PUSH_CONST,
    DUP, DROP, SWAP
)
from ast_nodes import *

class TypeChecker:
    """
    Dedicated pass to validate types across the AST before code generation.
    """
    def __init__(self):
        self.variables = {} # name -> type
        self.functions = {} # name -> {ret, params}
        self.current_locals = None

    def infer_type(self, node):
        if isinstance(node, NumberNode): return "int"
        if isinstance(node, StringNode): return "str"
        if isinstance(node, VariableNode):
            if self.current_locals and node.name in self.current_locals:
                return self.current_locals[node.name]
            if node.name in self.variables:
                return self.variables[node.name]
            raise Exception(f"Type Error: Variable '{node.name}' undefined.")
        if isinstance(node, BinaryOpNode):
            l, r = self.infer_type(node.left), self.infer_type(node.right)
            if l != "int" or r != "int":
                raise Exception(f"Type Error: Math needs int, got {l}, {r}")
            return "int"
        if isinstance(node, ConditionNode): return "int"
        if isinstance(node, ArrayNode):
            if not node.elements: return "arr int"
            return f"arr {self.infer_type(node.elements[0])}"
        if isinstance(node, ArrayAccessNode):
            t = self.get_var_type(node.name)
            return t.split(" ", 1)[1] if " " in t else "int"
        if isinstance(node, ArrayLenNode): return "int"
        if isinstance(node, FunctionCallNode):
            if node.name not in self.functions:
                raise Exception(f"Type Error: Function '{node.name}' undefined")
            return self.functions[node.name]['ret_type']
        return "unknown"

    def get_var_type(self, name):
        if self.current_locals and name in self.current_locals:
            return self.current_locals[name]
        if name in self.variables:
            return self.variables[name]
        raise Exception(f"Type Error: Variable '{name}' undefined")

    def check(self, ast):
        if isinstance(ast, ProgramNode):
            for s in ast.statements: self.check(s)
        elif isinstance(ast, AssignNode):
            vt = self.infer_type(ast.value)
            if ast.type_name != vt:
                raise Exception(f"Type Error: {vt} -> {ast.type_name}")
            if self.current_locals is not None:
                self.current_locals[ast.name] = ast.type_name
            else:
                self.variables[ast.name] = ast.type_name
            self.check(ast.value)
        elif isinstance(ast, ReassignNode):
            vt, et = self.infer_type(ast.value), self.get_var_type(ast.name)
            if vt != et:
                raise Exception(f"Type Error: {vt} -> {et}")
            self.check(ast.value)
        elif isinstance(ast, PrintNode):
            self.check(ast.value_node)
        elif isinstance(ast, IfNode):
            self.check(ast.condition)
            for s in ast.body: self.check(s)
            for s in ast.else_body: self.check(s)
        elif isinstance(ast, WhileNode):
            self.check(ast.condition)
            for s in ast.body: self.check(s)
        elif isinstance(ast, FunctionDefNode):
            # Parse params for types: handle "arr int" vs "int"
            params = []
            for pt, pn in ast.params:
                params.append(pt)
            
            self.functions[ast.name] = {'ret_type': ast.ret_type, 'params': params}
            old = self.current_locals
            self.current_locals = {p[1]: p[0] for p in ast.params}
            for s in ast.body: self.check(s)
            self.current_locals = old
        elif isinstance(ast, FunctionCallNode):
            if ast.name not in self.functions:
                raise Exception(f"Type Error: Function '{ast.name}' undefined")
            info = self.functions[ast.name]
            if len(ast.args) != len(info['params']):
                raise Exception(f"Type Error: {ast.name} expects {len(info['params'])} args")
            for i, arg in enumerate(ast.args):
                at = self.infer_type(arg)
                if at != info['params'][i]:
                    raise Exception(f"Type Error: Arg {i} {at} -> {info['params'][i]}")
        elif isinstance(ast, BinaryOpNode):
            self.check(ast.left)
            self.check(ast.right)
        elif isinstance(ast, ConditionNode):
            self.check(ast.left)
            self.check(ast.right)
        elif isinstance(ast, ArrayAssignNode):
            self.check(ast.index)
            self.check(ast.value)
        elif isinstance(ast, ReturnNode):
            self.check(ast.value)

class Compiler:
    """
    Code Generator. Translates AST to bytecode.
    """
    def __init__(self, package_name):
        self.package_name = package_name
        self.bytecode = []
        self.variables = {}
        self.next_available_index = 0
        self.string_pool = []
        self.array_pool = []
        self.constant_pool = []
        self.functions = {}
        self.current_scope_locals = None
        self.local_next_index = 0

    def register_variable(self, name, var_type):
        if self.current_scope_locals is not None:
            idx = self.local_next_index
            self.current_scope_locals[name] = {'index': idx, 'type': var_type, 'is_used': False}
            self.local_next_index += 1
            return idx, True
        self.variables[name] = {'index': self.next_available_index, 'type': var_type, 'is_used': False}
        self.next_available_index += 1
        return self.variables[name]['index'], False

    def lookup_variable_index(self, name):
        if self.current_scope_locals and name in self.current_scope_locals:
            self.current_scope_locals[name]['is_used'] = True
            return self.current_scope_locals[name]['index'], True
        self.variables[name]['is_used'] = True
        return self.variables[name]['index'], False

    def infer_type(self, node):
        # Simplified infer for Print logic only
        if isinstance(node, StringNode): return "str"
        if isinstance(node, VariableNode):
            if self.current_scope_locals and node.name in self.current_scope_locals:
                return self.current_scope_locals[node.name]['type']
            return self.variables[node.name]['type']
        if isinstance(node, FunctionCallNode): return self.functions[node.name]['ret_type']
        return "int"

    def add_push(self, val):
        if val not in self.constant_pool: self.constant_pool.append(val)
        idx = self.constant_pool.index(val)
        self.bytecode.append(f"{PUSH_CONST} {idx}")
    def add_push_str(self, s):
        if s not in self.string_pool: self.string_pool.append(s)
        self.bytecode.append(f"{PUSH_STR} {self.string_pool.index(s)}")
    def add_push_arr(self, vals):
        if vals not in self.array_pool: self.array_pool.append(vals)
        self.bytecode.append(f"{PUSH_ARR} {self.array_pool.index(vals)}")
    def add_load(self, idx, local): self.bytecode.append(f"{LOAD_LOCAL if local else LOAD} {idx}")
    def add_store(self, idx, local): self.bytecode.append(f"{STORE_LOCAL if local else STORE} {idx}")
    def add_operation(self, op): self.bytecode.append(str(op))

    def generate(self, ast):
        if isinstance(ast, ProgramNode):
            for s in ast.statements: self.generate(s)
        elif isinstance(ast, AssignNode):
            idx, local = self.register_variable(ast.name, ast.type_name)
            self.generate(ast.value)
            self.add_store(idx, local)
        elif isinstance(ast, ArrayAssignNode):
            idx, local = self.lookup_variable_index(ast.name)
            self.add_load(idx, local)
            self.generate(ast.index)
            self.generate(ast.value)
            self.add_operation(ARR_SET)
        elif isinstance(ast, ReassignNode):
            idx, local = self.lookup_variable_index(ast.name)
            self.generate(ast.value)
            self.add_store(idx, local)
        elif isinstance(ast, PrintNode):
            self.generate(ast.value_node)
            self.add_operation(PRINT_STR if self.infer_type(ast.value_node) == "str" else PRINT)
        elif isinstance(ast, IfNode):
            self.generate(ast.condition)
            jz_idx = len(self.bytecode)
            self.bytecode.append("JZ_PLACEHOLDER")
            for s in ast.body: self.generate(s)
            if ast.else_body:
                jmp_idx = len(self.bytecode)
                self.bytecode.append("JMP_PLACEHOLDER")
                else_start = len(self.bytecode)
                self.bytecode[jz_idx] = f"{JZ} {else_start}"
                for s in ast.else_body: self.generate(s)
                finish = len(self.bytecode)
                self.bytecode[jmp_idx] = f"{JMP} {finish}"
            else:
                self.bytecode[jz_idx] = f"{JZ} {len(self.bytecode)}"
        elif isinstance(ast, WhileNode):
            start = len(self.bytecode)
            self.generate(ast.condition)
            jz_idx = len(self.bytecode)
            self.bytecode.append("JZ_PLACEHOLDER")
            for s in ast.body: self.generate(s)
            self.add_operation(f"{JMP} {start}")
            self.bytecode[jz_idx] = f"{JZ} {len(self.bytecode)}"
        elif isinstance(ast, HaltNode): self.add_operation(HALT)
        elif isinstance(ast, ConditionNode):
            self.generate(ast.left); self.generate(ast.right)
            self.add_operation(CMP_OP_MAP[ast.op])
        elif isinstance(ast, BinaryOpNode):
            self.generate(ast.left); self.generate(ast.right)
            self.add_operation(OP_MAP[ast.op])
        elif isinstance(ast, NumberNode): self.add_push(ast.value)
        elif isinstance(ast, StringNode): self.add_push_str(ast.value)
        elif isinstance(ast, VariableNode):
            idx, local = self.lookup_variable_index(ast.name)
            self.add_load(idx, local)
        elif isinstance(ast, ArrayNode):
            all_lit = all(isinstance(e, (NumberNode, StringNode)) for e in ast.elements)
            if all_lit:
                vals = []
                for e in ast.elements:
                    if isinstance(e, StringNode):
                        if e.value not in self.string_pool: self.string_pool.append(e.value)
                        vals.append(self.string_pool.index(e.value))
                    else: vals.append(e.value)
                self.add_push_arr(vals)
            else:
                for e in ast.elements: self.generate(e)
                self.add_operation(f"{MAKE_ARR} {len(ast.elements)}")
        elif isinstance(ast, ArrayAccessNode):
            idx, local = self.lookup_variable_index(ast.name)
            self.add_load(idx, local)
            self.generate(ast.index)
            self.add_operation(ARR_GET)
        elif isinstance(ast, ArrayLenNode):
            idx, local = self.lookup_variable_index(ast.name)
            self.add_load(idx, local)
            self.add_operation(ARR_LEN)
        elif isinstance(ast, FunctionDefNode):
            jmp_idx = len(self.bytecode)
            self.bytecode.append("JMP_PLACEHOLDER")
            func_start = len(self.bytecode)
            self.functions[ast.name] = {'address': func_start, 'ret_type': ast.ret_type, 'argc': len(ast.params)}
            self.current_scope_locals = {}
            self.local_next_index = 0
            for pt, pn in ast.params:
                self.current_scope_locals[pn] = {'index': self.local_next_index, 'type': pt, 'is_used': True}
                self.local_next_index += 1
            for s in ast.body: self.generate(s)
            if not self.bytecode[-1].startswith(str(RET)):
                self.add_push(0); self.add_operation(RET)
            self.current_scope_locals = None
            self.bytecode[jmp_idx] = f"{JMP} {len(self.bytecode)}"
        elif isinstance(ast, FunctionCallNode):
            func = self.functions[ast.name]
            for arg in ast.args: self.generate(arg)
            self.add_operation(f"{CALL} {func['address']} {func['argc']}")
        elif isinstance(ast, ReturnNode):
            self.generate(ast.value)
            self.add_operation(RET)

    def compile(self, source):
        from lexer import lex
        from parser import Parser
        src = "\n".join(source) if isinstance(source, list) else source
        tokens = lex(src)
        ast = Parser(tokens).parse()
        TypeChecker().check(ast)
        self.generate(ast)
        if not self.bytecode or not self.bytecode[-1].startswith(str(HALT)):
            self.add_operation(HALT)
        self.verify_usage()
        return self.bytecode

    def format_bytecode(self):
        consts = [f"CONST {i} {v}" for i, v in enumerate(self.constant_pool)]
        if consts: consts = ["# --- CONSTANT POOL ---"] + consts + ["# --- END CONSTANTS ---", ""]
        strs = [f"STR {i} {s}" for i, s in enumerate(self.string_pool)]
        if strs: strs = ["# --- STRING POOL ---"] + strs + ["# --- END STRINGS ---", ""]
        arrs = [f"ARR {i} {','.join(map(str, v))}" for i, v in enumerate(self.array_pool)]
        if arrs: arrs = ["# --- ARRAY POOL ---"] + arrs + ["# --- END ARRAYS ---", ""]
        header = [f"# Package: {self.package_name}", "# Generated by ELIN Compiler", "#"]
        return "\n".join(header + consts + strs + arrs + self.bytecode)

    def verify_usage(self):
        unused = [n for n, i in self.variables.items() if not i['is_used']]
        if unused:
            print(f"Compilation Warning: Unused variables: {', '.join(unused)}")
            sys.exit(1)

