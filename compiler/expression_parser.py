"""Expression parsing logic for ELIN."""

def get_priority(op):
    """Returns the precedence of an operator."""
    if op in ["+", "-"]:
        return 1
    elif op in ["*", "/"]:
        return 2
    return 0

def infix_to_postfix(expression):
    """
    Converts infix expression to postfix using the Shunting Yard algorithm.
    Supports parentheses and operator precedence.
    """
    output = []
    operator_stack = []
    operators = ["+", "-", "*", "/"]
    
    for token in expression:
        if token == '(':
            operator_stack.append(token)
        elif token == ')':
            while operator_stack and operator_stack[-1] != '(':
                output.append(operator_stack.pop())
            if operator_stack:
                operator_stack.pop() # Remove '('
        elif token in operators:
            while operator_stack:
                top = operator_stack[-1]
                if top not in operators:
                    break
                if get_priority(top) >= get_priority(token):
                    output.append(operator_stack.pop())
                else:
                    break
            operator_stack.append(token)
        else:
            # It's an operand (number or variable)
            output.append(token)
    
    while operator_stack:
        output.append(operator_stack.pop())
        
    return output
