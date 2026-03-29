"""
Expression parsing logic (Infix to Postfix converter).
Used by the AST parser to handle operator precedence.
"""

def get_operator_precedence(operator):
    if operator in ["+", "-"]:
        return 1
    elif operator in ["*", "/"]:
        return 2
    return 0

def infix_to_postfix(tokens):
    output_queue = []
    operator_stack = []
    supported_operators = ["+", "-", "*", "/"]
    
    for token in tokens:
        if token == '(':
            operator_stack.append(token)
        elif token == ')':
            while operator_stack and operator_stack[-1] != '(':
                output_queue.append(operator_stack.pop())
            if operator_stack:
                operator_stack.pop()
        elif token in supported_operators:
            while operator_stack:
                top_operator = operator_stack[-1]
                if top_operator not in supported_operators:
                    break
                if get_operator_precedence(top_operator) >= get_operator_precedence(token):
                    output_queue.append(operator_stack.pop())
                else:
                    break
            operator_stack.append(token)
        else:
            output_queue.append(token)
    
    while operator_stack:
        output_queue.append(operator_stack.pop())
        
    return output_queue
