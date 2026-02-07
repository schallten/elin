"""ELIN Compiler
A simple stack-based bytecode compiler for the ELIN language.
in future , if need be this will be a multi file compiler instead of one file only

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
# new
10 = CMP_EQ   (==) pop two, push 1 if equal, 0 if not
11 = CMP_NEQ   (!=) pop two, push 1 if not equal, 0 if equal
12 = CMP_LT   (<) pop two, push 1 if less than, 0 if not
13 = CMP_LTE   (<=) pop two, push 1 if less than or equal, 0 if not
14 = CMP_GT   (>) pop two, push 1 if greater than, 0 if not
15 = CMP_GTE   (>=) pop two, push 1 if greater than or equal, 0 if not
16 = JMP <address> # jump to the address
17 = JZ <address> # jump if zero , meaning if the top of the stack is 0, jump to the address
18 = JNZ <address> # jump if not zero , meaning if the top of the stack is not 0, jump to the address
"""

import enum
import os
import sys

CMP_operators = ["==", "!=", "<", "<=", ">", ">="]  # used to check if current statement has comparsion operators

class Compiler:
    """
    Compiler class to translate ELIN source code into a string-based bytecode.
    Each bytecode instruction is on its own line.
    """
    def __init__(self, package_name):
        self.package_name = package_name
        self.bytecode = []  # Each element is a complete instruction line
        self.variables = {}  # var_name -> {'index': int, 'defined': bool, 'used': bool} , so the interpretor knows which variable is which number in the stack
        self.next_var_index = 0
        self.label_map = {} # label -> address , used for if and else . it works like this : 
        # when we see an if , we add a label to the label_map with the current address
        # when we see an else , we add a label to the label_map with the current address
        # when we see an end , we add a label to the label_map with the current address
        # then we go back and fill the addresses in the bytecode

    def priority(self, op): # used for expressions that is more than just two things , like a + b * c
        if op == "+" or op == "-":
            return 1
        elif op == "*" or op == "/":
            return 2
        else:
            return 0

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

        has_comp_op = False
        for token in segments:
            if token in CMP_operators:
                has_comp_op = True
                break

        if not has_comp_op:
            if len(segments) == 4:
                # Simple assignment: let x = 10
                self.parse_operand(segments[3])
            elif len(segments) == 6:
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

            elif len(segments) > 6:
                # Complex expression: let x = a + b * c
                # We'll use the Shunting Yard algorithm to convert to postfix
                # Then generate bytecode from postfix notation
                
                expression = segments[3:]  # Get everything after '='
                postfix = self.infix_to_postfix(expression)
                
                # Now generate bytecode from postfix
                for token in postfix:
                    if token in ['+', '-', '*', '/']:
                        # It's an operator
                        op_map = {'+': 4, '-': 5, '*': 6, '/': 7}
                        self.add_op(op_map[token])
                    else:
                        # It's an operand (number or variable)
                        self.parse_operand(token)      
    
        else:
            # Has comparison operator!
            # Find the position of the comparison operator
            # Start from index 3 (after 'let x =')
            pos_of_cmp_op = -1
            
            for i in range(3, len(segments)):
                if segments[i] in CMP_operators:
                    pos_of_cmp_op = i
                    break
            
            if pos_of_cmp_op == -1:
                print("Error: No valid comparison operator found")
                sys.exit(1)

            # Split into LHS and RHS
            # LHS is from index 3 to pos_of_cmp_op
            # RHS is from pos_of_cmp_op + 1 to end
            lhs = segments[3:pos_of_cmp_op]
            cmp_op = segments[pos_of_cmp_op]
            rhs = segments[pos_of_cmp_op + 1:]
            
            # Convert LHS to postfix and evaluate
            if len(lhs) == 1:
                # Simple operand like 'a' or '10'
                self.parse_operand(lhs[0])
            else:
                # Complex expression like '(a + b)' or 'a + b'
                lhs_postfix = self.infix_to_postfix(lhs)
                for token in lhs_postfix:
                    if token in ['+', '-', '*', '/']:
                        op_map = {'+': 4, '-': 5, '*': 6, '/': 7}
                        self.add_op(op_map[token])
                    else:
                        self.parse_operand(token)
            
            # Convert RHS to postfix and evaluate
            if len(rhs) == 1:
                # Simple operand like 'b' or '5'
                self.parse_operand(rhs[0])
            else:
                # Complex expression like '(c + d)' or 'c + d'
                rhs_postfix = self.infix_to_postfix(rhs)
                for token in rhs_postfix:
                    if token in ['+', '-', '*', '/']:
                        op_map = {'+': 4, '-': 5, '*': 6, '/': 7}
                        self.add_op(op_map[token])
                    else:
                        self.parse_operand(token)
            
            # Now apply the comparison operator
            cmp_op_map = {
                '==': 10, 
                '!=': 11, 
                '<': 12, 
                '<=': 13, 
                '>': 14, 
                '>=': 15
            }
            self.add_op(cmp_op_map[cmp_op])
        
        # Store the result in the target variable
        self.add_store(target_index)

    def infix_to_postfix(self, expression):
        """
        Converts infix expression to postfix using what i learnt in class.
        Now supports parentheses!
        Example: ['(', 'a', '+', 'b', ')', '*', 'c'] -> ['a', 'b', '+', 'c', '*']
        """
        output = []           # Final postfix result
        operator_stack = []   # Temporary holding place for operators
        
        operators = ['+', '-', '*', '/']  # All valid operators
        
        for token in expression:
            # Is this a left parenthesis?
            if token == '(':
                # Push it onto the stack
                operator_stack.append(token)
            
            # Is this a right parenthesis?
            elif token == ')':
                # Pop operators until we find the matching '('
                while len(operator_stack) > 0 and operator_stack[-1] != '(':
                    output.append(operator_stack.pop())
                
                # Pop the '(' itself
                if len(operator_stack) > 0:
                    operator_stack.pop()
            
            # Is this an operator?
            elif token in operators:                
                # Keep popping operators that should execute BEFORE this one
                # We pop if:
                # 1. Stack is not empty AND
                # 2. Top of stack is an operator (not '(') AND
                # 3. Top of stack has >= priority than current operator
                
                while len(operator_stack) > 0:
                    top = operator_stack[-1]  # Peek at top
                    
                    # Is the top an operator (not a parenthesis)?
                    if top not in operators:
                        break
                    
                    # Does top have higher or equal priority?
                    top_priority = self.priority(top)
                    current_priority = self.priority(token)
                    
                    if top_priority >= current_priority:
                        # Yes! Pop it to output
                        output.append(operator_stack.pop())
                    else:
                        # No! Stop popping
                        break
                
                # Now push current operator to stack
                operator_stack.append(token)
            
            else:
                # It's an operand (number or variable)
                # Just add it directly to output
                output.append(token)
        
        # Expression is done! Pop all remaining operators
        while len(operator_stack) > 0:
            output.append(operator_stack.pop())
        
        return output

    def handle_if(self,lines_to_check,has_else):
        # i am thinking of a c like syntax , but since the language is line based , and some users might have preference of their position of {} , i am not so sure
        # so i will go with if ... end , this way it can work for else as well
        # i am not sure if this is a good idea , but i will try it for now
        # uses labels
        # if the condition in if is false , it will jump to the end
        # if the condition in if is true , it will execute the code in if
        # if the condition in else is true , it will execute the code in else
        # if the condition in else is false , it will jump to the end
        # every if will have an end and so will every else , nothing like combined end for both of them
        # kind of like this will be the syntax
        # if a >=b
        # line1
        # line2
        # line3
        # end
        # else
        # line4
        # line5
        # line6
        # end
        # look for end statement
        end_positions = []
        for i,line in enumerate(lines_to_check):
            if line.strip() == "end":
                end_positions.append(i)
        
        if not end_positions:
            print("Error: Missing 'end' for 'if' statement")
            sys.exit(1)

        if has_else:
            else_pos = -1
            for i,line in enumerate(lines_to_check):
                if line.strip() == "else":
                    else_pos = i
                    break
            
            if else_pos == -1:
                print("Error: Missing 'else' for 'if' statement")
                sys.exit(1)

            # structre: if_line -> if_body -> end -> else -> else_body -> end
            if_line = lines_to_check[0]
            if_body = lines_to_check[1:end_positions[0]]
            else_body = []

        if_condition = if_line.strip().split()[1:] # everything after if
        self.handle_comparsion(if_condition)

        # now we need to generate jumps
        # # the stack now has : 1 (true) or 0 (false)

        if has_else:
            # structure:
            # [condition evaluation]
            # JZ else_label <- if false , jump to else
            # [if body]
            # JMP end_label <- if true , jump to end
            # else_label:
            # [else body]
            # end_label:

        # saving positions for JZ ( jump it zero - condition is false)
            jz_pos = len(self.bytecode)
            self.bytecode.append("PLACEHOLDER_JZ") # will fix this later

            # now handle if body
            for line in if_body:
                self.compile_line(line.strip())        


            # save postionm for JMP , jump to skip else
            jmp_pos = len(self.bytecode)
            self.bytecode.append("PLACEHOLDER_JMP") # will fix this later

            #else label where JZ should jump to
            else_label = len(self.bytecode)

            for line in else_body:
                self.compile_line(line.strip())

            # end label where JMP should jump to
            end_label = len(self.bytecode)

            # now fix the placeholders
            self.bytecode[jz_pos] = f"17 {else_label}"
            self.bytecode[jmp_pos] = f"16 {end_label}"
        
        else:
            # man i am tired
            # strucutre:
            # [condition eval]
            # JZ end_label <- if false, jump to end
            # [if body]
            # end_label:

            # save position for JZ
            jz_pos = len(self.bytecode)
            self.bytecode.append("PLACEHOLDER_JZ") # will fix this later

            # now handle if body
            for line in if_body:
                self.compile_line(line.strip())

            # end label where JZ should jump to
            end_label = len(self.bytecode)

            # now fix the placeholder
            self.bytecode[jz_pos] = f"17 {end_label}"

    def compile_line(self,line):
        # used to compile single lines inside if elses
        # will do tmrw
        # am tired
        pass

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
            elif command == "if":
                # thinking to pass from if to end as a list , then check for else and pass from else to end as well , combined in that list
                lines_of_conditions = []
                has_else = False
                while segments[-1] != "end":
                    lines_of_conditions.append(line)
                    line = lines.pop(0)
                    if segments[-1] == "else":
                        has_else = True
                self.handle_if(lines_of_conditions,has_else)
                
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