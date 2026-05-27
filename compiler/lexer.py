"""
Lexer for ELIN source code.
Responsible for converting a string of raw code into a stream of usable Tokens.
"""

class Token:
    """Represents a single meaningful unit of code (like a keyword or number)."""
    def __init__(self, type, value=None):
        self.type = type  # "LET", "WHILE", "NUMBER", etc.
        self.value = value  # The raw string value if applicable (e.g. for identifiers)
        
    def __repr__(self):
        """String representation for easier debugging during development."""
        return f"Token({self.type}, {repr(self.value)})" if self.value else f"Token({self.type})"

def lex(code_string):
    """
    Main entry point for tokenization.
    Takes a multi-line source string and returns a flat list of Token objects.
    Now handles strings with spaces and properly separates operators.
    """
    tokens = []
    lines = code_string.splitlines()
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("#"):
            continue
            
        i = 0
        while i < len(line):
            char = line[i]
            
            # Skip whitespace
            if char.isspace():
                i += 1
                continue
                
            # String literals
            if char == '"':
                i += 1
                start = i
                while i < len(line) and line[i] != '"':
                    i += 1
                val = line[start:i]
                tokens.append(Token("STRING", val))
                i += 1
                continue
            
            # Identifiers and Keywords
            if char.isalpha() or char == '_':
                start = i
                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    i += 1
                part = line[start:i]
                
                if part == "let": tokens.append(Token("LET"))
                elif part == "func": tokens.append(Token("FUNC"))
                elif part == "return": tokens.append(Token("RETURN"))
                elif part == "print": tokens.append(Token("PRINT"))
                elif part == "if": tokens.append(Token("IF"))
                elif part == "else": tokens.append(Token("ELSE"))
                elif part == "end": tokens.append(Token("END"))
                elif part == "while": tokens.append(Token("WHILE"))
                elif part == "wend": tokens.append(Token("WEND"))
                elif part == "halt": tokens.append(Token("HALT"))
                elif part == "arr": tokens.append(Token("ARR"))
                elif part == "len": tokens.append(Token("LEN"))
                elif part in ["int", "str"]: tokens.append(Token("TYPE", part))
                else: tokens.append(Token("IDENTIFIER", part))
                continue
                
            # Numbers
            if char.isdigit():
                start = i
                while i < len(line) and line[i].isdigit():
                    i += 1
                tokens.append(Token("NUMBER", line[start:i]))
                continue
            
            # Operators and Comparisons
            # Check two-char ops first
            two_char = line[i:i+2]
            if two_char in ["==", "!=", "<=", ">="]:
                tokens.append(Token("CMP", two_char))
                i += 2
                continue
            
            if char in ["<", ">"]:
                tokens.append(Token("CMP", char))
                i += 1
                continue
                
            if char == "=":
                tokens.append(Token("EQUALS"))
                i += 1
                continue
                
            if char in ["+", "-", "*", "/"]:
                tokens.append(Token("OP", char))
                i += 1
                continue
                
            if char == "!":
                tokens.append(Token("OP", "!"))
                i += 1
                continue

            if char == "[":
                tokens.append(Token("LBRACKET"))
                i += 1
                continue
            if char == "]":
                tokens.append(Token("RBRACKET"))
                i += 1
                continue
            if char == ",":
                tokens.append(Token("COMMA"))
                i += 1
                continue
                
            if char == ";":
                tokens.append(Token("SEMI"))
                i += 1
                continue
                
            if char == "(":
                tokens.append(Token("LPAREN"))
                i += 1
                continue
            if char == ")":
                tokens.append(Token("RPAREN"))
                i += 1
                continue
                
            # Comments (Inline) - ignore the rest of the line
            if line[i:i+2] == "//":
                i = len(line)
                continue
                
            if char == "#":
                i = len(line)
                continue
                
            i += 1 # Catch-all for unknown chars
                
        # We will stop returning NEWLINE to enforce SEMI if desired, but 
        # let's keep NEWLINE for backward compatibility and add SEMI explicitly.
        tokens.append(Token("NEWLINE"))
        
    return tokens
