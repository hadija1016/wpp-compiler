from tokens import (
    TOKEN_PATTERNS,
    classify_identifier,
    classify_operator,
    classify_separator
)

class Lexer:
    def __init__(self):
        self.tokens = []

    def tokenize(self, code):
        self.tokens = []
        lines = code.split("\n")

        for line_no, line in enumerate(lines, start=1):
            i = 0
            while i < len(line):
                if line[i].isspace():
                    i += 1
                    continue

                matched = False
                for token_type, pattern in TOKEN_PATTERNS:
                    m = pattern.match(line, i)
                    if m:
                        value = m.group(0)
                        if token_type.startswith("COMMENT"):
                            i = m.end()
                            matched = True
                            break
                        token = self._build_token(token_type, value, line_no)
                        self.tokens.append(token)
                        i = m.end()
                        matched = True
                        break

                if not matched:
                    self.tokens.append({
                        "type": "INVALID",
                        "category": "INVALID",
                        "value": line[i],
                        "line": line_no
                    })
                    i += 1

        return self.tokens

    def _build_token(self, token_type, value, line_no):
        if token_type == "IDENTIFIER":
            specific, broad = classify_identifier(value)
            # broad  = "KEYWORD" or "IDENTIFIER"
            # specific = "KEYWORD_INT", "KEYWORD_IF", or "IDENTIFIER"
            t_type   = "KEYWORD" if broad == "KEYWORD" else "IDENTIFIER"
            category = specific          # e.g. KEYWORD_INT, IDENTIFIER

        elif token_type == "OPERATOR":
            specific, _broad = classify_operator(value)
            # specific = "OPERATOR_PLUS", "OPERATOR_ASSIGN", …
            t_type   = "OPERATOR"
            category = specific          # e.g. OPERATOR_PLUS

        elif token_type == "SEPARATOR":
            specific, _broad = classify_separator(value)
            # specific = "SEPARATOR_SEMICOLON", "SEPARATOR_LPAREN", …
            t_type   = "SEPARATOR"
            category = specific          # e.g. SEPARATOR_SEMICOLON

        elif "LITERAL" in token_type:
            t_type = "LITERAL"
            # Map regex pattern names → spec names
            if   token_type == "INT_LITERAL":    category = "LITERAL_INTEGER"
            elif token_type == "FLOAT_LITERAL":  category = "LITERAL_FLOAT"
            elif token_type == "STRING_LITERAL": category = "LITERAL_STRING"
            elif token_type == "CHAR_LITERAL":   category = "LITERAL_CHAR"
            else:                                category = "LITERAL"

        else:
            t_type   = token_type
            category = token_type

        return {
            "type":     t_type,
            "category": category,
            "value":    value,
            "line":     line_no
        }


class Analyzer:
    def __init__(self, tokens):
        self.tokens = tokens

    def analyze(self):
        summary      = {}
        line_dist    = {}
        identifiers  = {}
        literals     = {}
        total_tokens = len(self.tokens)

        for t in self.tokens:
            t_type   = t["type"]       # broad:    KEYWORD, OPERATOR, LITERAL, SEPARATOR, IDENTIFIER
            category = t["category"]   # specific: KEYWORD_INT, OPERATOR_PLUS, LITERAL_INTEGER, …
            value    = t["value"]
            line     = t["line"]

            # ── Token Type Summary ────────────────────────────────────────
            # Key on the SPECIFIC type so each subtype gets its own row
            # (KEYWORD_INT separate from KEYWORD_FLOAT, etc.)
            if category not in summary:
                summary[category] = {
                    "category": t_type,   # broad category for the 'Category' column
                    "count":    0,
                    "lines":    set()
                }
            summary[category]["count"] += 1
            summary[category]["lines"].add(line)

            # ── Line distribution ─────────────────────────────────────────
            line_dist[line] = line_dist.get(line, 0) + 1

            # ── Identifier stats (broad type == IDENTIFIER) ───────────────
            if t_type == "IDENTIFIER":
                if value not in identifiers:
                    identifiers[value] = {"count": 0, "lines": set()}
                identifiers[value]["count"] += 1
                identifiers[value]["lines"].add(line)

            # ── Literal stats (broad type == LITERAL) ────────────────────
            if t_type == "LITERAL":
                if value not in literals:
                    literals[value] = {
                        "type":  category,   # specific: LITERAL_INTEGER etc.
                        "count": 0,
                        "lines": set()
                    }
                literals[value]["count"] += 1
                literals[value]["lines"].add(line)

        for t in summary:
            summary[t]["percentage"] = (
                summary[t]["count"] / total_tokens * 100 if total_tokens else 0
            )

        type_counts = {k: v["count"] for k, v in summary.items()}
        most  = max(type_counts.items(), key=lambda x: x[1]) if type_counts else ("None", 0)
        least = min(type_counts.items(), key=lambda x: x[1]) if type_counts else ("None", 0)
        total_lines = len(line_dist)
        avg = total_tokens / total_lines if total_lines else 0

        return {
            "summary":           summary,
            "line_distribution": line_dist,
            "identifiers":       identifiers,
            "literals":          literals,
            "overall": {
                "total_tokens":       total_tokens,
                "unique_token_types": len(summary),
                "lines_with_code":    total_lines,
                "most_frequent":      most,
                "least_frequent":     least,
                "avg_tokens_per_line": round(avg, 2)
            }
        }


def analyze_code(code):
    lexer   = Lexer()
    tokens  = lexer.tokenize(code)
    results = Analyzer(tokens).analyze()
    return {"tokens": tokens, **results}