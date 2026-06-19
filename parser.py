# =============================================================
#  parser.py  –  Recursive Descent Parser for W++
# =============================================================

class ParseError(Exception):
    pass


class Parser:

    TYPE_KEYWORDS = {
        "int", "float", "char", "void",
        "string", "double", "long", "short"
    }
    # NOTE: "bool" is intentionally absent — it falls to the generic KEYWORD
    # branch so we can emit "Unknown data type 'bool'" exactly once.

    SYNC_KEYWORDS = TYPE_KEYWORDS | {
        "if", "else", "return", "for", "while", "do",
        "print", "println", "cout"
    }

    COMPARISON_OPS = {"==", "!=", "<", ">", "<=", ">="}

    def __init__(self, tokens):
        COMMENT_TYPES = {
            "COMMENT", "MULTILINE_COMMENT",
            "SINGLE_LINE_COMMENT", "BLOCK_COMMENT",
            "LINE_COMMENT", "COMMENT_SINGLE", "COMMENT_MULTI"
        }
        self.tokens  = [t for t in tokens if self._type(t) not in COMMENT_TYPES]
        self.current = 0
        self.errors  = []

    # ── Token accessors ───────────────────────────────────────
    def _type(self, t):  return t["type"]  if isinstance(t, dict) else t.type
    def _value(self, t): return t["value"] if isinstance(t, dict) else t.value
    def _line(self, t):  return t["line"]  if isinstance(t, dict) else t.line

    # ── Navigation ────────────────────────────────────────────
    def is_at_end(self): return self.current >= len(self.tokens)
    def peek(self):      return None if self.is_at_end() else self.tokens[self.current]
    def previous(self):  return self.tokens[self.current - 1] if self.current > 0 else None

    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, tok_type, value=None):
        t = self.peek()
        if t is None: return False
        if self._type(t) != tok_type: return False
        if value is not None and self._value(t) != value: return False
        return True

    def match(self, tok_type, value=None):
        if self.check(tok_type, value):
            self.advance(); return True
        return False

    def expect(self, tok_type, value=None, msg=None):
        if self.check(tok_type, value):
            return self.advance()
        tok  = self.peek()
        prev = self.previous()
        line = (self._line(tok)  if tok  else
                self._line(prev) if prev else "?")
        found_str    = f"'{self._value(tok)}'" if tok else "end of input"
        expected_str = f"'{value}'"            if value else tok_type
        self.errors.append({"line": line,
                             "message": msg or f"Expected {expected_str}, got {found_str}"})
        raise ParseError()

    # ── Error recovery ────────────────────────────────────────
    def synchronize(self):
        """Advance to the next safe statement boundary."""
        while not self.is_at_end():
            t = self.peek()
            if self._type(t) == "SEPARATOR" and self._value(t) == ";":
                self.advance(); return
            if self._type(t) == "SEPARATOR" and self._value(t) == "}":
                return
            if self._type(t) == "KEYWORD" and self._value(t) in self.SYNC_KEYWORDS:
                return
            self.advance()

    def _scan_for_not_op(self, error_line):
        """
        Look ahead from the current position to the end of the current
        statement (';') and emit the '!' error if found.
        This must be called BEFORE synchronize() consumes those tokens.
        """
        j = self.current
        while j < len(self.tokens):
            t = self.tokens[j]
            val = self._value(t)
            typ = self._type(t)
            if typ == "SEPARATOR" and val == ";":
                break
            if typ == "SEPARATOR" and val == "}":
                break
            if typ == "OPERATOR" and val == "!":
                self.errors.append({
                    "line": self._line(t),
                    "message": "Unexpected token '!'. Unary logical NOT operator is not supported."
                })
                break
            j += 1

    def _check_identifier(self, name, line):
        if name and name[0].isdigit():
            self.errors.append({
                "line": line,
                "message": f"Invalid identifier '{name}': names must begin with a letter or underscore"
            })

    # ── Entry point ───────────────────────────────────────────
    def parse(self):
        while not self.is_at_end():
            # A bare '}' at the top level has no matching '{' — skip it
            # to prevent the main loop from spinning on it forever.
            t = self.peek()
            if t and self._type(t) == "SEPARATOR" and self._value(t) == "}":
                self.advance()
                continue
            try:
                self.statement()
            except ParseError:
                self.synchronize()
        return self.errors

    # ── Statement dispatcher ──────────────────────────────────
    def statement(self):
        t = self.peek()
        if t is None: return

        kind = self._type(t)
        val  = self._value(t)

        if kind == "KEYWORD" and val in self.TYPE_KEYWORDS:
            self.declaration()

        elif kind == "KEYWORD" and val == "if":
            self.if_statement()

        elif kind == "KEYWORD" and val == "else":
            self.errors.append({"line": self._line(t),
                                 "message": "'else' without a matching 'if'"})
            self.advance(); self.synchronize()

        elif kind == "KEYWORD" and val == "return":
            self.return_statement()

        elif kind == "KEYWORD" and val == "while":
            self.while_statement()

        elif kind == "KEYWORD" and val == "for":
            self.for_statement()

        elif kind == "KEYWORD" and val in ("print", "println", "cout"):
            self.print_statement()

        elif kind == "KEYWORD":
            if val == "bool":
                self.errors.append({
                    "line": self._line(t),
                    "message": "Unknown data type 'bool'"
                })
                self.advance()           # consume 'bool'
                # Before we synchronize, check if the RHS contains '!'
                self._scan_for_not_op(self._line(t))
            else:
                self.errors.append({
                    "line": self._line(t),
                    "message": f"Keyword '{val}' is not fully supported in this W++ version"
                })
                self.advance()
            self.synchronize()

        elif kind == "IDENTIFIER":
            self.assignment_or_expression_statement()

        elif kind == "OPERATOR" and val in ("++", "--"):
            self.expression_statement()

        elif kind == "SEPARATOR" and val == "{":
            self.block()

        elif kind == "SEPARATOR" and val == ";":
            self.advance()

        elif kind == "SEPARATOR" and val == "}":
            return

        else:
            self.errors.append({"line": self._line(t),
                                 "message": f"Unexpected token '{val}'"})
            self.advance()

    # ── Declaration ───────────────────────────────────────────
    def declaration(self):
        type_tok  = self.advance()
        type_val  = self._value(type_tok)
        type_line = self._line(type_tok)

        if not self.check("IDENTIFIER"):
            tok   = self.peek()
            found = f"'{self._value(tok)}'" if tok else "end of input"
            line  = self._line(tok) if tok else type_line
            self.errors.append({"line": line,
                                 "message": f"Expected identifier after '{type_val}', got {found}"})
            raise ParseError()

        name_tok  = self.advance()
        name      = self._value(name_tok)
        name_line = self._line(name_tok)
        self._check_identifier(name, name_line)

        # main() function
        if name == "main" and self.check("SEPARATOR", "("):
            self.advance()
            self.expect("SEPARATOR", ")", "Expected ')' after 'main('")
            self.block()
            return

        # generic function definition / forward declaration
        if self.check("SEPARATOR", "("):
            self.advance()
            depth = 1
            while not self.is_at_end() and depth > 0:
                tok = self.peek()
                if self._type(tok) == "SEPARATOR":
                    if   self._value(tok) == "(": depth += 1
                    elif self._value(tok) == ")": depth -= 1
                self.advance()
            if self.check("SEPARATOR", "{"):
                self.block()
            else:
                self.expect("SEPARATOR", ";",
                            f"Expected '{{' or ';' after function '{name}(...)'")
            return

        # optional initialiser for the first declarator
        if self.match("OPERATOR", "="):
            try:
                self.expression()
            except ParseError:
                self.synchronize(); return

        # comma-separated additional declarators: int a = 1, b, c = 3;
        while self.match("SEPARATOR", ","):
            if not self.check("IDENTIFIER"):
                tok   = self.peek()
                found = f"'{self._value(tok)}'" if tok else "end of input"
                line  = self._line(tok) if tok else type_line
                self.errors.append({"line": line,
                                     "message": f"Expected identifier after ',' in '{type_val}' declaration, got {found}"})
                raise ParseError()
            extra_tok  = self.advance()
            extra_name = self._value(extra_tok)
            extra_line = self._line(extra_tok)
            self._check_identifier(extra_name, extra_line)
            if self.match("OPERATOR", "="):
                try:
                    self.expression()
                except ParseError:
                    self.synchronize(); return

        self.expect("SEPARATOR", ";",
                    f"Expected ';' after declaration of '{name}'")

    # ── Assignment or expression statement ────────────────────
    def assignment_or_expression_statement(self):
        name_tok = self.advance()
        name     = self._value(name_tok)
        line     = self._line(name_tok)
        self._check_identifier(name, line)

        if self.match("OPERATOR", "="):
            try:
                self.expression()
            except ParseError:
                self.synchronize(); return
            self.expect("SEPARATOR", ";",
                        f"Expected ';' after assignment to '{name}'")
            return

        if self.check("OPERATOR", "++") or self.check("OPERATOR", "--"):
            op = self._value(self.peek())
            self.advance()
            self.expect("SEPARATOR", ";", f"Expected ';' after '{name}{op}'")
            return

        while not self.is_at_end():
            t = self.peek()
            if self._type(t) == "OPERATOR" and self._value(t) in ("+", "-", "*", "/"):
                self.advance()
                try:
                    self.unary()
                except ParseError:
                    self.synchronize(); return
            else:
                break

        self.expect("SEPARATOR", ";", "Expected ';' after expression")

    def expression_statement(self):
        try:
            self.expression()
        except ParseError:
            self.synchronize(); return
        self.expect("SEPARATOR", ";", "Expected ';' after expression")

    # ── if / else ─────────────────────────────────────────────
    def if_statement(self):
        self.advance()  # consume 'if'
        try:
            self.expect("SEPARATOR", "(", "Expected '(' after 'if'")
            self.expression()
            self.expect("SEPARATOR", ")", "Expected ')' to close if-condition")
            self.block()
        except ParseError:
            self.synchronize(); return

        if not self.is_at_end():
            nxt = self.peek()
            if self._type(nxt) == "KEYWORD" and self._value(nxt) == "else":
                self.advance()
                try:
                    after = self.peek()
                    if after and self._type(after) == "KEYWORD" and self._value(after) == "if":
                        self.if_statement()
                    else:
                        self.block()
                except ParseError:
                    self.synchronize()

    # ── return ────────────────────────────────────────────────
    def return_statement(self):
        self.advance()
        if not self.is_at_end():
            t = self.peek()
            if not (self._type(t) == "SEPARATOR" and self._value(t) == ";"):
                try:
                    self.expression()
                except ParseError:
                    self.synchronize(); return
        self.expect("SEPARATOR", ";", "Expected ';' after return statement")

    # ── block ─────────────────────────────────────────────────
    def block(self):
        self.expect("SEPARATOR", "{", "Expected '{' to open block")
        while not self.is_at_end():
            t = self.peek()
            if self._type(t) == "SEPARATOR" and self._value(t) == "}":
                break
            try:
                self.statement()
            except ParseError:
                self.synchronize()
        self.expect("SEPARATOR", "}", "Expected '}' to close block")

    # ── while ─────────────────────────────────────────────────
    def while_statement(self):
        kw = self.advance()          # consume 'while'
        try:
            self.expect("SEPARATOR", "(", "Expected '(' after 'while'")
            self.expression()
            self.expect("SEPARATOR", ")", "Expected ')' to close while-condition")
            self.block()
        except ParseError:
            self.synchronize()

    # ── for-clause expression (init / increment) ──────────────
    def _for_clause_expr(self):
        """
        Parse one expression that may be a plain assignment:
            i = i + 1   |   i += 1   |   i++   |   ++i   |   expr
        Assignment operators that are single tokens (+=, -=, *=, /=)
        are handled the same way as plain =.
        """
        ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%="}

        # prefix ++ / --
        if self.check("OPERATOR", "++") or self.check("OPERATOR", "--"):
            self.advance()
            self.primary()
            return

        # try to detect  identifier <assign-op> expr
        # peek ahead: if token[0] is IDENTIFIER and token[1] is an assign op
        if self.check("IDENTIFIER"):
            saved = self.current
            self.advance()  # consume identifier tentatively
            t = self.peek()
            if t and self._type(t) == "OPERATOR" and self._value(t) in ASSIGN_OPS:
                self.advance()          # consume the assign op
                self.expression()       # parse RHS
                return
            # not an assignment — backtrack and fall through to expression()
            self.current = saved

        self.expression()

    # ── for ───────────────────────────────────────────────────
    def for_statement(self):
        self.advance()               # consume 'for'
        try:
            self.expect("SEPARATOR", "(", "Expected '(' after 'for'")

            # init clause: declaration OR assignment OR empty
            if not (self.check("SEPARATOR", ";")):
                t = self.peek()
                if t and self._type(t) == "KEYWORD" and self._value(t) in self.TYPE_KEYWORDS:
                    # inline declaration without its own ';' — parse manually
                    type_tok = self.advance()
                    type_val = self._value(type_tok)
                    if not self.check("IDENTIFIER"):
                        tok   = self.peek()
                        found = f"'{self._value(tok)}'" if tok else "end of input"
                        self.errors.append({"line": self._line(tok) if tok else self._line(type_tok),
                                             "message": f"Expected identifier after '{type_val}' in for-init"})
                        raise ParseError()
                    name_tok = self.advance()
                    self._check_identifier(self._value(name_tok), self._line(name_tok))
                    if self.match("OPERATOR", "="):
                        self.expression()
                    # handle comma-separated declarators in for-init
                    while self.match("SEPARATOR", ","):
                        if not self.check("IDENTIFIER"):
                            tok = self.peek()
                            found = f"'{self._value(tok)}'" if tok else "end of input"
                            self.errors.append({
                                "line": self._line(tok) if tok else "?",
                                "message": f"Expected identifier after ',' in for-init"
                            })
                            raise ParseError()
                        et = self.advance()
                        self._check_identifier(self._value(et), self._line(et))
                        if self.match("OPERATOR", "="):
                            self.expression()
                else:
                    # plain expression OR assignment (e.g. i = 0)
                    self._for_clause_expr()
            self.expect("SEPARATOR", ";", "Expected ';' after for-init")

            # condition clause (may be empty)
            if not self.check("SEPARATOR", ";"):
                self.expression()
            self.expect("SEPARATOR", ";", "Expected ';' after for-condition")

            # increment clause — may be i++, ++i, i = i + 1, i += 1, etc.
            if not self.check("SEPARATOR", ")"):
                self._for_clause_expr()
            self.expect("SEPARATOR", ")", "Expected ')' to close for-header")

            self.block()
        except ParseError:
            self.synchronize()

    # ── print / println / cout ────────────────────────────────
    def print_statement(self):
        kw_tok = self.advance()      # consume 'print' / 'println' / 'cout'
        kw     = self._value(kw_tok)

        # cout uses << stream-insertion syntax
        if kw == "cout":
            try:
                # expect at least one << operand
                self.expect("OPERATOR", "<<",
                            "Expected '<<' after 'cout'")
                self.expression()
                # allow chained insertions: cout << a << b << endl;
                while self.check("OPERATOR", "<<"):
                    self.advance()
                    # 'endl' is an identifier token — expression() handles it
                    self.expression()
            except ParseError:
                self.synchronize(); return
            self.expect("SEPARATOR", ";", "Expected ';' after cout statement")
            return

        # print / println: accept BOTH bare-value and parenthesised forms
        #   print "hello";          ← bare (no parens)
        #   print(x);               ← parenthesised
        #   print("a", b, 3);       ← parenthesised multi-arg
        try:
            if self.check("SEPARATOR", "("):
                # parenthesised form
                self.advance()
                if not self.check("SEPARATOR", ")"):
                    self.expression()
                    while self.match("SEPARATOR", ","):
                        self.expression()
                self.expect("SEPARATOR", ")", f"Expected ')' to close '{kw}(...)'")
            else:
                # bare form: print expr ;   (single expression, no parens required)
                if not self.check("SEPARATOR", ";"):
                    self.expression()
        except ParseError:
            self.synchronize(); return
        self.expect("SEPARATOR", ";", f"Expected ';' after '{kw}' statement")

    # ── Expressions ───────────────────────────────────────────
    def expression(self):  self.logical()

    def logical(self):
        """Handles && and || (lowest precedence above comparison)."""
        self.comparison()
        while not self.is_at_end():
            t = self.peek()
            if self._type(t) == "OPERATOR" and self._value(t) in ("&&", "||"):
                self.advance(); self.comparison()
            else:
                break

    def comparison(self):
        self.term()
        while not self.is_at_end():
            t = self.peek()
            if self._type(t) == "OPERATOR" and self._value(t) in self.COMPARISON_OPS:
                self.advance(); self.term()
            else:
                break

    def term(self):
        self.factor()
        while not self.is_at_end():
            t = self.peek()
            if self._type(t) == "OPERATOR" and self._value(t) in ("+", "-"):
                self.advance(); self.factor()
            else:
                break

    def factor(self):
        self.unary()
        while not self.is_at_end():
            t = self.peek()
            if self._type(t) == "OPERATOR" and self._value(t) in ("*", "/", "%"):
                self.advance(); self.unary()
            else:
                break

    def unary(self):
        t = self.peek()
        # Unsupported unary NOT
        if t and self._type(t) == "OPERATOR" and self._value(t) == "!":
            self.errors.append({
                "line": self._line(t),
                "message": "Unexpected token '!'. Unary logical NOT operator is not supported."
            })
            raise ParseError()

        if t and self._type(t) == "OPERATOR" and self._value(t) in ("++", "--"):
            self.advance(); self.primary(); return

        self.primary()

        if not self.is_at_end():
            t = self.peek()
            if t and self._type(t) == "OPERATOR" and self._value(t) in ("++", "--"):
                self.advance()

    def primary(self):
        t = self.peek()
        if t is None:
            prev = self.previous()
            line = self._line(prev) if prev else "?"
            self.errors.append({"line": line, "message": "Unexpected end of expression"})
            raise ParseError()

        tok_t = self._type(t)
        tok_v = self._value(t)
        tok_l = self._line(t)

        if tok_t == "IDENTIFIER":
            self.advance(); return

        # true / false are valid literal values
        if tok_t == "KEYWORD" and tok_v in ("true", "false"):
            self.advance(); return

        NUMERIC_TYPES = {
            "INTEGER", "INT_LITERAL", "INT",
            "FLOAT",   "FLOAT_LITERAL",
            "NUMBER",  "LITERAL",
            "DOUBLE",  "LONG"
        }
        if tok_t in NUMERIC_TYPES or "LITERAL" in tok_t.upper():
            self.advance(); return

        STRING_TYPES = {
            "STRING", "STRING_LITERAL", "STR",
            "CHAR",   "CHAR_LITERAL"
        }
        if tok_t in STRING_TYPES:
            self.advance(); return

        if tok_t == "SEPARATOR" and tok_v == "(":
            self.advance()
            self.expression()
            self.expect("SEPARATOR", ")", "Expected ')' in expression")
            return

        self.errors.append({"line": tok_l,
                             "message": f"Unexpected token '{tok_v}' in expression"})
        raise ParseError()