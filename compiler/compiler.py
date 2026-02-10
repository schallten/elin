import sys
from ops import (
    HALT, OP_MAP, CMP_OP_MAP, CMP_OPERATORS
)
from expression_parser import infix_to_postfix

class Compiler:
    """
    Core ELIN Compiler class.
    Translates source lines into bytecode instructions.
    """
    def __init__(self, package_name):
        self.package_name = package_name
        self.bytecode = []
        self.variables = {} # name -> {'index': int, 'defined': bool, 'used': bool}
        self.next_var_index = 0

    def add_push(self, value):
        self.bytecode.append(f"1 0 0 0 {value}")

    def add_load(self, index):
        self.bytecode.append(f"2 {index}")

    def add_store(self, index):
        self.bytecode.append(f"3 {index}")

    def add_op(self, op_code):
        self.bytecode.append(str(op_code))

    def define_variable(self, name):
        if name not in self.variables:
            self.variables[name] = {
                'index': self.next_var_index,
                'defined': True,
                'used': False
            }
            self.next_var_index += 1
        return self.variables[name]['index']

    def use_variable(self, name):
        if name not in self.variables:
            print(f"Error: Variable '{name}' used before definition.")
            sys.exit(1)
        self.variables[name]['used'] = True
        return self.variables[name]['index']

    def parse_operand(self, operand):
        if operand.isdigit() or (operand.startswith('-') and operand[1:].isdigit()):
            self.add_push(operand)
        else:
            index = self.use_variable(operand)
            self.add_load(index)

    def handle_assignment(self, segments):
        if len(segments) < 4: return
        
        target_var = segments[1]
        target_index = self.define_variable(target_var)
        
        expression = segments[3:]
        # Check for comparison in assignment
        pos_of_cmp = -1
        for i, token in enumerate(expression):
            if token in CMP_OPERATORS:
                pos_of_cmp = i
                break
        
        if pos_of_cmp != -1:
            lhs = expression[:pos_of_cmp]
            cmp_op = expression[pos_of_cmp]
            rhs = expression[pos_of_cmp + 1:]
            
            self._compile_expression(lhs)
            self._compile_expression(rhs)
            self.add_op(CMP_OP_MAP[cmp_op])
        else:
            self._compile_expression(expression)
            
        self.add_store(target_index)

    def _compile_expression(self, expr_tokens):
        if len(expr_tokens) == 1:
            self.parse_operand(expr_tokens[0])
        else:
            postfix = infix_to_postfix(expr_tokens)
            for token in postfix:
                if token in OP_MAP:
                    self.add_op(OP_MAP[token])
                else:
                    self.parse_operand(token)

    def handle_comparison(self, segments):
        pos = -1
        for i, token in enumerate(segments):
            if token in CMP_OPERATORS:
                pos = i
                break
        
        if pos == -1:
            print("Error: No comparison operator found")
            sys.exit(1)
            
        self._compile_expression(segments[:pos])
        self._compile_expression(segments[pos + 1:])
        self.add_op(CMP_OP_MAP[segments[pos]])

    def handle_while(self, while_condition, while_body):
        start_addr = len(self.bytecode)
        self.handle_comparison(while_condition)
        
        jz_pos = len(self.bytecode)
        self.bytecode.append("PLACEHOLDER_JZ")
        
        self.compile_raw(while_body)
        
        self.bytecode.append(f"16 {start_addr}") # JMP back
        
        end_addr = len(self.bytecode)
        self.bytecode[jz_pos] = f"17 {end_addr}" # Fill JZ

    def handle_if(self, lines, has_else):
        else_pos = -1
        end_pos = -1
        depth = 0
        
        for i in range(1, len(lines)):
            line = lines[i].strip()
            if line.startswith("if"): depth += 1
            elif line.startswith("end"):
                if depth == 0:
                    end_pos = i
                    break
                else: depth -= 1
            elif line == "else" and depth == 0:
                else_pos = i

        if end_pos == -1:
            print("Error: Missing 'end' for 'if'")
            sys.exit(1)

        if_line = lines[0]
        self.handle_comparison(if_line.split()[1:])

        if has_else and else_pos != -1:
            if_body = lines[1:else_pos]
            else_body = lines[else_pos + 1:end_pos]

            jz_pos = len(self.bytecode)
            self.bytecode.append("PLACEHOLDER_JZ")
            self.compile_raw(if_body)

            jmp_pos = len(self.bytecode)
            self.bytecode.append("PLACEHOLDER_JMP")

            else_label = len(self.bytecode)
            self.compile_raw(else_body)

            end_label = len(self.bytecode)
            self.bytecode[jz_pos] = f"17 {else_label}"
            self.bytecode[jmp_pos] = f"16 {end_label}"
        else:
            if_body = lines[1:end_pos]
            jz_pos = len(self.bytecode)
            self.bytecode.append("PLACEHOLDER_JZ")
            self.compile_raw(if_body)
            end_label = len(self.bytecode)
            self.bytecode[jz_pos] = f"17 {end_label}"

    def handle_print(self, segments):
        if len(segments) < 2: return
        var_name = segments[1]

        if var_name.isdigit() or (var_name.startswith('-') and var_name[1:].isdigit()):
             temp_var = f"__literal_{var_name}"
             index = self.define_variable(temp_var)
             self.add_push(var_name)
             self.add_store(index)
             self.variables[temp_var]['used'] = True
        else:
             index = self.use_variable(var_name)
        
        self.bytecode.append(f"8 {index}")

    def compile_line(self, line):
        if not line or line.startswith("//") or line.startswith("#"): return
        if line in ["end", "else", "wend"]: return
        
        segments = line.split()
        cmd = segments[0]

        if cmd == "let": self.handle_assignment(segments)
        elif cmd == "print": self.handle_print(segments)
        elif cmd == "halt": self.add_op(HALT)
        else:
            print(f"Error: Unknown command '{cmd}'")
            sys.exit(1)

    def compile_raw(self, lines):
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("//") or line.startswith("#"):
                i += 1
                continue
            
            segments = line.split()
            cmd = segments[0]

            if cmd == "while":
                block, i_next = self._collect_block(lines, i, "while", "wend")
                self.handle_while(block[0].split()[1:], block[1:-1])
                i = i_next
            elif cmd == "if":
                block, i_next = self._collect_block(lines, i, "if", "end")
                # Special check for else sibling
                has_else = False
                for b_line in block:
                    if b_line.strip() == "else":
                        has_else = True
                        break
                self.handle_if(block, has_else)
                i = i_next
            else:
                self.compile_line(line)
                i += 1

    def _collect_block(self, lines, start_idx, open_tag, close_tag):
        block = [lines[start_idx].strip()]
        i = start_idx + 1
        depth = 1
        while i < len(lines) and depth > 0:
            curr = lines[i].strip()
            block.append(curr)
            if curr.startswith(open_tag): depth += 1
            elif curr.startswith(close_tag): depth -= 1
            i += 1
        return block, i

    def check_unused_variables(self):
        unused = [name for name, info in self.variables.items() if not info['used']]
        if unused:
            print(f"Error: Unused variables: {', '.join(unused)}")
            sys.exit(1)

    def compile(self, lines):
        self.compile_raw(lines)
        if not self.bytecode or self.bytecode[-1] != str(HALT):
            self.add_op(HALT)
        self.check_unused_variables()
        header = [f"# Package: {self.package_name}", "#", "#", "#"]
        return "\n".join(header + self.bytecode)
