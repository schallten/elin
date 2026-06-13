from ast_nodes import N, Node
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
    return N("program", statements=stmts), pos


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
            stmts.append(N("halt"))
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
        elif tok.type in ("IDENTIFIER", "LPAREN", "LBRACKET", "NUMBER", "STRING", "LEN", "ABS", "INPUT", "READ", "STRLEN", "STRCAT", "SUBSTR", "STRCMP", "TIME", "DELAY", "RTC_READ", "RTC_WRITE", "FOPEN", "FREAD", "FWRITE", "FCLOSE", "RAND", "ALLOC", "ALLOC_SEG", "FREE", "LOAD_H", "STORE_H", "HEAP_LEN", "REGION_ENTER", "REGION_EXIT", "SEG_USED"):
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
    return N("reassign", name=name_tok.value, value=expr), pos


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
    return N("array_assign", name=name_tok.value, index=index_expr, value=value_expr), pos


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
    return N("assign", type_name=full_type, name=name_tok.value, value=expr), pos


def parse_print(tokens, pos):
    pos += 1
    expr, pos = parse_expression(tokens, pos)
    return N("print", value_node=expr), pos


def parse_write(tokens, pos):
    pos += 1
    expr, pos = parse_expression(tokens, pos)
    return N("write", value=expr), pos


def parse_flush(tokens, pos):
    pos += 1
    return N("flush"), pos


def parse_srand(tokens, pos):
    pos += 1  # SRAND
    pos += 1  # LPAREN
    seed, pos = parse_expression(tokens, pos)
    if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
        pos += 1
    return N("srand", seed=seed), pos


def parse_extern(tokens, pos):
    pos += 1  # EXTERN
    lib_tok = peek(tokens, pos)
    pos += 1  # STRING (library name)
    name_tok = peek(tokens, pos)
    pos += 1  # IDENTIFIER (function name)
    if peek(tokens, pos) and peek(tokens, pos).type == "SEMI":
        pos += 1
    return N("extern", library=lib_tok.value, func_name=name_tok.value), pos


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
    return N("if", condition=cond, body=body, else_body=else_body), pos


def parse_while(tokens, pos):
    pos += 1
    cond, pos = parse_expression(tokens, pos)
    body, pos = parse_statements(tokens, pos)
    while peek(tokens, pos) and peek(tokens, pos).type in ("NEWLINE", "SEMI"):
        pos += 1
    pos += 1
    return N("while", condition=cond, body=body), pos


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
    return N("func_def", ret_type=ret_type, name=name, params=params, body=body), pos


def parse_return(tokens, pos):
    pos += 1
    expr, pos = parse_expression(tokens, pos)
    return N("return", value=expr), pos


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
                left = N("condition", op=curr.value, left=left, right=right)
            else:
                left = N("binary_op", op=curr.value, left=left, right=right)
            continue
        if curr.type == "LPAREN":
            if left.type == "variable":
                func_name = left.fields["name"]
                pos += 1
                args = []
                while pos < len(tokens) and peek(tokens, pos).type != "RPAREN":
                    arg, pos = parse_expression(tokens, pos)
                    args.append(arg)
                    if pos < len(tokens) and peek(tokens, pos).type == "COMMA":
                        pos += 1
                if pos < len(tokens) and peek(tokens, pos).type == "RPAREN":
                    pos += 1
                left = N("func_call", name=func_name, args=args)
                continue
        if precedence == 0 and curr.type in ("NUMBER", "STRING", "IDENTIFIER", "LPAREN", "LBRACKET", "LEN"):
            if left.type == "variable":
                left = N("func_call", name=left.fields["name"], args=[])
            if left.type == "func_call":
                arg, pos = parse_expression(tokens, pos, precedence=10)
                left.fields["args"].append(arg)
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
        return N("unary_op", op=tok.value, operand=operand), pos
    if tok.type == "NUMBER":
        pos += 1
        return N("number", value=tok.value), pos
    if tok.type == "STRING":
        pos += 1
        return N("string", value=tok.value), pos
    if tok.type == "IDENTIFIER":
        name = tok.value
        pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "LBRACKET":
            pos += 1
            idx, pos = parse_expression(tokens, pos)
            if peek(tokens, pos) and peek(tokens, pos).type == "RBRACKET":
                pos += 1
            return N("array_access", name=name, index=idx), pos
        return N("variable", name=name), pos
    if tok.type == "LBRACKET":
        return parse_array_literal(tokens, pos)
    if tok.type == "LPAREN":
        pos += 1
        expr, pos = parse_expression(tokens, pos)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return expr, pos

    # Function-call style keywords: (node_type, expected_args, has_parens, field_names)
    FUNC_STYLE = {
        "LEN":     ("array_len", 1, False, ["name"]),
        "ABS":     ("abs",       1, True,  ["value"]),
        "STRLEN":  ("strlen",    1, True,  ["value"]),
        "STRCAT":  ("strcat",    2, True,  ["left", "right"]),
        "SUBSTR":  ("substr",    3, True,  ["string", "offset", "length"]),
        "STRCMP":  ("strcmp",    2, True,  ["left", "right"]),
        "DELAY":   ("delay",     1, True,  ["value"]),
        "RTC_WRITE": ("rtc_write", 1, True, ["value"]),
        "FOPEN":   ("fopen",     1, True,  ["path"]),
        "FREAD":   ("fread",     1, True,  ["fd"]),
        "FWRITE":  ("fwrite",    2, True,  ["fd", "string"]),
        "FCLOSE":  ("fclose",    1, True,  ["fd"]),
        "ALLOC":   ("alloc",     1, True,  ["size"]),
        "ALLOC_SEG": ("alloc_seg", 2, True, ["size", "segment"]),
        "FREE":    ("free",      1, True,  ["handle"]),
        "LOAD_H":  ("load_h",    2, True,  ["handle", "index"]),
        "STORE_H": ("store_h",   3, True,  ["handle", "index", "value"]),
        "HEAP_LEN": ("heap_len", 1, True,  ["handle"]),
        "REGION_ENTER": ("region_enter", 1, True, ["segment"]),
        "REGION_EXIT":  ("region_exit",  1, True, ["segment"]),
        "SEG_USED":     ("seg_used",     1, True, ["segment"]),
    }

    # Zero-arg keywords (just the keyword, optional parens)
    ZERO_ARG = {
        "INPUT": "input", "READ": "read_str", "TIME": "time",
        "RTC_READ": "rtc_read", "RAND": "rand",
    }

    if tok.type in ZERO_ARG:
        pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "LPAREN":
            pos += 1
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        return N(ZERO_ARG[tok.type]), pos

    if tok.type in FUNC_STYLE:
        node_type, expected_args, has_parens, field_names = FUNC_STYLE[tok.type]
        pos += 1
        if has_parens:
            pos += 1  # skip LPAREN
        args = []
        for i in range(expected_args):
            if i > 0 and peek(tokens, pos) and peek(tokens, pos).type == "COMMA":
                pos += 1
            arg, pos = parse_expression(tokens, pos)
            args.append(arg)
        if peek(tokens, pos) and peek(tokens, pos).type == "RPAREN":
            pos += 1
        fields = dict(zip(field_names, args))
        return N(node_type, **fields), pos

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
    return N("array", elements=elements), pos
