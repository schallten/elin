from ast_nodes import *
from ops import CMP_OPERATORS


def peek(tokens, pos):
    return tokens[pos] if pos < len(tokens) else None


def get_precedence(op_type, op_val):
    if op_type in ("COMMA", "RPAREN", "RBRACKET", "SEMI", "NEWLINE"):
        return -1
    if op_val in CMP_OPERATORS:
        return 1
    if op_val in ("+", "-"):
        return 2
    if op_val in ("*", "/", "%"):
        return 3
    return 0


def parse(tokens, pos=0):
    stmts, pos = parse_statements(tokens, pos, root=True)
    return ProgramNode(statements=stmts), pos


def parse_statements(tokens, pos, root=False):
    stmts = []
    while pos < len(tokens):
        tok = peek(tokens, pos)
        if tok.type in ("NEWLINE", "SEMI"):
            pos += 1
            continue
        if not root and tok.type in ("END", "ELSE", "WEND"):
            break
        if tok.type == "LET":
            node, pos = parse_let(tokens, pos)
            stmts.append(node)
        elif tok.type == "PRINT":
            node, pos = parse_print(tokens, pos)
            stmts.append(node)
        elif tok.type == "IF":
            node, pos = parse_if(tokens, pos)
            stmts.append(node)
        elif tok.type == "WHILE":
            node, pos = parse_while(tokens, pos)
            stmts.append(node)
        elif tok.type == "FUNC":
            node, pos = parse_func(tokens, pos)
            stmts.append(node)
        elif tok.type == "RETURN":
            node, pos = parse_return(tokens, pos)
            stmts.append(node)
        elif tok.type == "HALT":
            pos += 1
            stmts.append(HaltNode())
        elif tok.type == "WRITE":
            node, pos = parse_write(tokens, pos)
            stmts.append(node)
        elif tok.type == "FLUSH":
            node, pos = parse_flush(tokens, pos)
            stmts.append(node)
        elif tok.type == "SRAND":
            node, pos = parse_srand(tokens, pos)
            stmts.append(node)
        elif tok.type == "EXTERN":
            node, pos = parse_extern(tokens, pos)
            stmts.append(node)
        elif (tok.type == "IDENTIFIER" and pos + 1 < len(tokens)
              and peek(tokens, pos + 1).type == "LBRACKET"):
            node, pos = parse_array_assign(tokens, pos)
            stmts.append(node)
        elif (tok.type == "IDENTIFIER" and pos + 1 < len(tokens)
              and peek(tokens, pos + 1).type == "EQUALS"):
            node, pos = parse_reassign(tokens, pos)
            stmts.append(node)
        elif tok.type in ("IDENTIFIER", "LPAREN", "LBRACKET", "NUMBER", "STRING", "LEN", "ABS", "INPUT", "READ", "STRLEN", "STRCAT", "SUBSTR", "STRCMP", "TIME", "DELAY", "RTC_READ", "RTC_WRITE", "FOPEN", "FREAD", "FWRITE", "FCLOSE", "RAND", "ALLOC", "FREE", "LOAD_H", "STORE_H", "HEAP_LEN"):
            node, pos = parse_expression(tokens, pos)
            stmts.append(node)
        elif tok.type in ("COMMA", "RPAREN", "RBRACKET"):
            pos += 1
        else:
            raise Exception(f"Syntax error at {tok.type}: unexpected token")
    return stmts, pos


def parse_reassign(tokens, pos):
    name_tok = peek(tokens, pos)
    pos += 1
    pos += 1
    expr, pos = parse_expression(tokens, pos)
    return ReassignNode(name=name_tok.value, value=expr), pos


def parse_array_assign(tokens, pos):
    name_tok = peek(tokens, pos)
    pos += 1
    pos += 1
    index_expr, pos = parse_expression(tokens, pos)
    if peek(tokens, pos) and peek(tokens, pos).type == "RBRACKET":
        pos += 1
    if peek(tokens, pos) and peek(tokens, pos).type == "EQUALS":
        pos += 1
    value_expr, pos = parse_expression(tokens, pos)
    return ArrayAssignNode(name=name_tok.value, index=index_expr, value=value_expr), pos


def parse_let(tokens, pos):
    pos += 1
    is_array = False
    if peek(tokens, pos).type == "ARR":
        is_array = True
        pos += 1
    type_tok = peek(tokens, pos)
    pos += 1
    name_tok = peek(tokens, pos)
    pos += 1
    pos += 1
    expr, pos = parse_expression(tokens, pos)
    full_type = f"arr {type_tok.value}" if is_array else type_tok.value
    return AssignNode(type_name=full_type, name=name_tok.value, value=expr), pos


def parse_print(tokens, pos):
    pos += 1
    expr, pos = parse_expression(tokens, pos)
    return PrintNode(value_node=expr), pos


def parse_write(tokens, pos):
    pos += 1
    expr, pos = parse_expression(tokens, pos)
    return WriteNode(value=expr), pos


def parse_flush(tokens, pos):
    pos += 1
    return FlushNode(), pos


def parse_srand(tokens, pos):
    pos += 1  # SRAND
    pos += 1  # LPAREN
    seed, pos = parse_expression(tokens, pos)
    if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
        pos += 1
    return SrandNode(seed=seed), pos


def parse_extern(tokens, pos):
    pos += 1  # EXTERN
    lib_tok = peek(tokens, pos)
    pos += 1  # STRING (library name)
    name_tok = peek(tokens, pos)
    pos += 1  # IDENTIFIER (function name)
    if peek(tokens, pos) and peek(tokens, pos).type == "SEMI":
        pos += 1
    return ExternNode(library=lib_tok.value, func_name=name_tok.value), pos


def parse_if(tokens, pos):
    pos += 1
    cond, pos = parse_expression(tokens, pos)
    body, pos = parse_statements(tokens, pos)
    else_body = []
    while peek(tokens, pos) and peek(tokens, pos).type in ("NEWLINE", "SEMI"):
        pos += 1
    if peek(tokens, pos) and peek(tokens, pos).type == "ELSE":
        pos += 1
        else_body, pos = parse_statements(tokens, pos)
    while peek(tokens, pos) and peek(tokens, pos).type in ("NEWLINE", "SEMI"):
        pos += 1
    pos += 1
    return IfNode(condition=cond, body=body, else_body=else_body), pos


def parse_while(tokens, pos):
    pos += 1
    cond, pos = parse_expression(tokens, pos)
    body, pos = parse_statements(tokens, pos)
    while peek(tokens, pos) and peek(tokens, pos).type in ("NEWLINE", "SEMI"):
        pos += 1
    pos += 1
    return WhileNode(condition=cond, body=body), pos


def parse_func(tokens, pos):
    pos += 1
    ret_type = peek(tokens, pos).value
    pos += 1
    name = peek(tokens, pos).value
    pos += 1
    params = []
    while pos < len(tokens) and peek(tokens, pos).type not in ("NEWLINE", "SEMI"):
        p_is_arr = False
        if peek(tokens, pos).type == "ARR":
            p_is_arr = True
            pos += 1
        p_type = peek(tokens, pos).value
        pos += 1
        p_name = peek(tokens, pos).value
        pos += 1
        full_type = f"arr {p_type}" if p_is_arr else p_type
        params.append((full_type, p_name))
    body, pos = parse_statements(tokens, pos)
    if peek(tokens, pos) and peek(tokens, pos).type == "END":
        pos += 1
    return FunctionDefNode(ret_type=ret_type, name=name, params=params, body=body), pos


def parse_return(tokens, pos):
    pos += 1
    expr, pos = parse_expression(tokens, pos)
    return ReturnNode(value=expr), pos


def parse_expression(tokens, pos, precedence=0):
    left, pos = parse_primary(tokens, pos)
    while pos < len(tokens):
        curr = peek(tokens, pos)
        op_prec = get_precedence(curr.type, curr.value)
        if op_prec < 0:
            break
        if curr.type in ("OP", "CMP"):
            if op_prec <= precedence:
                break
            pos += 1
            right, pos = parse_expression(tokens, pos, op_prec)
            if curr.value in CMP_OPERATORS:
                left = ConditionNode(op=curr.value, left=left, right=right)
            else:
                left = BinaryOpNode(op=curr.value, left=left, right=right)
            continue
        if curr.type == "LPAREN":
            if isinstance(left, VariableNode):
                func_name = left.name
                pos += 1
                args = []
                while pos < len(tokens) and peek(tokens, pos).type != "RPAREN":
                    arg, pos = parse_expression(tokens, pos)
                    args.append(arg)
                    if pos < len(tokens) and peek(tokens, pos).type == "COMMA":
                        pos += 1
                if pos < len(tokens) and peek(tokens, pos).type == "RPAREN":
                    pos += 1
                left = FunctionCallNode(name=func_name, args=args)
                continue
        if precedence == 0 and curr.type in ("NUMBER", "STRING", "IDENTIFIER", "LPAREN", "LBRACKET", "LEN"):
            if isinstance(left, VariableNode):
                left = FunctionCallNode(name=left.name, args=[])
            if isinstance(left, FunctionCallNode):
                arg, pos = parse_expression(tokens, pos, precedence=10)
                left.args.append(arg)
                continue
        break
    return left, pos


def parse_primary(tokens, pos):
    tok = peek(tokens, pos)
    if not tok:
        raise Exception("Unexpected end of input")
    if tok.type == "OP" and tok.value in ("-", "!"):
        pos += 1
        operand, pos = parse_primary(tokens, pos)
        return UnaryOpNode(op=tok.value, operand=operand), pos
    if tok.type == "NUMBER":
        pos += 1
        return NumberNode(value=tok.value), pos
    if tok.type == "STRING":
        pos += 1
        return StringNode(value=tok.value), pos
    if tok.type == "IDENTIFIER":
        name = tok.value
        pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "LBRACKET":
            pos += 1
            idx, pos = parse_expression(tokens, pos)
            if peek(tokens, pos) and peek(tokens, pos).type == "RBRACKET":
                pos += 1
            return ArrayAccessNode(name=name, index=idx), pos
        return VariableNode(name=name), pos
    if tok.type == "LBRACKET":
        return parse_array_literal(tokens, pos)
    if tok.type == "LPAREN":
        pos += 1
        expr, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return expr, pos
    if tok.type == "LEN":
        pos += 1
        pos += 1
        name_tok = peek(tokens, pos)
        pos += 1
        pos += 1
        return ArrayLenNode(name=name_tok.value), pos
    if tok.type == "ABS":
        pos += 1
        pos += 1
        expr, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return AbsNode(value=expr), pos
    if tok.type == "INPUT":
        pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "LPAREN":
            pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return InputNode(), pos
    if tok.type == "READ":
        pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "LPAREN":
            pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return ReadStrNode(), pos
    if tok.type == "STRLEN":
        pos += 1
        pos += 1
        expr, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return StrLenNode(value=expr), pos
    if tok.type == "STRCAT":
        pos += 1
        pos += 1
        left, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "COMMA":
            pos += 1
        right, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return StrCatNode(left=left, right=right), pos
    if tok.type == "SUBSTR":
        pos += 1
        pos += 1
        string, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "COMMA":
            pos += 1
        offset, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "COMMA":
            pos += 1
        length, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return SubstrNode(string=string, offset=offset, length=length), pos
    if tok.type == "STRCMP":
        pos += 1
        pos += 1
        left, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "COMMA":
            pos += 1
        right, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return StrCmpNode(left=left, right=right), pos
    if tok.type == "TIME":
        pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "LPAREN":
            pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return TimeNode(), pos
    if tok.type == "DELAY":
        pos += 1
        pos += 1 # LPAREN
        expr, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return DelayNode(value=expr), pos
    if tok.type == "RTC_READ":
        pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "LPAREN":
            pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return RtcReadNode(), pos
    if tok.type == "RTC_WRITE":
        pos += 1
        pos += 1 # LPAREN
        expr, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return RtcWriteNode(value=expr), pos
    if tok.type == "FOPEN":
        pos += 1
        pos += 1
        path, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return FopenNode(path=path), pos
    if tok.type == "FREAD":
        pos += 1
        pos += 1
        fd, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return FreadNode(fd=fd), pos
    if tok.type == "FWRITE":
        pos += 1
        pos += 1
        fd, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "COMMA":
            pos += 1
        string_expr, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return FwriteNode(fd=fd, string=string_expr), pos
    if tok.type == "FCLOSE":
        pos += 1
        pos += 1
        fd, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return FcloseNode(fd=fd), pos
    if tok.type == "RAND":
        pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "LPAREN":
            pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return RandNode(), pos
    if tok.type == "ALLOC":
        pos += 1  # ALLOC
        pos += 1  # LPAREN
        size, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return AllocNode(size=size), pos
    if tok.type == "FREE":
        pos += 1  # FREE
        pos += 1  # LPAREN
        handle, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return FreeNode(handle=handle), pos
    if tok.type == "LOAD_H":
        pos += 1  # LOAD_H
        pos += 1  # LPAREN
        handle, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "COMMA":
            pos += 1
        index, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return LoadHNode(handle=handle, index=index), pos
    if tok.type == "STORE_H":
        pos += 1  # STORE_H
        pos += 1  # LPAREN
        handle, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "COMMA":
            pos += 1
        index, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "COMMA":
            pos += 1
        value, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return StoreHNode(handle=handle, index=index, value=value), pos
    if tok.type == "HEAP_LEN":
        pos += 1  # HEAP_LEN
        pos += 1  # LPAREN
        handle, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return HeapLenNode(handle=handle), pos
    raise Exception(f"Unexpected token in expression: {tok.type}")


def parse_array_literal(tokens, pos):
    pos += 1
    elements = []
    while pos < len(tokens) and peek(tokens, pos).type != "RBRACKET":
        elem, pos = parse_expression(tokens, pos)
        elements.append(elem)
        if pos < len(tokens) and peek(tokens, pos).type == "COMMA":
            pos += 1
    if pos < len(tokens) and peek(tokens, pos).type == "RBRACKET":
        pos += 1
    return ArrayNode(elements=elements), pos
