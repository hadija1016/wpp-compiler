import re

# KEYWORDS (spec-exact — bool is NOT a valid type but IS recognized as a keyword
# so the parser can emit "Unknown data type 'bool'" instead of a generic error)
KEYWORDS = {
    "int", "float", "double", "char", "string",
    "if", "else", "while", "for", "return",
    "print", "read", "true", "false"
}

# "bool" is kept as a keyword so the parser can emit a specific
# "Unknown data type 'bool'" message instead of a generic error.
# "main" is intentionally NOT a keyword — it is a regular identifier
# that the parser's declaration() rule recognises by name.
KEYWORDS.add("bool")

# OPERATORS
OPERATORS = {
    "++": "INC",
    "--": "DEC",
    "==": "EQ",
    "!=": "NEQ",
    "<=": "LE",
    ">=": "GE",
    "&&": "AND",
    "||": "OR",
    "=":  "ASSIGN",
    "+":  "PLUS",
    "-":  "MINUS",
    "*":  "MUL",
    "/":  "DIV",
    "%":  "MOD",
    "<":  "LT",
    ">":  "GT",
    "!":  "NOT"
}

# SEPARATORS
SEPARATORS = {
    ";": "SEMICOLON",
    ",": "COMMA",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE"
}

# REGEX PATTERNS — order matters (longer/more-specific first)
TOKEN_PATTERNS = [
    ("COMMENT_MULTI",   re.compile(r"/\*[\s\S]*?\*/")),
    ("COMMENT_SINGLE",  re.compile(r"//.*")),
    ("STRING_LITERAL",  re.compile(r'"(\\.|[^"\\])*"')),
    ("CHAR_LITERAL",    re.compile(r"'(\\.|[^\\'])'")),
    ("FLOAT_LITERAL",   re.compile(r"\d+\.\d+")),
    ("INT_LITERAL",     re.compile(r"\d+")),
    ("IDENTIFIER",      re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")),
    ("OPERATOR",        re.compile(r"\+\+|--|==|!=|<=|>=|&&|\|\||[+\-*/%=<>!]")),
    ("SEPARATOR",       re.compile(r"[;,(){}]")),
]

# ── Classifier helpers ────────────────────────────────────────────────────────

def classify_identifier(value):
    if value in KEYWORDS:
        return f"KEYWORD_{value.upper()}", "KEYWORD"
    return "IDENTIFIER", "IDENTIFIER"


def classify_operator(value):
    return f"OPERATOR_{OPERATORS.get(value, 'UNKNOWN')}", "OPERATOR"


def classify_separator(value):
    return f"SEPARATOR_{SEPARATORS.get(value, 'UNKNOWN')}", "SEPARATOR"